import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '../frontend/css/base.css'
import '../frontend/css/layout.css'
import '../frontend/css/components.css'
import '../frontend/css/processing.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
