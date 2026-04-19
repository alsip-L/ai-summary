<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-title">
        <span class="icon">A</span>
        AI Summary
      </div>
      <div v-if="!taskStore.isProcessing" class="sidebar-start">
        <button type="button" class="btn btn-start-process" @click="taskStore.start()">开始处理</button>
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
        <a class="btn btn-secondary btn-admin" href="/admin/" target="_blank" rel="noopener">
          <span class="btn-admin-icon">&#9881;</span>
          数据库管理
        </a>
      </div>
    </aside>
    <main class="main-content">
      <div class="main-content-upper">
        <div v-if="!taskStore.isProcessing && taskStore.results.length === 0" class="main-content-empty">
          <span class="empty-hint">配置左侧参数后，点击「开始处理」</span>
        </div>
        <TaskProgress v-if="taskStore.isProcessing" />
        <ResultTable v-if="taskStore.results.length > 0" />
      </div>
      <div class="main-content-lower">
        <LogPanel />
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

const message = reactive({ show: false, text: '', type: 'info', fading: false })

function showMessage(text, type = 'info') {
  message.show = true
  message.text = text
  message.type = type
  message.fading = false
  setTimeout(() => {
    message.fading = true
    setTimeout(() => { message.show = false; message.fading = false }, 200)
  }, 1800)
}

provide('showMessage', showMessage)
provide('openDirectoryBrowser', () => directoryBrowser.value?.open())

onMounted(async () => {
  await Promise.all([
    providerStore.loadAll(),
    promptStore.loadAll(),
    trashStore.loadAll(),
  ])
  taskStore.directoryPath = providerStore.directoryPath
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
