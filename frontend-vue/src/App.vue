<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-title">
        <span class="icon">A</span>
        AI Summary
        <button type="button" class="btn-rebuild" :disabled="rebuilding" :title="rebuilding ? '正在重启...' : '重启服务（重新构建前端 + 重启后端）'" @click="handleRebuild">
          <span class="btn-rebuild-icon" :class="{ spinning: rebuilding }">&#8635;</span>
        </button>
      </div>
      <div v-if="!taskStore.isProcessing" class="sidebar-start">
        <button type="button" class="btn btn-start-process" @click="handleStart">开始处理</button>
      </div>
      <div class="sidebar-scroll">
        <div id="message" :class="['alert', message.type ? `alert-${message.type === 'error' ? 'danger' : message.type}` : '', { hidden: !message.show }, { 'alert-fading': message.fading }]">
          {{ message.text }}
        </div>
        <ProviderPanel />
        <div class="sidebar-divider"></div>
        <PromptPanel />
        <div class="sidebar-divider"></div>
        <TrashPanel />
      </div>
      <div class="sidebar-footer">
        <a class="btn btn-secondary btn-admin" href="/admin/" target="_blank" rel="noopener" @click.prevent="openAdmin">
          <span class="btn-admin-icon">&#9881;</span>
          数据库管理
        </a>
      </div>
    </aside>
    <main class="main-content">
      <div class="main-content-upper">
        <div v-if="!taskStore.isProcessing && taskStore.status !== 'error' && taskStore.results.length === 0 && taskStore.failedCount === 0" class="main-content-empty">
          <span class="empty-hint">配置左侧参数后，点击「开始处理」</span>
        </div>
        <TaskProgress v-if="taskStore.isProcessing || taskStore.status === 'error'" />
        <ResultTable v-if="taskStore.results.length > 0 || taskStore.failedCount > 0" />
      </div>
      <div class="main-content-lower">
        <LogPanel ref="logPanel" />
      </div>
    </main>
  </div>
  <DirectoryBrowser ref="directoryBrowser" />
</template>

<script setup>
import { reactive, provide, onMounted, ref } from 'vue'
import { useProviderStore } from './stores/provider'
import { usePromptStore } from './stores/prompt'
import { useTaskStore } from './stores/task'
import { useTrashStore } from './stores/trash'
import { api, setApiToken } from './composables/useApi'
import ProviderPanel from './components/ProviderPanel.vue'
import PromptPanel from './components/PromptPanel.vue'
import TrashPanel from './components/TrashPanel.vue'
import TaskProgress from './components/TaskProgress.vue'
import ResultTable from './components/ResultTable.vue'
import DirectoryBrowser from './components/DirectoryBrowser.vue'
import LogPanel from './components/LogPanel.vue'

const providerStore = useProviderStore()
const promptStore = usePromptStore()
const taskStore = useTaskStore()
const trashStore = useTrashStore()

const directoryBrowser = ref(null)
const logPanel = ref(null)

const message = reactive({ show: false, text: '', type: 'info', fading: false })
const rebuilding = ref(false)

function showMessage(text, type = 'info') {
  message.show = true
  message.text = text
  message.type = type
  message.fading = false
  // rebuilding 期间不自动隐藏消息
  if (rebuilding.value) return
  setTimeout(() => {
    message.fading = true
    setTimeout(() => { message.show = false; message.fading = false }, 200)
  }, 1800)
}

provide('showMessage', showMessage)
provide('openDirectoryBrowser', () => directoryBrowser.value?.open())

// 重置日志清空标记（供子组件在重试任务时调用）
function resetLogsClearedForChildren() {
  logPanel.value?.resetLogsCleared()
}
provide('resetLogsCleared', resetLogsClearedForChildren)

function openAdmin() {
  window.open('/admin/', '_blank', 'noopener')
}

