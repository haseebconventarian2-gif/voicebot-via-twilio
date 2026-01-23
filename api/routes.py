import asyncio
import json
import os

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from .azure import (
  audio_content_type,
  generate_text,
  synthesize_speech,
  transcribe_audio,
)
from rag_pipeline import build_rag_context, build_vectorstore_from_path, format_response
from .whatsapp import (
  debug_access_token,
  download_media,
  download_twilio_media,
  get_audio,
  parse_message,
  parse_twilio_message,
  push_text,
  reply_audio,
  reply_audio_twilio,
  reply_text,
  reply_text_twilio,
)
from .ui import UI_HTML


_STT_FIXES = {
  "a count": "account",
  "a/c": "account",
  "a san": "asaan",
}


def _load_json(path: str) -> dict:
  with open(path, "r", encoding="utf-8") as f:
    return json.load(f)


def _load_voice_config() -> dict:
  path = os.getenv("VOICE_CONFIG_PATH", "bankislami_voice_config.json")
  data = _load_json(path)
  system_prompt = data.get("system_prompt", {}).get("content")
  if not system_prompt:
    raise RuntimeError("Missing system_prompt.content in voice config.")
  return data


def _load_product_map(rag_path: str) -> dict:
  if not rag_path.lower().endswith(".json") or not os.path.exists(rag_path):
    return {}
  data = _load_json(rag_path)
  accounts = data.get("accounts", [])
  product_map = {}
  for item in accounts:
    pid = item.get("id")
    name = item.get("name")
    if pid and name:
      product_map[pid] = name
  return product_map


def _apply_stt_fixes(text: str) -> str:
  normalized = text
  for src, target in _STT_FIXES.items():
    normalized = normalized.replace(src, target)
  return normalized


def _normalize_transcript(text: str, product_normalization: dict, product_map: dict) -> tuple[str, str | None]:
  cleaned = " ".join(text.strip().split())
  lowered = cleaned.lower()
  lowered = _apply_stt_fixes(lowered)
  product_name = None
  for canonical, variants in product_normalization.items():
    for variant in variants:
      needle = variant.lower()
      if needle in lowered:
        product_name = product_map.get(canonical) or canonical.replace("_", " ").title()
        for v in variants:
          lowered = lowered.replace(v.lower(), product_name.lower())
        return lowered, product_name
  return lowered, None


def _detect_intent(normalized_text: str, intent_keywords: dict) -> str | None:
  for intent, keywords in intent_keywords.items():
    for keyword in keywords:
      if keyword.lower() in normalized_text:
        return intent
  return None


def _build_retrieval_query(
  normalized_text: str,
  product_name: str | None,
  intent: str | None,
  intent_keywords: dict,
) -> str:
  parts = [normalized_text] if normalized_text else []
  if product_name and product_name.lower() not in normalized_text:
    parts.append(product_name)
  if intent:
    parts.append(intent.replace("_", " "))
  expansion = ["features", "eligibility", "documents", "process"]
  if intent and intent in intent_keywords:
    expansion.extend(intent_keywords[intent])
  seen = set()
  ordered = []
  for item in parts + expansion:
    token = item.strip()
    key = token.lower()
    if token and key not in seen:
      seen.add(key)
      ordered.append(token)
  return " ".join(ordered)


def _fallback_response(
  normalized_text: str,
  product_name: str | None,
  intent: str | None,
  fallbacks: dict,
) -> str:
  is_account = "account" in normalized_text or (intent in {"account_benefits", "account_opening"})
  if is_account and not product_name:
    return fallbacks.get("clarify_account") or fallbacks.get("handoff") or "Mazrat, main samajh nahi saka."
  if intent == "account_opening":
    return fallbacks.get("general_opening") or fallbacks.get("handoff") or "Mazrat, main samajh nahi saka."
  return fallbacks.get("handoff") or "Mazrat, main samajh nahi saka."


