<template>
  <div class="log-panel">
    <div class="log-panel-header">
      <span class="log-panel-title">
        <span class="log-panel-icon">&#9654;</span>
        日志
      </span>
      <div class="log-panel-actions">
        <span v-if="!connected" class="log-status log-status-disconnected">未连接</span>
        <span v-else class="log-status log-status-connected">已连接</span>
        <button type="button" class="btn btn-sm btn-secondary log-btn" @click="clearLogs">清空</button>
      </div>
    </div>
    <div class="log-panel-body">
      <div class="log-list" ref="logList" @scroll="onLogListScroll">
        <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
        <template v-for="log in logs" :key="log.id">
          <div v-if="log.stream" class="log-stream" :class="{ 'log-stream-ended': !log.streaming }">
            <span class="log-stream-label">AI</span>
            <span class="log-stream-content">{{ log.text }}</span>
            <span v-if="log.streaming" class="log-stream-cursor"></span>
          </div>
          <div v-else class="log-entry" :class="logLevelClass(log.text)">
            <span class="log-time">{{ logTime(log.text) }}</span>
            <span class="log-level">{{ logLevel(log.text) }}</span>
            <span class="log-msg">{{ logMsg(log.text) }}</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, triggerRef } from 'vue'
import { api, getStoredApiToken } from '../composables/useApi'
const logs = ref([])
const connected = ref(false)
const logList = ref(null)
const MAX_LOGS = 500

let ws = null
let reconnectTimer = null
let shouldConnect = false
let reconnectDelay = 1000  // 初始重连延迟1秒
const MAX_RECONNECT_DELAY = 10000  // 最大延迟10秒
let logIdCounter = 0  // 唯一日志 ID 计数器
let isReplaying = false  // 是否正在回放历史日志
let userScrolledUp = false  // 用户是否正在向上查看历史日志
// 页面刷新后不恢复清空标记，允许回放历史日志
let logsCleared = false

// 预编译日志级别正则，避免重复创建
const LOG_LEVEL_REGEX = /\]\s*(INFO|ERROR|WARNING|DEBUG|CRITICAL):/
const LOG_TIME_REGEX = /\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]/
const LOG_MSG_REGEX = /\]\s*(?:INFO|ERROR|WARNING|DEBUG|CRITICAL):\s*(.*)/

function logLevelClass(text) {
  // 仅从日志格式化部分提取级别，避免消息内容中的误匹配
  const m = text.match(LOG_LEVEL_REGEX)
  if (!m) return ''
  const level = m[1]
  if (level === 'ERROR' || level === 'CRITICAL') return 'log-error'
  if (level === 'WARNING') return 'log-warning'
  if (level === 'INFO') return 'log-info'
  if (level === 'DEBUG') return 'log-debug'
  return ''
}

function logTime(text) {
  const m = text.match(LOG_TIME_REGEX)
  return m ? m[1] : ''
}

function logLevel(text) {
  const m = text.match(LOG_LEVEL_REGEX)
  return m ? m[1] : ''
}

function logMsg(text) {
  const m = text.match(LOG_MSG_REGEX)
  return m ? m[1] : text
}

async function clearLogs() {
  logs.value = []
  isReplaying = false
  userScrolledUp = false
  logsCleared = true
  sessionStorage.setItem('logsCleared', '1')
  try {
    await api.clearLogs()
  } catch (e) {
    // 后端清空失败不影响前端清空，logsCleared 标记会阻止回放旧日志
    console.error('清空后端日志缓冲区失败:', e)
  }
}

// 重置清空标记（供父组件在用户启动新任务时调用）
function resetLogsCleared() {
  logsCleared = false
  sessionStorage.removeItem('logsCleared')
}

function trimLogs() {
  // 裁剪超出上限的日志（包括流式消息）
  if (logs.value.length > MAX_LOGS) {
    logs.value.splice(0, logs.value.length - MAX_LOGS)
  }
}

function addLogEntry(entry) {
  entry.id = ++logIdCounter
  logs.value.push(entry)
  trimLogs()
}

