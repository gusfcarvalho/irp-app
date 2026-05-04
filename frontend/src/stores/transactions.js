import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTransactions } from '@/services/api.js'

export const useTransactionStore = defineStore('transactions', () => {
  const transactions = ref([])
  const loading = ref(false)

  const load = async () => {
    loading.value = true
    try {
      transactions.value = await getTransactions()
    } finally {
      loading.value = false
    }
  }

  return { transactions, loading, load }
})