async function handleRebuild() {
  if (rebuilding.value) return
  rebuilding.value = true
  // 记录当前后端的启动时间，用于确认重启后是新进程
  let oldStartedAt = null
  try {
    const info = await fetch('/api/system/info', { cache: 'no-store' }).then(r => r.json())
    oldStartedAt = info.started_at
  } catch { /* 忽略 */ }

  showMessage('正在重新构建前端...', 'info')
  try {
    const res = await api.rebuild()
    if (res.success) {
      showMessage('前端构建完成，后端重启中...', 'info')
      _waitForBackendAndReload(oldStartedAt)
    } else {
      showMessage('重启失败: ' + (res.detail?.frontend || '未知错误'), 'error')
      rebuilding.value = false
    }
  } catch (e) {
    // 后端重启过程中连接断开是正常的，也视为成功
    showMessage('后端重启中，等待恢复...', 'info')
    _waitForBackendAndReload(oldStartedAt)
  }
}

function _waitForBackendAndReload(oldStartedAt) {
  // 轮询后端是否恢复，确认是新进程，最多等 60 秒
  let attempts = 0
  const maxAttempts = 60
  const interval = 1000

  function check() {
    attempts++
    if (attempts > maxAttempts) {
      rebuilding.value = false
      showMessage('重启超时，请手动刷新页面', 'error')
      return
    }
    fetch('/api/system/info?_t=' + Date.now(), { cache: 'no-store' })
      .then(res => {
        if (!res.ok) {
          setTimeout(check, interval)
          return
        }
        return res.json().then(data => {
          // 确认是新进程：started_at 比旧的大，或者 PID 不同
          if (oldStartedAt && data.started_at && data.started_at <= oldStartedAt) {
            // 还是旧进程，继续等
            setTimeout(check, interval)
            return
          }
          // 新进程已就绪，刷新页面加载新代码
          showMessage('重启成功，正在刷新页面...', 'info')
          setTimeout(() => { window.location.reload() }, 1500)
        })
      })
      .catch(() => {
        // 网络错误 = 后端还没启动，继续轮询
        setTimeout(check, interval)
      })
  }

  // 先等 5 秒让旧后端退出 + 新后端启动，再开始轮询
  setTimeout(check, 5000)
}

async function handleStart() {
  if (!providerStore.selectedProvider) {
    showMessage('请先选择服务商', 'error')
    return
  }
  if (!providerStore.selectedModel) {
    showMessage('请先选择模型', 'error')
    return
  }
  if (!providerStore.getCurrentApiKey()) {
    showMessage('请先配置 API Key', 'error')
    return
  }
  if (!promptStore.selectedPrompt) {
    showMessage('请先选择提示词', 'error')
    return
  }
  if (!taskStore.directoryPath) {
    showMessage('请先配置处理目录', 'error')
    return
  }
  try {
    await taskStore.start()
    logPanel.value?.resetLogsCleared()
  } catch (e) {
    showMessage(e.message || '启动失败', 'error')
  }
}

onMounted(async () => {
  // 初始化时获取 API Token（使用配置中的 secret_key）
  try {
    const settingsResp = await fetch('/api/settings/system')
    if (settingsResp.ok) {
      const settingsData = await settingsResp.json()
      const maskedKey = settingsData.settings?.secret_key || ''
      // 如果 secret_key 是默认的（未修改），尝试用默认值获取 token
      if (maskedKey.includes('******')) {
        // 密钥已设置但脱敏，尝试用默认密钥获取 token
        try {
          const tokenResult = await api.getToken('default-dev-secret-key-please-change-in-prod')
          if (tokenResult.success && tokenResult.token) {
            setApiToken(tokenResult.token)
          }
        } catch {
          // 默认密钥不匹配，用户已修改密钥，需要手动输入
        }
      }
    }
  } catch {
    // 获取系统设置失败，继续初始化
  }

  const preferences = await providerStore.loadAll()
  await Promise.all([
    promptStore.loadAll(preferences),
    trashStore.loadAll(),
  ])
  taskStore.directoryPath = providerStore.directoryPath
  taskStore.loadFailedRecords()
})
</script>

<style scoped>
/* ========== Sidebar Start Button ========== */
.sidebar-start {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border);
}

.sidebar-start .btn-start-process {
    width: 100%;
    padding: 10px 16px;
    font-size: var(--text-md);
    border-radius: var(--radius-md);
}
</style>
