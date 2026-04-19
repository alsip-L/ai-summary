<template>
  <div id="provider-section">
    <div class="section-header">服务商</div>
    <div class="form-group">
      <label class="form-label">AI 服务商</label>
      <div class="custom-dropdown">
        <div class="dropdown-selected" @click="toggleProviderDropdown">
          <span>{{ store.selectedProvider || '请选择...' }}</span>
          <span class="dropdown-arrow">&#9662;</span>
        </div>
        <div class="dropdown-content" :class="{ show: showProviderDropdown }">
          <div v-for="name in store.providerNames" :key="name" class="dropdown-option" @click.stop="selectProvider(name)">
            <span>{{ name }}</span>
            <button type="button" class="delete-option-btn" @click.stop="deleteProvider(name)">&times;</button>
          </div>
          <div class="dropdown-option" @click.stop="addNew">
            <span style="color: var(--accent-indigo);">+ 新增服务商</span>
          </div>
        </div>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">模型</label>
      <div class="custom-dropdown">
        <div class="dropdown-selected" @click="toggleModelDropdown">
          <span>{{ store.selectedModel || '请选择...' }}</span>
          <span class="dropdown-arrow">&#9662;</span>
        </div>
        <div class="dropdown-content" :class="{ show: showModelDropdown }">
          <div v-for="display in modelKeys" :key="display" class="dropdown-option" @click.stop="selectModel(display)">
            <span>{{ display }}</span>
            <button type="button" class="delete-option-btn" @click.stop="deleteModel(display)">&times;</button>
          </div>
          <div class="dropdown-option" @click.stop="addModel">
            <span style="color: var(--accent-indigo);">+ 新增模型</span>
          </div>
        </div>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">API Key</label>
      <input type="text" class="form-control" v-model="apiKeyInput" :placeholder="apiKeyInput ? '已配置' : '请输入 API Key'" @blur="saveApiKey">
    </div>
    <div class="form-group">
      <label class="form-label">处理目录</label>
      <div class="input-group">
        <input type="text" class="form-control" v-model="directoryPath" placeholder="输入目录路径" @blur="saveDirectoryPath">
        <button type="button" class="btn btn-sm btn-secondary" @click="$emit('open-directory')">浏览</button>
      </div>
    </div>

    <div v-if="showDialog" class="modal-overlay" @click.self="showDialog = false">
      <div class="modal-content">
        <div class="modal-header"><h3>{{ dialogTitle }}</h3></div>
        <div class="modal-body">
          <div v-for="field in dialogFields" :key="field.id" class="form-group">
            <label class="form-label">{{ field.label }}</label>
            <textarea v-if="field.type === 'textarea'" :id="field.id" class="form-control" :placeholder="field.placeholder || ''" v-model="field.value"></textarea>
            <input v-else :type="field.type || 'text'" :id="field.id" class="form-control" :placeholder="field.placeholder || ''" v-model="field.value">
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="showDialog = false">取消</button>
          <button type="button" class="btn btn-primary btn-sm" @click="submitDialog">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useProviderStore } from '../stores/provider'
import { useTaskStore } from '../stores/task'
import { useTrashStore } from '../stores/trash'

const store = useProviderStore()
const taskStore = useTaskStore()
const trashStore = useTrashStore()
const showMessage = inject('showMessage')

const showProviderDropdown = ref(false)
const showModelDropdown = ref(false)
const apiKeyInput = ref(store.apiKey)
const directoryPath = ref(taskStore.directoryPath)

const modelKeys = computed(() => Object.keys(store.getCurrentModels()))

const showDialog = ref(false)
const dialogTitle = ref('')
const dialogFields = ref([])
let dialogSubmit = null

function toggleProviderDropdown() {
  showProviderDropdown.value = !showProviderDropdown.value
  showModelDropdown.value = false
}

function toggleModelDropdown() {
  showModelDropdown.value = !showModelDropdown.value
  showProviderDropdown.value = false
}

async function selectProvider(name) {
  showProviderDropdown.value = false
  try {
    store.selectedProvider = name
    const models = store.getCurrentModels()
    store.selectedModel = Object.keys(models)[0] || ''
    store.apiKey = store.getCurrentApiKey()
    apiKeyInput.value = store.apiKey
    await store.savePreferences()
    showMessage('已保存', 'success')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

async function selectModel(name) {
  showModelDropdown.value = false
  try {
    store.selectedModel = name
    await store.savePreferences()
    showMessage('已保存', 'success')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

async function deleteProvider(name) {
  showProviderDropdown.value = false
  if (!confirm(`确定删除服务商 '${name}' 吗？`)) return
  try {
    await store.deleteProvider(name)
    await trashStore.loadAll()
  } catch (e) {
    showMessage('删除失败: ' + e.message, 'error')
  }
}

async function deleteModel(modelDisplay) {
  showModelDropdown.value = false
  if (!confirm(`确定从 '${store.selectedProvider}' 删除模型 '${modelDisplay}' 吗？`)) return
  try {
    await store.deleteModel(store.selectedProvider, modelDisplay)
  } catch (e) {
    showMessage('删除失败: ' + e.message, 'error')
  }
}

async function saveApiKey() {
  if (!store.selectedProvider) return
  try {
    await store.saveApiKey(store.selectedProvider, apiKeyInput.value.trim())
    showMessage('API Key 已保存', 'success')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

async function saveDirectoryPath() {
  const path = directoryPath.value.trim()
  if (!path) return
  try {
    taskStore.directoryPath = path
    await store.savePreferences()
    showMessage('目录路径已保存', 'success')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

function addNew() {
  showProviderDropdown.value = false
  dialogTitle.value = '新增服务商'
  dialogFields.value = [
    { id: 'name', label: '名称', placeholder: '如: OpenAI', value: '' },
    { id: 'base_url', label: 'API 地址', placeholder: '如: https://api.openai.com/v1', value: '' },
    { id: 'api_key', label: 'API Key', placeholder: '可选', value: '' },
    { id: 'model_name', label: '模型名称', placeholder: '可选，如: gpt-4', value: '' },
  ]
  dialogSubmit = async () => {
    const name = dialogFields.value[0].value.trim()
    const url = dialogFields.value[1].value.trim()
    const apiKey = dialogFields.value[2].value.trim()
    const modelName = dialogFields.value[3].value.trim()
    if (!name || !url) { showMessage('名称和地址为必填', 'warning'); return false }
    const models = modelName ? { [modelName]: modelName } : { 'default': name.toLowerCase().replace(/\s+/g, '-') + '-model' }
    await store.createProvider({ name, base_url: url, api_key: apiKey, models })
    return true
  }
  showDialog.value = true
}

function addModel() {
  showModelDropdown.value = false
  if (!store.selectedProvider) { showMessage('请先选择服务商', 'warning'); return }
  dialogTitle.value = `新增模型 — ${store.selectedProvider}`
  dialogFields.value = [
    { id: 'display_name', label: '显示名称', placeholder: '如: GPT-4', value: '' },
    { id: 'model_id', label: '模型 ID', placeholder: '如: gpt-4', value: '' },
  ]
  dialogSubmit = async () => {
    const display = dialogFields.value[0].value.trim()
    const id = dialogFields.value[1].value.trim()
    if (!display || !id) { showMessage('两项均为必填', 'warning'); return false }
    await store.addModel(store.selectedProvider, display, id)
    return true
  }
  showDialog.value = true
}

async function submitDialog() {
  if (dialogSubmit) {
    const ok = await dialogSubmit()
    if (ok !== false) showDialog.value = false
  }
}
</script>
