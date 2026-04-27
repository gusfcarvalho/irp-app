import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import vueTsEslintConfig from '@vue/eslint-config-typescript'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  ...vueTsEslintConfig(),
  {
    files: ['**/*.{js,vue}'],
    rules: {
      'no-undef': 'off'
    }
  }
]
