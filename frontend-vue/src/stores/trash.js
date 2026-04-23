import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../composables/useApi'

export const useTrashStore = defineStore('trash', () => {
  const trashProviders = ref({})
  const trashPrompts = ref({})

  async function loadAll() {
    const data = await api.getTrash().catch(() => ({ providers: [], custom_prompts: [] }))
    // providers 和 custom_prompts 现在是列表格式
    const providerList = Array.isArray(data.providers) ? data.providers : []
    const promptList = Array.isArray(data.custom_prompts) ? data.custom_prompts : []
    const providerMap = {}
    for (const p of providerList) {
      providerMap[p.name] = p
    }
    const promptMap = {}
    for (const p of promptList) {
      promptMap[p.name] = p.content !== undefined ? p.content : p
    }
    trashProviders.value = providerMap
    trashPrompts.value = promptMap
  }

  const totalCount = computed(() => Object.keys(trashProviders.value).length + Object.keys(trashPrompts.value).length)

  async function restoreProvider(name) {
    await api.restoreProvider(name)
    await loadAll()
  }

  async function permanentDeleteProvider(name) {
    await api.permanentDeleteProvider(name)
    await loadAll()
  }

  async function restorePrompt(name) {
    await api.restorePrompt(name)
    await loadAll()
  }

  async function permanentDeletePrompt(name) {
    await api.permanentDeletePrompt(name)
    await loadAll()
  }

  return {
    trashProviders, trashPrompts,
    loadAll, totalCount,
    restoreProvider, permanentDeleteProvider, restorePrompt, permanentDeletePrompt,
  }
})
