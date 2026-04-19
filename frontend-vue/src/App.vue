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
    </aside>
    <main class="main-content">
      <div v-if="!taskStore.isProcessing" class="main-content-empty">
        <div class="empty-icon">A</div>
        <button type="button" class="btn btn-start-process" @click="taskStore.start()">开始处理</button>
        <div class="empty-text">选择服务商、模型和目录后，开始批量处理</div>
      </div>
      <TaskProgress v-else />
      <ResultTable v-if="taskStore.results.length > 0" />
    </main>
  </div>
  <DirectoryBrowser />
</template>

<script setup>
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

const providerStore = useProviderStore()
const promptStore = usePromptStore()
const taskStore = useTaskStore()
const trashStore = useTrashStore()

const message = reactive({ show: false, text: '', type: 'info' })

function showMessage(text, type = 'info') {
  message.show = true
  message.text = text
  message.type = type
  setTimeout(() => { message.show = false }, 2000)
}

provide('showMessage', showMessage)

onMounted(async () => {
  await Promise.all([
    providerStore.loadAll(),
    promptStore.loadAll(),
    trashStore.loadAll(),
  ])
})
</script>

<script>
import { reactive, provide, onMounted } from 'vue'
export default { name: 'App' }
</script>
