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
      <div v-if="currentModelParams" class="model-params-hint">
        <span>T={{ currentModelParams.temperature }}</span>
        <span>FP={{ currentModelParams.frequency_penalty }}</span>
        <span>PP={{ currentModelParams.presence_penalty }}</span>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">API Key</label>
      <div class="input-group">
        <input type="text" class="form-control" :value="store.apiKey" :placeholder="store.apiKey ? '已配置' : '未配置'" readonly>
        <button type="button" class="btn btn-sm btn-secondary" @click="copyApiKey" title="复制完整 API Key">复制</button>
        <button type="button" class="btn btn-sm btn-secondary" @click="editApiKey" title="修改 API Key">修改</button>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">处理目录</label>
      <div class="input-group">
        <input type="text" class="form-control" v-model="store.directoryPath" placeholder="输入目录路径" @blur="saveDirectoryPath">
        <button type="button" class="btn btn-sm btn-secondary" @click="openDirectoryBrowser">浏览</button>
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
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import { useProviderStore } from '../stores/provider'
import { useTaskStore } from '../stores/task'
import { useTrashStore } from '../stores/trash'

const store = useProviderStore()
const taskStore = useTaskStore()
const trashStore = useTrashStore()
const showMessage = inject('showMessage')
const openDirectoryBrowser = inject('openDirectoryBrowser')

const showProviderDropdown = ref(false)
const showModelDropdown = ref(false)

function closeAllDropdowns() {
  showProviderDropdown.value = false
  showModelDropdown.value = false
}

function onDocumentClick(e) {
  const el = e.target.closest('.custom-dropdown')
  if (!el) closeAllDropdowns()
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

const modelKeys = computed(() => Object.keys(store.getCurrentModels()))

const currentModelParams = computed(() => {
  const detail = store.getCurrentModelsDetail()
  const model = store.selectedModel
  return detail[model] || null
})

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

async function copyApiKey() {
  if (!store.selectedProvider) { showMessage('请先选择服务商', 'warning'); return }
  const key = store.apiKey
  if (!key) { showMessage('未配置 API Key', 'warning'); return }
  try {
    await navigator.clipboard.writeText(key)
    showMessage('API Key 已复制到剪贴板', 'success')
  } catch (e) {
    showMessage('复制失败: ' + e.message, 'error')
  }
}

function editApiKey() {
  if (!store.selectedProvider) { showMessage('请先选择服务商', 'warning'); return }
  dialogTitle.value = `修改 API Key — ${store.selectedProvider}`
  dialogFields.value = [
    { id: 'api_key', label: 'API Key', placeholder: '输入新的 API Key', value: '', type: 'text' },
  ]
  dialogSubmit = async () => {
    const key = dialogFields.value[0].value.trim()
    if (!key) { showMessage('API Key 不能为空', 'warning'); return false }
    await store.saveApiKey(store.selectedProvider, key)
    showMessage('API Key 已更新', 'success')
    return true
  }
  showDialog.value = true
}

async function saveDirectoryPath() {
  const path = store.directoryPath.trim()
  if (!path) return
  try {
    taskStore.directoryPath = path
    await store.savePreferences(path)
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
    if (!/^https?:\/\//.test(url)) { showMessage('API 地址须以 http:// 或 https:// 开头', 'warning'); return false }
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
    { id: 'temperature', label: '温度 (0-2)', placeholder: '默认 0.7', value: '0.7', type: 'number' },
    { id: 'frequency_penalty', label: '频率惩罚 (-2~2)', placeholder: '默认 0.4', value: '0.4', type: 'number' },
    { id: 'presence_penalty', label: '存在惩罚 (-2~2)', placeholder: '默认 0.2', value: '0.2', type: 'number' },
  ]
  dialogSubmit = async () => {
    const display = dialogFields.value[0].value.trim()
    const id = dialogFields.value[1].value.trim()
    if (!display || !id) { showMessage('显示名称和模型ID为必填', 'warning'); return false }
    const temperature = parseFloat(dialogFields.value[2].value)
    const frequency_penalty = parseFloat(dialogFields.value[3].value)
    const presence_penalty = parseFloat(dialogFields.value[4].value)
    const params = {
      temperature: isNaN(temperature) ? 0.7 : temperature,
      frequency_penalty: isNaN(frequency_penalty) ? 0.4 : frequency_penalty,
      presence_penalty: isNaN(presence_penalty) ? 0.2 : presence_penalty,
    }
    await store.addModel(store.selectedProvider, display, id, params)
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

<style scoped>
.model-params-hint {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-muted, #888);
}
</style>
