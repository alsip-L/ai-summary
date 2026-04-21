<template>
  <div id="prompt-section">
    <div class="section-header">提示词</div>
    <div class="form-group">
      <label class="form-label">系统提示词</label>
      <div class="custom-dropdown">
        <div class="dropdown-selected" @click="showDropdown = !showDropdown">
          <span>{{ store.selectedPrompt || '请选择...' }}</span>
          <span class="dropdown-arrow">&#9662;</span>
        </div>
        <div class="dropdown-content" :class="{ show: showDropdown }">
          <div v-for="name in store.promptNames" :key="name" class="dropdown-option" @click.stop="selectPrompt(name)">
            <span>{{ name }}</span>
            <button type="button" class="delete-option-btn" @click.stop="deletePrompt(name)">&times;</button>
          </div>
          <div class="dropdown-option" @click.stop="addNew">
            <span style="color: var(--accent-indigo);">+ 新增提示词</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="currentContent" class="prompt-preview">
      <label class="form-label">内容预览</label>
      <textarea readonly rows="4" class="form-control prompt-preview-text" :value="currentContent"></textarea>
    </div>

    <div v-if="showDialog" class="modal-overlay" @click.self="showDialog = false">
      <div class="modal-content">
        <div class="modal-header"><h3>新增提示词</h3></div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">名称</label>
            <input type="text" class="form-control" placeholder="如: 文章摘要" v-model="newName">
          </div>
          <div class="form-group">
            <label class="form-label">内容</label>
            <textarea class="form-control" placeholder="输入提示词内容..." rows="4" v-model="newContent"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="showDialog = false">取消</button>
          <button type="button" class="btn btn-primary btn-sm" @click="submitNew">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import { usePromptStore } from '../stores/prompt'
import { useTrashStore } from '../stores/trash'

const store = usePromptStore()
const trashStore = useTrashStore()
const showMessage = inject('showMessage')

const showDropdown = ref(false)

function onDocumentClick(e) {
  if (!e.target.closest('#prompt-section .custom-dropdown')) {
    showDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))
const showDialog = ref(false)
const newName = ref('')
const newContent = ref('')

const currentContent = computed(() => store.prompts[store.selectedPrompt] || '')

async function selectPrompt(name) {
  showDropdown.value = false
  try {
    store.selectedPrompt = name
    await store.savePreferences()
    showMessage('已保存', 'success')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

async function deletePrompt(name) {
  showDropdown.value = false
  if (!confirm(`确定删除提示词 '${name}' 吗？`)) return
  try {
    await store.deletePrompt(name)
    await trashStore.loadAll()
  } catch (e) {
    showMessage('删除失败: ' + e.message, 'error')
  }
}

function addNew() {
  showDropdown.value = false
  newName.value = ''
  newContent.value = ''
  showDialog.value = true
}

async function submitNew() {
  const name = newName.value.trim()
  const content = newContent.value.trim()
  if (!name || !content) { showMessage('两项均为必填', 'warning'); return }
  try {
    await store.createPrompt(name, content)
    showDialog.value = false
  } catch (e) {
    showMessage('创建失败: ' + e.message, 'error')
  }
}
</script>
