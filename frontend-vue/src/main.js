import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '../css/base.css'
import '../css/layout.css'
import '../css/components.css'
import '../css/processing.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
