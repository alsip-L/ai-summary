import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../composables/useApi'
import { useProviderStore } from './provider'
import { usePromptStore } from './prompt'

export const useTaskStore = defineStore('task', () => {
  const status = ref('idle')
  const progress = ref(0)
  const totalFiles = ref(0)
  const processedFilesCount = ref(0)
  const currentFile = ref('')
  const results = ref([])
  const error = ref(null)
  const startTime = ref(null)
  const cancelled = ref(false)
  const directoryPath = ref('')
  const retrying = ref(false)
  const retryAttempt = ref(0)
  const retryMax = ref(3)
  const failedRecords = ref([])
  const failedCount = ref(0)

  let pollTimer = null

  const isProcessing = computed(() => status.value === 'processing' || status.value === 'scanning')

  const failedResults = computed(() => results.value.filter(r => r.error))
  const successResults = computed(() => results.value.filter(r => !r.error))

  async function start() {
    const providerStore = useProviderStore()
    const promptStore = usePromptStore()

    const apiKey = providerStore.getCurrentApiKey()
    if (!apiKey) {
      throw new Error('API Key 未配置')
    }

    const data = {
      provider: providerStore.selectedProvider,
      model: providerStore.selectedModel,
      api_key: apiKey,
      prompt: promptStore.selectedPrompt,
      directory: directoryPath.value,
      skip_existing: false,
    }

    await api.startProcessing(data)
    startPolling()
  }

  async function cancel() {
    await api.cancelProcessing()
    stopPolling()
  }

  function startPolling() {
    stopPolling()
    pollTimer = setInterval(async () => {
      try {
        const data = await api.getProcessingStatus()
        status.value = data.status
        progress.value = data.progress
        totalFiles.value = data.total_files
        processedFilesCount.value = data.processed_files_count
        currentFile.value = data.current_file
        results.value = data.results || []
        error.value = data.error
        startTime.value = data.start_time
        cancelled.value = data.cancelled
        retrying.value = data.retrying || false
        retryAttempt.value = data.retry_attempt || 0
        retryMax.value = data.retry_max || 3

        if (!isProcessing.value) {
          stopPolling()
          loadFailedRecords()
        }
      } catch (e) {
        console.error('Polling error:', e)
      }
    }, 1000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function loadStatus() {
    const data = await api.getProcessingStatus()
    status.value = data.status
    progress.value = data.progress
    totalFiles.value = data.total_files
    processedFilesCount.value = data.processed_files_count
    currentFile.value = data.current_file
    results.value = data.results || []
    error.value = data.error
    startTime.value = data.start_time
    cancelled.value = data.cancelled
    retrying.value = data.retrying || false
    retryAttempt.value = data.retry_attempt || 0
    retryMax.value = data.retry_max || 3
  }

  async function loadFailedRecords() {
    try {
      const data = await api.getFailedRecords()
      failedRecords.value = data.failed || []
      failedCount.value = data.count || 0
    } catch (e) {
      console.error('加载失败记录出错:', e)
    }
  }

  async function clearFailed() {
    try {
      await api.clearFailedRecords()
      failedRecords.value = []
      failedCount.value = 0
    } catch (e) {
      console.error('清除失败记录出错:', e)
    }
  }

  async function retryFailed() {
    const providerStore = useProviderStore()
    const promptStore = usePromptStore()

    const apiKey = providerStore.getCurrentApiKey()
    if (!apiKey) {
      throw new Error('API Key 未配置')
    }

    const data = {
      provider: providerStore.selectedProvider,
      model: providerStore.selectedModel,
      api_key: apiKey,
      prompt: promptStore.selectedPrompt,
    }

    await api.retryFailed(data)
    startPolling()
  }

  return {
    status, progress, totalFiles, processedFilesCount, currentFile,
    results, error, startTime, cancelled, directoryPath, isProcessing,
    retrying, retryAttempt, retryMax,
    failedRecords, failedCount, failedResults, successResults,
    start, cancel, loadStatus, loadFailedRecords, clearFailed, retryFailed,
    startPolling, stopPolling,
  }
})
