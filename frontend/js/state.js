/* frontend/js/state.js — 前端状态管理 */

const AppState = {
    // 当前配置
    selectedProvider: '',
    selectedModel: '',
    selectedPrompt: '',
    directoryPath: '',
    apiKey: '',

    // 提供商数据
    providers: {},       // { name: { base_url, api_key, models: { display: id } } }
    providerNames: [],

    // 提示词数据
    prompts: {},         // { name: content }
    promptNames: [],

    // 回收站
    trashProviders: {},
    trashPrompts: {},

    // 处理状态
    isProcessing: false,

    /** 从服务端加载全部初始数据 */
    async loadAll() {
        const [preferences, providers, prompts, trash] = await Promise.all([
            API.getPreferences().catch(() => ({})),
            API.getProviders().catch(() => ({})),
            API.getPrompts().catch(() => ({})),
            API.getTrash().catch(() => ({ providers: {}, custom_prompts: {} }))
        ]);

        // 用户偏好
        this.selectedProvider = preferences.selected_provider || '';
        this.selectedModel = preferences.selected_model || '';
        this.selectedPrompt = preferences.selected_prompt || '';
        this.directoryPath = preferences.directory_path || '';
        this.apiKey = preferences.api_key || '';

        // 提供商
        this.providers = providers || {};
        this.providerNames = Object.keys(this.providers);

        // 提示词
        this.prompts = prompts || {};
        this.promptNames = Object.keys(this.prompts);

        // 回收站
        this.trashProviders = trash.providers || {};
        this.trashPrompts = trash.custom_prompts || {};

        return this;
    },

    /** 获取当前提供商的模型列表 */
    getCurrentModels() {
        const provider = this.providers[this.selectedProvider];
        return provider ? provider.models || {} : {};
    },

    /** 获取当前 API Key */
    getCurrentApiKey() {
        const provider = this.providers[this.selectedProvider];
        return provider ? provider.api_key || '' : '';
    }
};

window.AppState = AppState;
