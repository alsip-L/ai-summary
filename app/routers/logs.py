# -*- coding: utf-8 -*-
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.log import get_ws_handler, LOGGER_NAME

router = APIRouter(tags=["logs"])

PING_INTERVAL = 15


@router.get("/api/logs/status")
def logs_status():
    logger = logging.getLogger(LOGGER_NAME)
    handler = get_ws_handler()
    return {
        "logger_level": logging.getLevelName(logger.level),
        "handlers": [h.__class__.__name__ for h in logger.handlers],
        "ws_handler_found": handler is not None,
        "ws_handler_class": handler.__class__.__name__ if handler else None,
        "queue_size": handler._queue.qsize() if handler else -1,
    }


@router.websocket("/api/logs/ws")
async def logs_ws(ws: WebSocket):
    await ws.accept()
    handler = get_ws_handler()
    if handler is None:
        for h in logging.getLogger(LOGGER_NAME).handlers:
            if h.__class__.__name__ == 'WebSocketLogHandler':
                handler = h
                break
    if handler is None:
        try:
            await ws.send_text("[system] No log handler found")
        except Exception:
            pass
        await ws.close()
        return
    try:
        idle_count = 0
        while True:
            try:
                messages = handler.get_pending()
            except Exception as e:
                # get_pending 异常不应发生，但以防万一
                await asyncio.sleep(0.1)
                continue
            if messages:
                idle_count = 0
                sent_count = 0
                for msg in messages:
                    try:
                        await ws.send_text(msg)
                        sent_count += 1
                    except Exception:
                        # 发送失败，将未发送的消息放回队列并退出
                        unsent = messages[sent_count:]
                        for m in reversed(unsent):
                            try:
                                handler._queue.put_nowait(m)
                            except Exception:
                                pass
                        return
            else:
                idle_count += 1

            # 每 15 秒无日志时发送心跳，保持连接活跃
            if idle_count >= int(PING_INTERVAL / 0.1):
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    return
                idle_count = 0

            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
