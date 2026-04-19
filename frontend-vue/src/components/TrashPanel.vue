<template>
  <div class="custom-dropdown" id="trash-dropdown">
    <div class="dropdown-selected" @click="showDropdown = !showDropdown">
      <span class="dropdown-label-group">
        <span>回收站</span>
        <span v-if="trashStore.totalCount > 0" class="results-count">{{ trashStore.totalCount }}</span>
      </span>
      <span class="dropdown-arrow">&#9662;</span>
    </div>
    <div class="dropdown-content trash-content-area" :class="{ show: showDropdown }">
      <div id="trash-section">
        <div v-if="trashStore.totalCount === 0" class="dropdown-option" style="color: var(--text-muted, #999); justify-content: center;">
          回收站为空
        </div>
        <div v-if="Object.keys(trashStore.trashProviders).length > 0">
          <div class="form-label" style="margin-top: 4px;">服务商</div>
          <div v-for="(provider, name) in trashStore.trashProviders" :key="name" class="dropdown-option" style="justify-content: space-between;">
            <span>{{ name }}</span>
            <div>
              <button type="button" class="btn btn-sm btn-secondary" @click="restoreProvider(name)">恢复</button>
              <button type="button" class="btn btn-sm btn-outline-danger" @click="permanentDeleteProvider(name)">永久删除</button>
            </div>
          </div>
        </div>
        <div v-if="Object.keys(trashStore.trashPrompts).length > 0">
          <div class="form-label" style="margin-top: 8px;">提示词</div>
          <div v-for="(content, name) in trashStore.trashPrompts" :key="name" class="dropdown-option" style="justify-content: space-between;">
            <span>{{ name }}</span>
            <div>
              <button type="button" class="btn btn-sm btn-secondary" @click="restorePrompt(name)">恢复</button>
              <button type="button" class="btn btn-sm btn-outline-danger" @click="permanentDeletePrompt(name)">永久删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useTrashStore } from '../stores/trash'
import { useProviderStore } from '../stores/provider'
import { usePromptStore } from '../stores/prompt'

const trashStore = useTrashStore()
const providerStore = useProviderStore()
const promptStore = usePromptStore()
const showMessage = inject('showMessage')

const showDropdown = ref(false)

async function restoreProvider(name) {
  try {
    await trashStore.restoreProvider(name)
    await providerStore.loadAll()
    showMessage('已恢复', 'success')
  } catch (e) {
    showMessage('恢复失败: ' + e.message, 'error')
  }
}

async function permanentDeleteProvider(name) {
  if (!confirm(`确定永久删除服务商 '${name}' 吗？此操作不可撤销。`)) return
  try {
    await trashStore.permanentDeleteProvider(name)
    showMessage('已永久删除', 'success')
  } catch (e) {
    showMessage('删除失败: ' + e.message, 'error')
  }
}

async function restorePrompt(name) {
  try {
    await trashStore.restorePrompt(name)
    await promptStore.loadAll()
    showMessage('已恢复', 'success')
  } catch (e) {
    showMessage('恢复失败: ' + e.message, 'error')
  }
}

async function permanentDeletePrompt(name) {
  if (!confirm(`确定永久删除提示词 '${name}' 吗？此操作不可撤销。`)) return
  try {
    await trashStore.permanentDeletePrompt(name)
    showMessage('已永久删除', 'success')
  } catch (e) {
    showMessage('删除失败: ' + e.message, 'error')
  }
}
</script>
