import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../composables/useApi'

export const useTrashStore = defineStore('trash', () => {
  const trashProviders = ref({})
  const trashPrompts = ref({})

  async function loadAll() {
    const data = await api.getTrash().catch(() => ({ providers: {}, custom_prompts: {} }))
    trashProviders.value = data.providers || {}
    trashPrompts.value = data.custom_prompts || {}
  }

  function get totalCount() {
    return Object.keys(trashProviders.value).length + Object.keys(trashPrompts.value).length
  }

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
