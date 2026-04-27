import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      globals: {
        fetch: 'readonly',
        File: 'readonly',
        FormData: 'readonly',
      },
    },
    rules: {
      'no-undef': 'off',
    },
  },
]
