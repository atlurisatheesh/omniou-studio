"""
utils/ws_manager.py — Production-grade WebSocket connection manager (Phase 12).

Features:
- Per-job connection registry
- Heartbeat ping/pong every 15s
- Redis pub/sub bridge for Celery workers
- Reconnect replay from Redis stream
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

import structlog
from fastapi import WebSocket, WebSocketDisconnect

log = structlog.get_logger(__name__)

STREAM_MAXLEN = 200
HEARTBEAT_SECS = 15
PING_TIMEOUT = 10


class ConnectionInfo:
    __slots__ = ("ws", "conn_id", "connected_at", "last_pong", "subscribed_job")

    def __init__(self, ws: WebSocket, job_id: str):
        self.ws = ws
        self.conn_id = str(uuid.uuid4())[:8]
        self.connected_at = time.time()
        self.last_pong = time.time()
        self.subscribed_job = job_id


class WebSocketManager:
    def __init__(self):
        self._connections: Dict[str, List[ConnectionInfo]] = defaultdict(list)
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._redis = None

    def start(self):
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def stop(self):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

    def _redis_client(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                from app.config import settings
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def connect(self, ws: WebSocket, job_id: str) -> ConnectionInfo:
        await ws.accept()
        info = ConnectionInfo(ws, job_id)
        self._connections[job_id].append(info)
        log.info("ws_connected", job_id=job_id, conn_id=info.conn_id)
        return info

    async def disconnect(self, info: ConnectionInfo):
        job_id = info.subscribed_job
        conns = self._connections.get(job_id, [])
        if info in conns:
            conns.remove(info)
        if not conns:
            self._connections.pop(job_id, None)

    async def send_to_job(self, job_id: str, event: dict):
        event.setdefault("ts", time.time())
        message = json.dumps(event)
        r = self._redis_client()
        if r:
            try:
                await r.publish(f"cloneai:ws:{job_id}", message)
                await r.xadd(f"cloneai:stream:{job_id}", {"data": message}, maxlen=STREAM_MAXLEN)
            except Exception as e:
                log.warning("redis_publish_failed", error=str(e))
        await self._broadcast_raw(job_id, message)

    async def _broadcast_raw(self, job_id: str, message: str):
        dead: List[ConnectionInfo] = []
        for info in list(self._connections.get(job_id, [])):
            try:
                await info.ws.send_text(message)
            except Exception:
                dead.append(info)
        for info in dead:
            await self.disconnect(info)

    async def replay_since(self, job_id: str, ws: WebSocket, last_event_id: str = "0"):
        r = self._redis_client()
        if not r:
            return
        try:
            entries = await r.xrange(f"cloneai:stream:{job_id}", min=last_event_id, count=100)
            for entry_id, fields in entries:
                if entry_id == last_event_id:
                    continue
                await ws.send_text(fields["data"])
        except Exception as e:
            log.warning("replay_failed", error=str(e))

    async def subscribe_redis(self, job_id: str):
        r = self._redis_client()
        if not r:
            return
        pubsub = r.pubsub()
        await pubsub.subscribe(f"cloneai:ws:{job_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._broadcast_raw(job_id, message["data"])
                    if not self._connections.get(job_id):
                        break
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(f"cloneai:ws:{job_id}")

    async def listen(self, ws: WebSocket, info: ConnectionInfo, since: str = "0"):
        job_id = info.subscribed_job
        if since != "0":
            await self.replay_since(job_id, ws, since)
        if len(self._connections.get(job_id, [])) == 1:
            asyncio.create_task(self.subscribe_redis(job_id))
        try:
            while True:
                try:
                    data = await asyncio.wait_for(ws.receive_text(), timeout=HEARTBEAT_SECS + 5)
                    msg = json.loads(data) if data else {}
                    if msg.get("type") == "pong":
                        info.last_pong = time.time()
                except asyncio.TimeoutError:
                    pass
        except WebSocketDisconnect:
            pass
        finally:
            await self.disconnect(info)

    async def _heartbeat_loop(self):
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_SECS)
                now = time.time()
                for job_id, conns in list(self._connections.items()):
                    dead: List[ConnectionInfo] = []
                    for info in conns:
                        if now - info.last_pong > HEARTBEAT_SECS + PING_TIMEOUT:
                            dead.append(info)
                            continue
                        try:
                            await info.ws.send_text(json.dumps({"type": "ping", "ts": now}))
                        except Exception:
                            dead.append(info)
                    for info in dead:
                        await self.disconnect(info)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning("heartbeat_error", error=str(e))


# Singleton
ws_manager = WebSocketManager()
