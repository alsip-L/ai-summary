<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content directory-browser">
      <div class="modal-header">
        <h3>选择目录</h3>
        <button type="button" class="modal-close-btn" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="browser-toolbar">
          <div class="current-path">
            <span class="path-label">路径:</span>
            <span class="path-value">{{ currentPath || '-' }}</span>
          </div>
          <div class="browser-actions">
            <button v-if="parentPath" type="button" class="btn btn-sm btn-secondary" @click="goBack">返回</button>
            <button type="button" class="btn btn-sm btn-secondary" @click="refresh">刷新</button>
          </div>
        </div>
        <div class="directory-list">
          <div v-for="dir in directories" :key="dir.path" class="dropdown-option" @click="navigateTo(dir.path)">
            <span>{{ dir.name }}</span>
          </div>
        </div>
        <div class="direct-input-section">
          <label>或输入路径:</label>
          <input type="text" class="form-control" placeholder="输入目录路径..." v-model="directPathInput">
          <button type="button" class="btn btn-sm btn-primary" @click="goToDirectPath">前往</button>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="close">取消</button>
        <button type="button" class="btn btn-primary" :disabled="!currentPath" @click="selectDirectory">选择</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../composables/useApi'
import { useTaskStore } from '../stores/task'

const taskStore = useTaskStore()
const show = ref(false)
const currentPath = ref('')
const parentPath = ref(null)
const directories = ref([])
const directPathInput = ref('')

async function open() {
  show.value = true
  await loadDrives()
}

function close() {
  show.value = false
}

async function loadDrives() {
  const result = await api.getDirectoryContents()
  if (result.success) {
    directories.value = (result.drives || []).map(d => ({ name: d, path: d }))
    currentPath.value = ''
    parentPath.value = null
  }
}

async function navigateTo(path) {
  const result = await api.getDirectoryContents(path)
  if (result.success) {
    currentPath.value = result.path
    parentPath.value = result.parent
    directories.value = result.directories || []
  }
}

async function goBack() {
  if (parentPath.value) {
    await navigateTo(parentPath.value)
  } else {
    await loadDrives()
  }
}

async function refresh() {
  if (currentPath.value) {
    await navigateTo(currentPath.value)
  } else {
    await loadDrives()
  }
}

async function goToDirectPath() {
  const path = directPathInput.value.trim()
  if (!path) return
  await navigateTo(path)
  directPathInput.value = ''
}

function selectDirectory() {
  taskStore.directoryPath = currentPath.value
  close()
}

defineExpose({ open })
</script>
