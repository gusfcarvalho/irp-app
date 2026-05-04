import { ref } from 'vue'

/**
 * Wraps an async function with loading/error state.
 * Returns { loading, error, execute } where execute calls fn and manages state.
 */
export function useLoading(fn) {
  const loading = ref(false)
  const error = ref('')

  const execute = async (...args) => {
    loading.value = true
    error.value = ''
    try {
      return await fn(...args)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { loading, error, execute }
}
