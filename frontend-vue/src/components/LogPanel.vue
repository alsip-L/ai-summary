<template>
  <div class="log-panel" :class="{ 'log-panel-expanded': expanded }">
    <div class="log-panel-header" @click="expanded = !expanded">
      <span class="log-panel-title">
        <span class="log-panel-icon">&#9654;</span>
        日志
      </span>
      <div class="log-panel-actions">
        <span v-if="!connected" class="log-status log-status-disconnected">未连接</span>
        <span v-else class="log-status log-status-connected">已连接</span>
        <button v-if="expanded" type="button" class="btn btn-sm btn-secondary log-btn" @click.stop="clearLogs">清空</button>
        <span class="log-panel-arrow">{{ expanded ? '&#9650;' : '&#9650;' }}</span>
      </div>
    </div>
    <div v-if="expanded" class="log-panel-body">
      <div class="log-list" ref="logList">
        <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
        <template v-for="(log, i) in logs" :key="i">
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
import { ref, onMounted, onUnmounted, nextTick, watch, triggerRef } from 'vue'
import { useTaskStore } from '../stores/task'

const taskStore = useTaskStore()
const expanded = ref(false)
const logs = ref([])
const connected = ref(false)
const logList = ref(null)
const MAX_LOGS = 500

let ws = null
let reconnectTimer = null
let shouldConnect = false

function logLevelClass(text) {
  if (text.includes('ERROR') || text.includes('CRITICAL')) return 'log-error'
  if (text.includes('WARNING')) return 'log-warning'
  if (text.includes('INFO')) return 'log-info'
  if (text.includes('DEBUG')) return 'log-debug'
  return ''
}

function logTime(text) {
  const m = text.match(/\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]/)
  return m ? m[1] : ''
}

function logLevel(text) {
  const m = text.match(/\]\s*(INFO|ERROR|WARNING|DEBUG|CRITICAL):/)
  return m ? m[1] : ''
}

function logMsg(text) {
  const m = text.match(/\]\s*(?:INFO|ERROR|WARNING|DEBUG|CRITICAL):\s*(.*)/)
  return m ? m[1] : text
}

function clearLogs() {
  logs.value = []
}

function addLogEntry(entry) {
  if (logs.value.length >= MAX_LOGS) {
    logs.value.splice(0, logs.value.length - MAX_LOGS + 1)
  }
  logs.value.push(entry)
}

function handleMessage(raw) {
  if (raw.startsWith('{')) {
    try {
      const msg = JSON.parse(raw)
      if (msg.type === 'stream') {
        const last = logs.value[logs.value.length - 1]
        if (last && last.stream && last.streaming) {
          last.text += msg.data
          triggerRef(logs)
        } else {
          addLogEntry({ stream: true, streaming: true, text: msg.data })
        }
        nextTick(scrollToBottom)
        return
      }
      if (msg.type === 'stream_end') {
        const last = logs.value[logs.value.length - 1]
        if (last && last.stream) {
          last.streaming = false
          triggerRef(logs)
        }
        return
      }
      if (msg.type === 'ping') {
        return
      }
    } catch (e) {
      // 不是有效 JSON，当作普通日志处理
    }
  }

  addLogEntry({ stream: false, text: raw })
  nextTick(scrollToBottom)
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${location.host}/api/logs/ws`
  ws = new WebSocket(url)

  ws.onopen = () => {
    connected.value = true
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
    connected.value = false
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    if (shouldConnect) {
      connect()
    }
  }, 3000)
}

function scrollToBottom() {
  if (logList.value) {
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

watch(() => taskStore.isProcessing, (val) => {
  if (val) {
    expanded.value = true
  }
})

onMounted(() => {
  shouldConnect = true
  connect()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  disconnect()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>
