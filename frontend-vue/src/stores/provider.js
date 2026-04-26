import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../composables/useApi'

export const useProviderStore = defineStore('provider', () => {
  const providers = ref({})
  const providerNames = ref([])
  const selectedProvider = ref('')
  const selectedModel = ref('')
  const apiKey = ref('')
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

  function getCurrentModelsDetail() {
    const provider = providers.value[selectedProvider.value]
    return provider ? provider.models_detail || {} : {}
  }

  function getCurrentApiKey() {
    const provider = providers.value[selectedProvider.value]
    return provider ? provider.api_key || '' : ''
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

  async function addModel(name, displayName, modelId, params = {}) {
    await api.addModel(name, { display_name: displayName, model_id: modelId, ...params })
    await loadAll()
  }

  async function updateModelParams(name, modelName, params) {
    await api.updateModelParams(name, modelName, params)
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
    providers, providerNames, selectedProvider, selectedModel, apiKey, directoryPath,
    loadAll, getCurrentModels, getCurrentModelsDetail, getCurrentApiKey,
    createProvider, deleteProvider, saveApiKey, addModel, updateModelParams, deleteModel, savePreferences,
  }
})
