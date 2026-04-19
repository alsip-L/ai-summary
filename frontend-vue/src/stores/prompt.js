import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../composables/useApi'

export const usePromptStore = defineStore('prompt', () => {
  const prompts = ref({})
  const promptNames = ref([])
  const selectedPrompt = ref('')

  async function loadAll() {
    const [preferences, promptData] = await Promise.all([
      api.getPreferences().catch(() => ({})),
      api.getPrompts().catch(() => ({})),
    ])
    prompts.value = promptData || {}
    promptNames.value = Object.keys(prompts.value)
    selectedPrompt.value = preferences.selected_prompt || ''
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
