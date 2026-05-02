import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getPositions } from '@/services/api.js'

export const usePositionStore = defineStore('positions', () => {
  const positions = ref([])
  const asOf = ref(new Date().toISOString().slice(0, 10))
  const loading = ref(false)
  const error = ref('')

  const load = async () => {
    loading.value = true
    error.value = ''
    try {
      positions.value = await getPositions(asOf.value)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { positions, asOf, loading, error, load }
})
