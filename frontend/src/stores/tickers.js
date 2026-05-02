import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTickerAliases, getTickerClassifications } from '@/services/api.js'

export const useTickerStore = defineStore('tickers', () => {
  const aliases = ref([])
  const classifications = ref({}) // ticker → asset_type

  const loadAliases = async () => {
    aliases.value = await getTickerAliases()
  }

  const loadClassifications = async () => {
    const rows = await getTickerClassifications()
    classifications.value = Object.fromEntries(rows.map(r => [r.ticker, r.asset_type]))
  }

  const load = () => Promise.all([loadAliases(), loadClassifications()])

  const pendingAliases = () => aliases.value.filter(a => !a.confirmed)

  return { aliases, classifications, load, loadAliases, loadClassifications, pendingAliases }
})
