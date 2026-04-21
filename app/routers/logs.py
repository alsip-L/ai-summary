# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.log import get_ws_handler, get_logger, LOGGER_NAME, WebSocketLogHandler

router = APIRouter(tags=["logs"])

PING_INTERVAL = 15
REPLAY_BATCH_SIZE = 100  # 回放时每批发送的记录数
POLL_INTERVAL = 0.1  # 实时推送轮询间隔（秒）


@router.get(
    "/api/logs/status",
    summary="获取日志状态",
    description="返回日志处理器的状态信息，包含日志级别、处理器列表和缓冲区大小。",
    responses={200: {"description": "日志状态信息"}},
)
def logs_status():
    logger = logging.getLogger(LOGGER_NAME)
    handler = get_ws_handler()
    return {
        "logger_level": logging.getLevelName(logger.level),
        "handlers": [h.__class__.__name__ for h in logger.handlers],
        "ws_handler_found": handler is not None,
        "ws_handler_class": handler.__class__.__name__ if handler else None,
        "buffer_size": handler.buffer_size if handler else -1,
        "current_seq": handler.current_seq if handler else -1,
    }


@router.post(
    "/api/logs/clear",
    summary="清除日志缓冲",
    description="清除 WebSocket 日志处理器的缓冲区，释放内存。",
    responses={200: {"description": "清除成功"}},
)
def clear_logs():
    handler = get_ws_handler()
    if handler is None:
        return {"success": False, "error": "日志处理器未找到"}
    handler.clear_buffer()
    return {"success": True}


@router.websocket("/api/logs/ws")
async def logs_ws(ws: WebSocket):
    await ws.accept()
    handler = get_ws_handler()
    if handler is None:
        logger = logging.getLogger(LOGGER_NAME)
        logger.warning("WebSocket 连接请求日志，但 WebSocketLogHandler 未找到")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": "No log handler found"}))
        except Exception:
            pass
        await ws.close()
        return

    try:
        # 1. 回放缓冲区中的历史记录（分批发送，避免阻塞事件循环）
        buffered = handler.get_buffer_since(0)
        if buffered:
            replay_msg = json.dumps({
                "type": "replay",
                "count": len(buffered),
            }, ensure_ascii=False)
            try:
                await ws.send_text(replay_msg)
            except Exception:
                return
            for i in range(0, len(buffered), REPLAY_BATCH_SIZE):
                batch = buffered[i:i + REPLAY_BATCH_SIZE]
                for seq, msg in batch:
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        return
                # 每批发送后让出控制权，避免阻塞事件循环
                if i + REPLAY_BATCH_SIZE < len(buffered):
                    await asyncio.sleep(0)

        # 2. 发送回放结束标记，通知客户端历史日志回放完毕
        try:
            await ws.send_text(json.dumps({"type": "replay_end"}))
        except Exception:
            return

        # 3. 记住回放中最后一条记录的 seq，之后只推送新记录
        #    使用回放数据中的seq而非current_seq，避免回放期间新日志被跳过
        last_seq = buffered[-1][0] if buffered else 0

        # 4. 实时推送循环（统一从缓冲区增量读取）
        last_ping_time = asyncio.get_event_loop().time()
        while True:
            # 接收并丢弃客户端消息（保持连接健康，避免缓冲区堆积）
            # 使用 asyncio.wait 竞争替代 timeout=0，避免高频 TimeoutError 异常
            receive_task = asyncio.create_task(ws.receive_text())
            sleep_task = asyncio.create_task(asyncio.sleep(POLL_INTERVAL))
            done, pending = await asyncio.wait(
                {receive_task, sleep_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            # 取消未完成的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            # 检查 receive_task 是否因断连而完成
            if receive_task in done:
                try:
                    receive_task.result()
                except WebSocketDisconnect:
                    return
                except Exception:
                    pass

            new_entries = handler.get_buffer_since(last_seq)
            if new_entries:
                last_ping_time = asyncio.get_event_loop().time()
                for seq, msg in new_entries:
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        return
                last_seq = new_entries[-1][0]

            # 基于时间戳判断是否需要发送心跳，避免浮点除法精度问题
            now = asyncio.get_event_loop().time()
            if now - last_ping_time >= PING_INTERVAL:
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    return
                last_ping_time = now
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # 记录非预期异常，便于排查
        logger = logging.getLogger(LOGGER_NAME)
        logger.error(f"WebSocket 日志推送异常: {e}")
