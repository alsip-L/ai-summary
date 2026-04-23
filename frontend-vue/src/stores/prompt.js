import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../composables/useApi'

export const usePromptStore = defineStore('prompt', () => {
  const prompts = ref({})
  const promptNames = ref([])
  const selectedPrompt = ref('')

  async function loadAll(preferences = null) {
    const prefs = preferences || await api.getPreferences().catch(() => ({}))
    const promptData = await api.getPrompts().catch(() => ({ prompts: [] }))
    const promptList = promptData.prompts || []
    const promptMap = {}
    for (const p of promptList) {
      promptMap[p.name] = p.content
    }
    prompts.value = promptMap
    promptNames.value = Object.keys(promptMap)
    selectedPrompt.value = prefs.selected_prompt || ''
    if (selectedPrompt.value && !prompts.value[selectedPrompt.value]) {
      selectedPrompt.value = ''
      await api.savePreferences({ selected_prompt: '' }).catch(() => {})
    }
  }

  async function createPrompt(name, content) {
    await api.createPrompt({ name, content })
    await loadAll()
  }

  async function deletePrompt(name) {
    await api.deletePrompt(name)
    await loadAll()
  }

  async function savePreferences() {
    await api.savePreferences({ selected_prompt: selectedPrompt.value })
  }

  return {
    prompts, promptNames, selectedPrompt,
    loadAll, createPrompt, deletePrompt, savePreferences,
  }
})
