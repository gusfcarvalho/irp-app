<template>
  <section>
    <h2>Upload Screen</h2>
    <form @submit.prevent="onSubmit">
      <input
        type="file"
        accept="application/pdf,.pdf"
        @change="onSelectFile"
      >
      <button type="submit" :disabled="loading || !file">
        {{ loading ? 'Uploading...' : 'Upload SINACOR PDF' }}
      </button>
    </form>

    <p v-if="message">{{ message }}</p>

    <h3>Imported Transactions</h3>
    <table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%">
      <thead>
        <tr>
          <th>Date</th>
          <th>Ticker</th>
          <th>Side</th>
          <th>Qty</th>
          <th>Price</th>
          <th>Upload ID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="transactions.length === 0">
          <td colspan="6">No transactions found.</td>
        </tr>
        <tr v-for="tx in transactions" v-else :key="tx.id">
          <td>{{ tx.trade_date }}</td>
          <td>{{ tx.ticker }}</td>
          <td>{{ tx.side }}</td>
          <td>{{ tx.quantity }}</td>
          <td>{{ tx.price }}</td>
          <td>{{ tx.upload_id }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const API_BASE = '/api'

const file = ref(null)
const loading = ref(false)
const message = ref('')
const transactions = ref([])

const loadTransactions = async () => {
  const res = await fetch(`${API_BASE}/transactions`)
  const data = await res.json()
  transactions.value = data
}

const onSelectFile = (event) => {
  file.value = event.target.files?.[0] ?? null
}

const onSubmit = async () => {
  if (!file.value) return
  loading.value = true
  message.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file.value)

    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Upload failed')
    }

    const data = await res.json()
    message.value = `Upload successful (ID: ${data.id}). Parsed transactions: ${data.transactions_created}.`
    file.value = null
    await loadTransactions()
  } catch (err) {
    message.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadTransactions()
  } catch {
    message.value = 'Failed to load transactions'
  }
})
</script>