function handleMessage(raw) {
  if (raw.startsWith('{')) {
    try {
      const msg = JSON.parse(raw)
      if (msg.type === 'replay') {
        // 回放开始标记
        if (logsCleared) {
          // 用户已清空日志，跳过回放旧内容（logsCleared将持续有效直到用户主动操作）
          isReplaying = true
          return
        }
        logs.value = []
        isReplaying = true
        return
      }
      if (msg.type === 'stream') {
        if (logsCleared) return  // 用户已清空日志，跳过流式消息
        const last = logs.value[logs.value.length - 1]
        if (last && last.stream && last.streaming) {
          last.text += msg.data
          triggerRef(logs)
          trimLogs()
        } else {
          addLogEntry({ stream: true, streaming: true, text: msg.data })
        }
        nextTick(autoScrollToBottom)
        return
      }
      if (msg.type === 'stream_end') {
        if (logsCleared) return  // 用户已清空日志，跳过流式结束消息
        const last = logs.value[logs.value.length - 1]
        if (last && last.stream) {
          last.streaming = false
          triggerRef(logs)
        }
        return
      }
      if (msg.type === 'replay_end') {
        // 回放结束标记：仅重置回放状态
        // 如果用户已清空日志(logsCleared=true)，不重置该标记，让其在会话期间持续有效
        isReplaying = false
        return
      }
      if (msg.type === 'ping') {
        return
      }
    } catch (e) {
      // 不是有效 JSON，当作普通日志处理
    }
  }

  // 用户已清空日志，跳过所有旧日志（回放期间和回放结束后均过滤）
  if (logsCleared) {
    return
  }

  addLogEntry({ stream: false, text: raw })
  nextTick(autoScrollToBottom)
}

function connect() {
  // 清理处于 CONNECTING 状态的旧连接，避免 onclose 触发多余重连
  if (ws && ws.readyState === WebSocket.CONNECTING) {
    ws.onclose = null
    ws.close()
    ws = null
  }
  if (ws && ws.readyState === WebSocket.OPEN) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const basePath = location.pathname.replace(/\/[^/]*$/, '')
  const token = getStoredApiToken()
  const url = `${protocol}//${location.host}${basePath}/api/logs/ws`
  // 通过 WebSocket 子协议传递 token，避免 token 出现在 URL 中被日志记录
  const protocols = token ? [`x-api-token.${token}`] : undefined
  ws = new WebSocket(url, protocols)

  ws.onopen = () => {
    connected.value = true
    reconnectDelay = 1000  // 连接成功，重置重连延迟
  }

  ws.onmessage = (event) => {
    handleMessage(event.data)
  }

  ws.onclose = () => {
    connected.value = false
    ws = null
    if (shouldConnect) {
      scheduleReconnect()
    }
  }

  ws.onerror = () => {
    // onerror 后通常会紧跟 onclose，此处仅更新状态
    // 但某些情况下 onclose 可能不触发，所以也主动触发重连
    connected.value = false
    ws = null
    if (shouldConnect) {
      scheduleReconnect()
    }
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    if (shouldConnect) {
      connect()
    }
  }, reconnectDelay)
  // 指数退避：1s, 2s, 4s, 8s, 10s, 10s...
  reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY)
}

function onLogListScroll() {
  // 判断用户是否正在向上查看历史日志（距底部超过 30px 视为向上滚动）
  if (logList.value) {
    const { scrollTop, scrollHeight, clientHeight } = logList.value
    userScrolledUp = scrollHeight - scrollTop - clientHeight > 30
  }
}

function autoScrollToBottom() {
  // 仅当用户未向上查看时自动滚动到底部
  if (!userScrolledUp && logList.value) {
    logList.value.scrollTop = logList.value.scrollHeight
  }
}

function disconnect() {
  shouldConnect = false
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
  connected.value = false
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible' && shouldConnect) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      if (ws) {
        ws.onclose = null
        ws.close()
        ws = null
      }
      connect()
    }
  }
}

onMounted(() => {
  shouldConnect = true
  connect()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  disconnect()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

defineExpose({ resetLogsCleared })
</script>
