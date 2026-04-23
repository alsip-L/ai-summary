import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../composables/useApi'

export const useProviderStore = defineStore('provider', () => {
  const providers = ref({})
  const providerNames = ref([])
  const selectedProvider = ref('')
  const selectedModel = ref('')
  const apiKey = ref('')
  const apiKeyMasked = ref(false)
  const directoryPath = ref('')

  async function loadAll() {
    const [preferences, providerData] = await Promise.all([
      api.getPreferences().catch(() => ({})),
      api.getProviders().catch(() => ({ providers: [] })),
    ])
    const providerList = providerData.providers || []
    const providerMap = {}
    for (const p of providerList) {
      providerMap[p.name] = p
    }
    providers.value = providerMap
    providerNames.value = Object.keys(providerMap)
    selectedProvider.value = preferences.selected_provider || ''
    selectedModel.value = preferences.selected_model || ''
    apiKey.value = preferences.api_key || ''
    directoryPath.value = preferences.directory_path || ''
    // 标记 API Key 是否为脱敏状态
    apiKeyMasked.value = !!preferences.api_key_masked
    let needSave = false
    if (selectedProvider.value && !providers.value[selectedProvider.value]) {
      selectedProvider.value = ''
      selectedModel.value = ''
      apiKey.value = ''
      needSave = true
    }
    if (selectedProvider.value && selectedModel.value && !getCurrentModels()[selectedModel.value]) {
      selectedModel.value = ''
      needSave = true
    }
    if (needSave) {
      await api.savePreferences({
        selected_provider: selectedProvider.value,
        selected_model: selectedModel.value,
      }).catch(() => {})
    }
    return preferences
  }

  function getCurrentModels() {
    const provider = providers.value[selectedProvider.value]
    return provider ? provider.models || {} : {}
  }

  function getCurrentApiKey() {
    const provider = providers.value[selectedProvider.value]
    return provider ? provider.api_key || '' : ''
  }

  function isCurrentApiKeyMasked() {
    const provider = providers.value[selectedProvider.value]
    return provider ? !!provider.api_key_masked : false
  }

  async function fetchFullApiKey(name) {
    // 优先从 provider 端点获取
    if (name) {
      const result = await api.getApiKey(name)
      return result.api_key || ''
    }
    // 从 preferences 认证端点获取
    const result = await api.getPreferencesApiKey()
    if (result.api_key) {
      apiKey.value = result.api_key
      apiKeyMasked.value = false
    }
    return result.api_key || ''
  }

  async function createProvider(data) {
    await api.createProvider(data)
    await loadAll()
  }

  async function deleteProvider(name) {
    await api.deleteProvider(name)
    await loadAll()
  }

  async function saveApiKey(name, key) {
    await api.saveApiKey(name, key)
    apiKey.value = key
    await api.savePreferences({ api_key: key }).catch(() => {})
    await loadAll()
  }

  async function addModel(name, displayName, modelId) {
    await api.addModel(name, { display_name: displayName, model_id: modelId })
    await loadAll()
  }

  async function deleteModel(name, modelName) {
    await api.deleteModel(name, modelName)
    await loadAll()
  }

  async function savePreferences(directoryPath) {
    const data = {
      selected_provider: selectedProvider.value,
      selected_model: selectedModel.value,
    }
    if (directoryPath !== undefined) {
      data.directory_path = directoryPath
    }
    await api.savePreferences(data)
  }

  return {
    providers, providerNames, selectedProvider, selectedModel, apiKey, apiKeyMasked, directoryPath,
    loadAll, getCurrentModels, getCurrentApiKey, isCurrentApiKeyMasked, fetchFullApiKey,
    createProvider, deleteProvider, saveApiKey, addModel, deleteModel, savePreferences,
  }
})
