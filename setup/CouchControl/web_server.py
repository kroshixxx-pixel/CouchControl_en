import hashlib
import hmac
import json
import logging
import os
import time
from urllib.parse import parse_qsl

from aiohttp import web
import pyautogui

log = logging.getLogger("couchcontrol.web")
PORT = int(os.getenv("WEB_SERVER_PORT", "8765"))
ALLOWED_ORIGIN = "https://kroshixxx-pixel.github.io"


def verify_init_data(raw: str) -> bool:
    token = os.getenv("BOT_TOKEN", "").strip()
    try:
        allowed_user_id = int(os.getenv("ALLOWED_USER_ID", "0") or "0")
    except ValueError:
        return False
    if not token or not allowed_user_id or not raw:
        return False
    try:
        pairs = dict(parse_qsl(raw, keep_blank_values=True, strict_parsing=True))
        received_hash = pairs.pop("hash", "")
        auth_date = int(pairs.get("auth_date", "0"))
        if not received_hash or time.time() - auth_date > 86400 or auth_date > time.time() + 60:
            return False
        check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return False
        user = json.loads(pairs.get("user", "{}"))
        return int(user.get("id", 0)) == allowed_user_id
    except (ValueError, TypeError, json.JSONDecodeError):
        return False


@web.middleware
async def security_headers(request, handler):
    origin = request.headers.get("Origin", "")
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)
    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Telegram-Init-Data"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Cache-Control"] = "no-store"
    return response


@web.middleware
async def require_telegram_user(request, handler):
    if request.path == "/api/health":
        return await handler(request)
    if request.method == "OPTIONS":
        return web.Response(status=204)
    origin = request.headers.get("Origin", "")
    if origin != ALLOWED_ORIGIN or not verify_init_data(request.headers.get("X-Telegram-Init-Data", "")):
        raise web.HTTPUnauthorized(text="Telegram authorization failed")
    return await handler(request)


async def health(_request):
    return web.json_response({"ok": True, "service": "CouchControl"})


async def mouse_move(request):
    try:
        data = await request.json()
        dx = max(-500, min(500, float(data.get("dx", 0))))
        dy = max(-500, min(500, float(data.get("dy", 0))))
        pyautogui.moveRel(dx, dy, duration=0)
        return web.json_response({"ok": True})
    except (ValueError, TypeError):
        raise web.HTTPBadRequest(text="Invalid movement")


async def mouse_click(request):
    try:
        data = await request.json()
        button = data.get("button")
        if button not in ("left", "right"):
            raise web.HTTPBadRequest(text="Invalid button")
        pyautogui.click(button=button)
        return web.json_response({"ok": True})
    except (ValueError, TypeError):
        raise web.HTTPBadRequest(text="Invalid request")


async def start_web_server(application):
    app = web.Application(middlewares=[security_headers, require_telegram_user], client_max_size=2048)
    app.router.add_get("/api/health", health)
    app.router.add_post("/api/mouse/move", mouse_move)
    app.router.add_post("/api/mouse/click", mouse_click)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", PORT)
    await site.start()
    application.bot_data["web_runner"] = runner
    log.info("CouchControl local control API listening on 127.0.0.1:%s", PORT)


async def stop_web_server(application):
    runner = application.bot_data.get("web_runner")
    if runner:
        await runner.cleanup()
        log.info("CouchControl local control API stopped")
