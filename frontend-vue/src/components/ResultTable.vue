<template>
  <div class="results-container">
    <div class="results-header">
      <span>处理结果</span>
      <span class="results-count">{{ taskStore.results.length }}</span>
      <span v-if="hasFailed" class="results-failed-count">{{ failedTotal }} 失败</span>
    </div>
    <!-- 失败操作栏 -->
    <div v-if="hasFailed && !taskStore.isProcessing" class="failed-actions">
      <div class="failed-hint">可在左侧切换服务商/模型/Prompt后重跑</div>
      <div class="failed-buttons">
        <button type="button" class="btn btn-sm btn-retry" @click="handleRetryFailed" :disabled="retrying">
          {{ retrying ? '重跑中...' : '重跑失败文件' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-danger" @click="handleClearFailed">清除记录</button>
      </div>
      <div v-if="retryError" class="retry-error-msg">{{ retryError }}</div>
    </div>
    <div class="results-list">
      <div v-for="(result, i) in taskStore.results" :key="i" class="result-item" :class="{ 'result-item-failed': result.error }">
        <span class="result-source" :title="result.source">{{ fileName(result.source) }}</span>
        <span class="result-arrow">&#8594;</span>
        <span class="result-output">
          <span v-if="result.error" class="result-error">
            {{ result.error }}
            <span v-if="result.retryable" class="result-retryable-tag">可重试</span>
          </span>
          <a v-else-if="result.output" href="#" @click.prevent="viewResult(result.output)" :title="result.output">{{ fileName(result.output) }}</a>
        </span>
      </div>
    </div>

    <!-- 结果查看模态框 -->
    <div v-if="showResultModal" class="modal-overlay" @click.self="showResultModal = false">
      <div class="modal-content result-modal-content">
        <div class="modal-header">
          <h3>处理结果</h3>
          <button type="button" class="modal-close-btn" @click="showResultModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <pre class="result-modal-text">{{ resultModalContent }}</pre>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="showResultModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useTaskStore } from '../stores/task'
import { api } from '../composables/useApi'

const taskStore = useTaskStore()
const resetLogsCleared = inject('resetLogsCleared', () => {})
const retrying = ref(false)
const retryError = ref('')
const showResultModal = ref(false)
const resultModalContent = ref('')

const hasFailed = computed(() =>
  taskStore.failedResults.length > 0 || taskStore.failedCount > 0
)

const failedTotal = computed(() =>
  taskStore.failedResults.length > 0 ? taskStore.failedResults.length : taskStore.failedCount
)

onMounted(() => {
  taskStore.loadFailedRecords()
})

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
      resultModalContent.value = result.content
      showResultModal.value = true
    }
  } catch (e) {
    console.error('查看结果失败:', e)
  }
}

async function handleRetryFailed() {
  retrying.value = true
  retryError.value = ''
  try {
    await taskStore.retryFailed()
    resetLogsCleared()
  } catch (e) {
    retryError.value = e.message || '重跑失败'
    console.error('重跑失败文件出错:', e)
  } finally {
    retrying.value = false
  }
}

async function handleClearFailed() {
  retryError.value = ''
  await taskStore.clearFailed()
}
</script>

<style scoped>
.result-modal-content {
  max-width: 720px;
}
.result-modal-text {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: var(--text-primary);
  background: var(--bg-canvas);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  max-height: 60vh;
  overflow-y: auto;
}
</style>
