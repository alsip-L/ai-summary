<template>
  <div class="processing-status-panel">
    <div class="progress-header">
      <div class="progress-title">
        <span class="status-icon">{{ statusIcon }}</span>
        <span>{{ statusTitle }}</span>
      </div>
      <div class="progress-percentage">{{ taskStore.progress }}%</div>
    </div>
    <div class="progress-main">
      <div class="progress-bar-wrapper">
        <div class="progress-bar-advanced">
          <div class="progress-fill" :style="{ width: taskStore.progress + '%' }"></div>
          <div class="progress-glow"></div>
        </div>
      </div>
      <div class="progress-details">
        <div class="progress-stats">
          <div class="stat-item">
            <span class="stat-label">当前文件</span>
            <span class="stat-value">{{ taskStore.currentFile || '-' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">进度</span>
            <span class="stat-value">{{ taskStore.processedFilesCount }} / {{ taskStore.totalFiles }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">耗时</span>
            <span class="stat-value">{{ elapsedTime }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="progress-footer">
      <div class="status-message">{{ statusMessage }}</div>
      <div class="progress-actions">
        <button v-if="taskStore.isProcessing" type="button" class="btn btn-sm btn-outline-danger" @click="taskStore.cancel()">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTaskStore } from '../stores/task'

const taskStore = useTaskStore()

const statusIcon = computed(() => {
  const map = { idle: '⏳', scanning: '🔍', processing: '⚙️', completed: '✅', error: '❌', cancelled: '🚫' }
  return map[taskStore.status] || '⏳'
})

const statusTitle = computed(() => {
  const map = { idle: '就绪', scanning: '扫描中', processing: '处理中', completed: '已完成', error: '出错', cancelled: '已取消' }
  return map[taskStore.status] || '就绪'
})

const statusMessage = computed(() => {
  if (taskStore.error) return taskStore.error
  const map = { idle: '等待开始...', scanning: '正在扫描文件...', processing: '正在处理文件...', completed: '处理完成', cancelled: '已取消' }
  return map[taskStore.status] || '等待开始...'
})

const elapsedTime = computed(() => {
  if (!taskStore.startTime) return '0:00'
  const elapsed = Math.floor((Date.now() / 1000) - taskStore.startTime)
  const min = Math.floor(elapsed / 60)
  const sec = elapsed % 60
  return `${min}:${sec.toString().padStart(2, '0')}`
})
</script>
