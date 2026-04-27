import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://backend:8000'
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test-setup.js',
    globals: true,
  },
})
