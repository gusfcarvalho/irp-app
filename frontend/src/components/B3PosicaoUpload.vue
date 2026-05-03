<template>
  <div class="space-y-6">
    <p class="text-muted-foreground text-sm">
      Importe o arquivo <strong>posicao.xlsx</strong> exportado do portal B3. As transações serão marcadas como
      pendentes de revisão — o preço de fechamento é usado como proxy e a data deve ser corrigida.
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
            {{ file ? file.name : 'Arraste o arquivo posicao.xlsx aqui ou clique para selecionar' }}
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
          {{ uploading ? 'Importando…' : 'Importar Posição' }}
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

    <!-- Imported transactions -->
    <Card v-if="transactions.length" class="overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <div class="flex items-center gap-2">
          <BarChart2 class="h-4 w-4 text-muted-foreground" />
          <span class="font-semibold text-sm">Transações Importadas</span>
          <Badge variant="secondary">{{ transactions.length }}</Badge>
        </div>
      </div>

      <!-- Review notice + mass date setter -->
      <div v-if="pendingReviewCount" class="px-5 py-3 bg-amber-50 border-b border-amber-200 space-y-2">
        <div class="flex items-start gap-2">
          <AlertTriangle class="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
          <p class="text-xs text-amber-800">
            {{ pendingReviewCount }} transaç{{ pendingReviewCount === 1 ? 'ão pendente' : 'ões pendentes' }} de revisão.
            O preço de fechamento foi usado como proxy e a data de aquisição deve ser corrigida.
          </p>
        </div>
        <div class="flex items-center gap-2 pl-6">
          <span class="text-xs text-amber-800 shrink-0">Aplicar data a todas:</span>
          <input
            v-model="bulkDate"
            type="date"
            class="h-7 rounded-md border border-amber-300 bg-white px-2 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400"
          />
          <button
            type="button"
            :disabled="!bulkDate || bulkSaving"
            class="px-3 py-1 rounded text-xs font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 transition-colors flex items-center gap-1"
            @click="applyBulkDate"
          >
            <Loader2 v-if="bulkSaving" class="h-3 w-3 animate-spin" />
            Aplicar a todas
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/40">
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Ticker</th>
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Data Aquisição</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Qtd</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Preço Unit.</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Total</th>
              <th class="px-4 py-3 text-center font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tx in transactions"
              :key="tx.id"
              class="border-b last:border-0 transition-colors"
              :class="editingId === tx.id ? 'bg-amber-50' : tx.needs_review ? 'bg-amber-50/30 hover:bg-amber-50/60' : 'hover:bg-muted/30'"
            >
              <td class="px-4 py-3 font-semibold font-mono">{{ tx.ticker }}</td>

              <!-- Date cell -->
              <td class="px-4 py-3">
                <input
                  v-if="editingId === tx.id"
                  v-model="draft.trade_date"
                  type="date"
                  class="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring w-36"
                />
                <span v-else class="tabular-nums text-muted-foreground">{{ tx.trade_date }}</span>
              </td>

              <td class="px-4 py-3 text-right tabular-nums">{{ formatQty(tx.quantity) }}</td>

              <!-- Price cell -->
              <td class="px-4 py-3 text-right">
                <input
                  v-if="editingId === tx.id"
                  v-model="draft.price"
                  type="number"
                  step="0.01"
                  min="0"
                  class="h-8 rounded-md border border-input bg-background px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring w-28"
                />
                <span v-else class="tabular-nums">{{ formatCurrency(tx.price) }}</span>
              </td>

              <td class="px-4 py-3 text-right tabular-nums font-medium">
                {{ formatCurrency(Number(editingId === tx.id ? draft.price : tx.price) * tx.quantity) }}
              </td>

              <!-- Status / actions cell -->
              <td class="px-4 py-3 text-center">
                <template v-if="editingId === tx.id">
                  <div class="flex items-center justify-center gap-1">
                    <button
                      type="button"
                      :disabled="saving"
                      class="px-2 py-1 rounded text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
                      @click="saveReview(tx)"
                    >
                      <Loader2 v-if="saving" class="h-3 w-3 animate-spin inline" />
                      <span v-else>Salvar</span>
                    </button>
                    <button
                      type="button"
                      class="px-2 py-1 rounded text-xs text-muted-foreground hover:text-foreground transition-colors"
                      @click="editingId = null"
                    >
                      Cancelar
                    </button>
                  </div>
                </template>
                <template v-else-if="tx.needs_review">
                  <button
                    type="button"
                    class="px-2 py-1 rounded text-xs font-medium text-amber-700 border border-amber-300 bg-amber-50 hover:bg-amber-100 transition-colors"
                    @click="startEdit(tx)"
                  >
                    Revisar
                  </button>
                </template>
                <template v-else>
                  <span class="text-xs text-emerald-600 font-medium">✓ Revisado</span>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatCurrency, formatQty } from '@/utils/format.js'
