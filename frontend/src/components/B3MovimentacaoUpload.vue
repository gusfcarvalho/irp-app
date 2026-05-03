<template>
  <div class="space-y-6">
    <p class="text-muted-foreground text-sm">
      Importe o arquivo <strong>movimentacao.xlsx</strong> exportado do portal B3. Apenas os tipos de movimentação
      relevantes (resgates, aplicações, compras e vendas) serão importados.
    </p>

    <Card class="p-6 space-y-4">
      <!-- Drop zone -->
      <div
        class="relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer"
        :class="isDragging
          ? 'border-primary bg-primary/5'
          : file
            ? 'border-emerald-400/60 bg-emerald-50/30'
            : 'border-border hover:border-primary/50 hover:bg-muted/40'"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
        @click="fileInputRef?.click()"
      >
        <input
          ref="fileInputRef"
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          class="hidden"
          @change="onSelectFile"
        >
        <div class="flex h-12 w-12 items-center justify-center rounded-full" :class="file ? 'bg-emerald-100' : 'bg-muted'">
          <CheckCircle v-if="file" class="h-6 w-6 text-emerald-600" />
          <FileSpreadsheet v-else class="h-6 w-6 text-muted-foreground" />
        </div>
        <div class="text-center">
          <p class="text-sm font-medium">
            {{ file ? file.name : 'Arraste o arquivo movimentacao.xlsx aqui ou clique para selecionar' }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">Arquivo .xlsx da B3</p>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3">
        <button
          v-if="file"
          type="button"
          class="text-sm text-muted-foreground hover:text-foreground transition-colors"
          @click="clearFile"
        >
          Limpar
        </button>
        <div class="flex-1" />
        <Button
          type="button"
          :disabled="uploading || !file"
          class="gap-2 min-w-36"
          @click="uploadFile"
        >
          <Loader2 v-if="uploading" class="h-4 w-4 animate-spin" />
          <Upload v-else class="h-4 w-4" />
          {{ uploading ? 'Importando…' : 'Importar Movimentações' }}
        </Button>
      </div>
    </Card>

    <!-- Result alert -->
    <Alert v-if="result" :variant="result.variant" class="animate-in fade-in">
      <CheckCircle v-if="result.variant === 'success'" class="h-4 w-4 shrink-0 mt-0.5" />
      <AlertTriangle v-else class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ result.message }}</span>
    </Alert>

    <!-- Pending alias alert -->
    <Alert v-if="hasPendingAliases" variant="default" class="animate-in fade-in border-amber-300 bg-amber-50">
      <AlertTriangle class="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
      <span class="text-amber-800">
        Alguns tickers não foram reconhecidos automaticamente.
        <RouterLink to="/tickers" class="underline font-medium hover:text-amber-900">
          Confirme os tickers aqui →
        </RouterLink>
      </span>
    </Alert>

    <!-- Imported transactions table -->
    <Card v-if="transactions.length" class="overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <div class="flex items-center gap-2">
          <BarChart2 class="h-4 w-4 text-muted-foreground" />
          <span class="font-semibold text-sm">Transações Importadas</span>
          <Badge variant="secondary">{{ transactions.length }}</Badge>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/40">
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Data</th>
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Ticker</th>
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Operação</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Qtd</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Preço Unit.</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tx in transactions"
              :key="tx.id"
              class="border-b last:border-0 hover:bg-muted/30 transition-colors"
            >
              <td class="px-4 py-3 text-muted-foreground tabular-nums">{{ formatDate(tx.trade_date) }}</td>
              <td class="px-4 py-3 font-semibold font-mono">{{ tx.ticker }}</td>
              <td class="px-4 py-3">
                <Badge :variant="tx.side === 'BUY' ? 'default' : 'destructive'" class="uppercase">
                  {{ tx.side === 'BUY' ? 'Compra' : 'Venda' }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">{{ formatQty(tx.quantity) }}</td>
              <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(tx.price) }}</td>
              <td class="px-4 py-3 text-right tabular-nums font-medium">
                {{ formatCurrency(Number(tx.price) * tx.quantity) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { formatCurrency, formatDate, formatQty } from '@/utils/format.js'
import { AlertTriangle, BarChart2, CheckCircle, FileSpreadsheet, Loader2, Upload } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import Alert from './ui/Alert.vue'
import Badge from './ui/Badge.vue'
import Button from './ui/Button.vue'
import Card from './ui/Card.vue'

const fileInputRef = ref(null)
const isDragging = ref(false)
const file = ref(null)
const uploading = ref(false)
const result = ref(null)
const hasPendingAliases = ref(false)
const transactions = ref([])

const onSelectFile = (e) => {
  const f = e.target.files?.[0]
  if (f?.name.toLowerCase().endsWith('.xlsx')) file.value = f
  e.target.value = ''
}

const onDrop = (e) => {
  isDragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f?.name.toLowerCase().endsWith('.xlsx')) file.value = f
}

const clearFile = () => {
  file.value = null
  result.value = null
}

const uploadFile = async () => {
  if (!file.value) return
  uploading.value = true
  result.value = null

  try {
    const formData = new FormData()
    formData.append('file', file.value)
    const res = await fetch('/api/b3/movimentacao', { method: 'POST', body: formData })

    if (res.status === 409) {
      result.value = { variant: 'default', message: 'Este arquivo já foi importado anteriormente.' }
    } else if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      result.value = { variant: 'destructive', message: body.detail || `Erro ${res.status}` }
    } else {
      const data = await res.json()
      let msg = `${data.transactions_created} transaç${data.transactions_created !== 1 ? 'ões importadas' : 'ão importada'} com sucesso.`
      if (data.skipped) msg += ` (${data.skipped} tipo${data.skipped !== 1 ? 's' : ''} de movimentação ignorado${data.skipped !== 1 ? 's' : ''})`
      result.value = { variant: 'success', message: msg }
      if (data.pending_aliases?.length) hasPendingAliases.value = true
      if (data.errors?.length) {
        result.value.message += ` — ${data.errors.length} aviso${data.errors.length !== 1 ? 's' : ''}`
      }
      await loadImportedTransactions(data.id)
    }
  } catch (e) {
    result.value = { variant: 'destructive', message: e.message }
  } finally {
    uploading.value = false
  }
}

const loadImportedTransactions = async (uploadId) => {
  try {
    const res = await fetch('/api/transactions')
    if (!res.ok) return
    const all = await res.json()
    transactions.value = all.filter(t => t.upload_id === uploadId)
  } catch {}
}
</script>
