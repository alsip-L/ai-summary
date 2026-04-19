<template>
  <div v-if="taskStore.results.length > 0" class="results-container">
    <div class="results-header">
      <span>处理结果</span>
      <span class="results-count">{{ taskStore.results.length }}</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>源文件</th>
          <th>输出</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(result, i) in taskStore.results" :key="i">
          <td>{{ result.source }}</td>
          <td>
            <span v-if="result.error" style="color: red;">{{ result.error }}</span>
            <a v-else-if="result.output" href="#" @click.prevent="viewResult(result.output)">{{ result.output }}</a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { useTaskStore } from '../stores/task'
import { api } from '../composables/useApi'

const taskStore = useTaskStore()

async function viewResult(filePath) {
  try {
    const result = await api.viewResult(filePath)
    if (result.success) {
      alert(result.content)
    }
  } catch (e) {
    console.error('查看结果失败:', e)
  }
}
</script>