import { AlertTriangle, BarChart2, CheckCircle, FileSpreadsheet, Loader2, Upload } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import Alert from './ui/Alert.vue'
import Button from './ui/Button.vue'
import Card from './ui/Card.vue'

const fileInputRef = ref(null)
const isDragging = ref(false)
const file = ref(null)
const uploading = ref(false)
const result = ref(null)
const hasPendingAliases = ref(false)
const transactions = ref([])
const editingId = ref(null)
const draft = ref({ trade_date: '', price: '' })
const saving = ref(false)
const bulkDate = ref('')
const bulkSaving = ref(false)

const pendingReviewCount = computed(() => transactions.value.filter(t => t.needs_review).length)

const startEdit = (tx) => {
  editingId.value = tx.id
  draft.value = { trade_date: tx.trade_date, price: String(tx.price) }
}

const applyBulkDate = async () => {
  if (!bulkDate.value) return
  bulkSaving.value = true
  const pending = transactions.value.filter(t => t.needs_review)
  try {
    await Promise.all(pending.map(async (tx) => {
      const res = await fetch(`/api/transactions/${tx.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trade_date: bulkDate.value, needs_review: false }),
      })
      if (res.ok) {
        const updated = await res.json()
        const idx = transactions.value.findIndex(t => t.id === tx.id)
        if (idx !== -1) transactions.value[idx] = updated
      }
    }))
    editingId.value = null
    bulkDate.value = ''
  } catch (e) {
    result.value = { variant: 'destructive', message: e.message }
  } finally {
    bulkSaving.value = false
  }
}

const saveReview = async (tx) => {
  saving.value = true
  try {
    const res = await fetch(`/api/transactions/${tx.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trade_date: draft.value.trade_date || null,
        price: draft.value.price ? Number(draft.value.price) : null,
        needs_review: false,
      }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      result.value = { variant: 'destructive', message: body.detail || `Erro ${res.status}` }
      return
    }
    const updated = await res.json()
    const idx = transactions.value.findIndex(t => t.id === tx.id)
    if (idx !== -1) transactions.value[idx] = updated
    editingId.value = null
  } catch (e) {
    result.value = { variant: 'destructive', message: e.message }
  } finally {
    saving.value = false
  }
}

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
    const res = await fetch('/api/b3/posicao', { method: 'POST', body: formData })

    if (res.status === 409) {
      result.value = { variant: 'default', message: 'Este arquivo já foi importado anteriormente.' }
    } else if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      result.value = { variant: 'destructive', message: body.detail || `Erro ${res.status}` }
    } else {
      const data = await res.json()
      result.value = {
        variant: 'success',
        message: `${data.transactions_created} posição${data.transactions_created !== 1 ? 'ões importadas' : ' importada'} com sucesso. Revise as transações antes de calcular.`,
      }
      if (data.pending_aliases?.length) hasPendingAliases.value = true
      if (data.errors?.length) {
        result.value.message += ` (${data.errors.length} aviso${data.errors.length !== 1 ? 's' : ''}: ${data.errors.join('; ')})`
      }
      // Load the just-imported transactions for preview
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