def create_app() -> FastAPI:
  app = FastAPI(title="Azure AI Bot")
  rag_store = None
  rag_path = os.getenv("RAG_DATA_PATH", "bank.json")
  voice_config = _load_voice_config()
  system_prompt = voice_config["system_prompt"]["content"]
  intent_keywords = voice_config.get("intent_keywords", {})
  product_normalization = voice_config.get("product_normalization", {}).get("accounts", {})
  fallback_responses = voice_config.get("fallback_responses", {})
  product_map = _load_product_map(rag_path)
  if os.path.exists(rag_path):
    try:
      rag_store = build_vectorstore_from_path(rag_path)
      print(f"RAG loaded from {rag_path}")
    except Exception as exc:
      print(f"RAG load failed for {rag_path}: {exc}")

  async def get_answer(user_text: str) -> str:
    normalized = user_text.strip().lower()
    if normalized in {"hi", "hello", "hey", "salam", "assalamualaikum", "asalamualaikum"}:
      return "Assalam-o-Alaikum. Welcome to Bank Islami. Mai aap ki madad ke liye hoon."
    normalized_text, product_name = _normalize_transcript(user_text, product_normalization, product_map)
    intent = _detect_intent(normalized_text, intent_keywords)
    query = _build_retrieval_query(normalized_text, product_name, intent, intent_keywords)
    rag_context = build_rag_context(query, rag_store) if rag_store else ""
    if not rag_context:
      return _fallback_response(normalized_text, product_name, intent, fallback_responses)
    return format_response(await generate_text(user_text, system_prompt, rag_context))

  @app.get("/")
  def ui() -> Response:
    return Response(content=UI_HTML, media_type="text/html")

  @app.get("/health")
  def health() -> JSONResponse:
    return JSONResponse({"ok": True})

  @app.post("/text")
  async def text_reply(payload: dict) -> JSONResponse:
    user_text = str(payload.get("text") or "").strip()
    if not user_text:
      raise HTTPException(status_code=400, detail="Missing text")
    answer = await get_answer(user_text)
    return JSONResponse({"text": answer})

  @app.get("/whatsapp/diagnose")
  async def whatsapp_diagnose(check_token: bool = False) -> JSONResponse:
    report = {
      "has_access_token": bool(os.getenv("ACCESS_TOKEN")),
      "has_phone_number_id": bool(os.getenv("PHONE_NUMBER_ID")),
      "has_verify_token": bool(os.getenv("VERIFY_TOKEN")),
      "has_public_base_url": bool(os.getenv("PUBLIC_BASE_URL")),
      "has_app_id": bool(os.getenv("APP_ID")),
      "has_app_secret": bool(os.getenv("APP_SECRET")),
      "has_recipient_waid": bool(os.getenv("RECIPIENT_WAID")),
      "version": os.getenv("VERSION") or os.getenv("META_API_VERSION") or "v20.0",
    }
    if check_token:
      try:
        report["token_debug"] = await debug_access_token()
      except Exception as exc:
        report["token_debug_error"] = str(exc)
    return JSONResponse(report)

  @app.post("/whatsapp/push")
  async def whatsapp_push(payload: dict) -> JSONResponse:
    text = str(payload.get("text") or "").strip()
    to_number = str(payload.get("to") or "").strip() or None
    if not text:
      raise HTTPException(status_code=400, detail="Missing text")
    await push_text(text, to_number)
    return JSONResponse({"ok": True})

  @app.post("/audio")
  async def audio_reply(file: UploadFile = File(...)) -> Response:
    audio_bytes = await file.read()
    if not audio_bytes:
      raise HTTPException(status_code=400, detail="Missing audio file")

    transcript = await transcribe_audio(audio_bytes, file.filename or "", file.content_type)
    answer = await get_answer(transcript)
    audio_out = await synthesize_speech(answer)
    return Response(content=audio_out, media_type=audio_content_type())

  @app.get("/tts")
  async def tts(text: str = Query(min_length=1)) -> Response:
    audio_out = await synthesize_speech(text)
    return Response(content=audio_out, media_type=audio_content_type())

  @app.get("/media/{media_id}")
  def media(media_id: str) -> Response:
    item = get_audio(media_id)
    if not item:
      raise HTTPException(status_code=404, detail="Not found")
    return Response(content=item["buffer"], media_type=item["content_type"])

  @app.get("/webhook")
  def webhook_verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
  ) -> Response:
    verify_token = os.getenv("VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_verify_token == verify_token and hub_challenge:
      return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403, content="Forbidden", media_type="text/plain")

  @app.post("/webhook")
  async def webhook_events(request: Request) -> JSONResponse:
    is_twilio = False
    payload = {}
    content_type = request.headers.get("content-type", "").lower()
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
      form = await request.form()
      payload = dict(form)
      is_twilio = "AccountSid" in payload or "SmsSid" in payload
    else:
      try:
        payload = await request.json()
      except Exception:
        return JSONResponse({"ok": True})

    try:
      print("Webhook payload:", payload)
    except Exception:
      print("Webhook payload: <unavailable>")

    msg = parse_twilio_message(payload) if is_twilio else parse_message(payload)
    if not msg:
      return JSONResponse({"ok": True})

    try:
      meta = (
        payload.get("entry", [])[0]
        .get("changes", [])[0]
        .get("value", {})
        .get("metadata", {})
      )
      print(
        "Webhook meta:",
        {"from": msg.get("from"), "phone_number_id": meta.get("phone_number_id")},
      )
    except Exception:
      print("Webhook meta: <unavailable>")

    async def handle_message() -> None:
      try:
        if msg["type"] == "text":
          answer = await get_answer(msg["text"])
          recipient = os.getenv("RECIPIENT_WAID") or msg["from"]
          if is_twilio:
            await reply_text_twilio(recipient, answer)
          else:
            await reply_text(recipient, answer)
          audio_out = await synthesize_speech(answer)
          if is_twilio:
            await reply_audio_twilio(recipient, audio_out, audio_content_type())
          else:
            await reply_audio(recipient, audio_out, audio_content_type())
          return

        if msg["type"] == "audio":
          if is_twilio:
            audio_bytes = await download_twilio_media(msg["media_url"])
          else:
            audio_bytes = await download_media(msg["media_id"])
          transcript = await transcribe_audio(audio_bytes, "audio", msg.get("media_type") or None)
          answer = await get_answer(transcript)
          recipient = os.getenv("RECIPIENT_WAID") or msg["from"]
          if is_twilio:
            await reply_text_twilio(recipient, answer)
          else:
            await reply_text(recipient, answer)
          audio_out = await synthesize_speech(answer)
          if is_twilio:
            await reply_audio_twilio(recipient, audio_out, audio_content_type())
          else:
            await reply_audio(recipient, audio_out, audio_content_type())
          return
      except Exception as exc:
        print("Webhook handler error:", exc)

    asyncio.create_task(handle_message())
    return JSONResponse({"ok": True})

  return app
