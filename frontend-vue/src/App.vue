<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-title">
        <span class="icon">A</span>
        AI Summary
      </div>
      <div class="sidebar-scroll">
        <div id="message" :class="['alert', message.type ? `alert-${message.type === 'error' ? 'danger' : message.type}` : '', { hidden: !message.show }]">
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
      <div v-if="!taskStore.isProcessing" class="main-content-empty">
        <button type="button" class="btn btn-start-process" @click="taskStore.start()">开始处理</button>
      </div>
      <TaskProgress v-else />
      <ResultTable v-if="taskStore.results.length > 0" />
      <LogPanel />
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

const message = reactive({ show: false, text: '', type: 'info' })

function showMessage(text, type = 'info') {
  message.show = true
  message.text = text
  message.type = type
  setTimeout(() => { message.show = false }, 2000)
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
