<template>
  <div class="results-container">
    <div class="results-header">
      <span>处理结果</span>
      <span class="results-count">{{ taskStore.results.length }}</span>
    </div>
    <div class="results-list">
      <div v-for="(result, i) in taskStore.results" :key="i" class="result-item">
        <span class="result-source" :title="result.source">{{ fileName(result.source) }}</span>
        <span class="result-arrow">&#8594;</span>
        <span class="result-output">
          <span v-if="result.error" class="result-error">{{ result.error }}</span>
          <a v-else-if="result.output" href="#" @click.prevent="viewResult(result.output)" :title="result.output">{{ fileName(result.output) }}</a>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTaskStore } from '../stores/task'
import { api } from '../composables/useApi'

const taskStore = useTaskStore()

function fileName(path) {
  if (!path) return ''
  const sep = path.includes('/') ? '/' : '\\'
  const parts = path.split(sep)
  return parts[parts.length - 1] || path
}

async function viewResult(filePath) {
  try {
    const result = await api.viewResult(filePath)
    if (result.success) {
      alert(result.content)
    }
  } catch (e) {
    console.error('查看结果失败:', e)
  }
}
</script>
