from __future__ import annotations

import asyncio
import json
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .capture import list_speakers
from .config import AppConfig
from .recognizer import TranscriptionEngine
from .settings import public_settings, test_deepseek, update_from_web


class EventHub:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.queue: asyncio.Queue[dict] | None = None
        self.clients: set[WebSocket] = set()
        self._lock = threading.Lock()
        self._sequence = 0
        self.latest_status: dict | None = None
        self.latest_error: dict | None = None

    def bind(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue(maxsize=256)

    def publish(self, event: dict) -> None:
        with self._lock:
            self._sequence += 1
            payload = {
                **event,
                "seq": self._sequence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if event.get("type") == "status":
                self.latest_status = payload
            elif event.get("type") == "error":
                self.latest_error = payload
        if self.loop and self.queue:
            self.loop.call_soon_threadsafe(self._enqueue, payload)

    def _enqueue(self, payload: dict) -> None:
        assert self.queue is not None
        if self.queue.full():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        self.queue.put_nowait(payload)

    async def dispatch(self) -> None:
        assert self.queue is not None
        while True:
            payload = await self.queue.get()
            message = json.dumps(payload, ensure_ascii=False)
            dead: list[WebSocket] = []
            for client in tuple(self.clients):
                try:
                    await client.send_text(message)
                except Exception:
                    dead.append(client)
            for client in dead:
                self.clients.discard(client)


def create_app(config: AppConfig) -> FastAPI:
    config.validate()
    hub = EventHub()
    engine = TranscriptionEngine(config, hub.publish)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        hub.bind()
        dispatcher = asyncio.create_task(hub.dispatch())
        engine.start()
        try:
            yield
        finally:
            engine.stop()
            dispatcher.cancel()
            try:
                await dispatcher
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="WASAPI Paraformer WebSocket", version="0.1.0", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")

    def require_local(request: Request) -> None:
        host = request.client.host if request.client else ""
        if host not in {"127.0.0.1", "::1"}:
            raise HTTPException(status_code=403, detail="设置接口只允许本机访问")

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request) -> str:
        require_local(request)
        return (Path(__file__).parent / "web" / "settings.html").read_text(encoding="utf-8")

    @app.get("/api/settings")
    async def get_settings(request: Request) -> dict:
        require_local(request)
        return await asyncio.to_thread(public_settings)

    @app.post("/api/settings")
    async def put_settings(request: Request, payload: dict) -> dict:
        require_local(request)
        saved = await asyncio.to_thread(update_from_web, payload)
        return {"ok": True, "settings": saved, "apiKeySet": public_settings()["apiKeySet"]}

    @app.post("/api/settings/test-deepseek")
    async def test_deepseek_api(request: Request) -> dict:
        require_local(request)
        try:
            return await asyncio.to_thread(test_deepseek)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/health")
    async def health() -> dict:
        return {
            "ok": hub.latest_error is None,
            "status": hub.latest_status,
            "error": hub.latest_error,
            "clients": len(hub.clients),
        }

    @app.get("/devices")
    async def devices() -> dict:
        return {"speakers": list_speakers()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json(
            {"type": "hello", "protocol": 1, "pcm": {"sample_rate": 16000, "channels": 1}}
        )
        if hub.latest_status:
            await websocket.send_json(hub.latest_status)
        if hub.latest_error:
            await websocket.send_json(hub.latest_error)
        hub.clients.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            hub.clients.discard(websocket)

    return app
