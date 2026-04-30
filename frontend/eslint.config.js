import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
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
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': ['warn', {
        html: { void: 'any' },
      }],
      'vue/multi-word-component-names': 'off',
      'vue/attributes-order': 'off',
    },
  },
]
