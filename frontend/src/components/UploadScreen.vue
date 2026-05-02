<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Importar Nota de Corretagem</h1>
      <p class="text-muted-foreground text-sm mt-1">
        Faça upload de um ou mais PDFs SINACOR (BTG, Clear, XP e outras) para importar suas transações.
      </p>
    </div>

    <Card class="p-6 space-y-4">
      <!-- Drop zone -->
      <div
        class="relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer"
        :class="isDragging
          ? 'border-primary bg-primary/5'
          : queue.length
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
          accept="application/pdf,.pdf"
          multiple
          class="hidden"
          @change="onSelectFiles"
        >
        <div class="flex h-12 w-12 items-center justify-center rounded-full" :class="queue.length ? 'bg-emerald-100' : 'bg-muted'">
          <CheckCircle v-if="queue.length" class="h-6 w-6 text-emerald-600" />
          <UploadCloud v-else class="h-6 w-6 text-muted-foreground" />
        </div>
        <div class="text-center">
          <p class="text-sm font-medium">
            {{ queue.length ? `${queue.length} arquivo${queue.length > 1 ? 's' : ''} selecionado${queue.length > 1 ? 's' : ''}` : 'Arraste PDFs aqui ou clique para selecionar' }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">Múltiplos arquivos .pdf permitidos</p>
        </div>
      </div>

      <!-- File queue -->
      <ul v-if="queue.length" class="space-y-1.5">
        <li
          v-for="item in queue"
          :key="item.name"
          class="flex items-center gap-3 rounded-md border px-3 py-2 text-sm"
          :class="{
            'border-emerald-300 bg-emerald-50/50': item.status === 'done',
            'border-red-300 bg-red-50/50': item.status === 'error' || item.status === 'duplicate',
            'border-primary/40 bg-primary/5': item.status === 'uploading',
            'border-border': item.status === 'pending',
          }"
        >
          <Loader2 v-if="item.status === 'uploading'" class="h-4 w-4 animate-spin text-primary shrink-0" />
          <CheckCircle v-else-if="item.status === 'done'" class="h-4 w-4 text-emerald-600 shrink-0" />
          <AlertTriangle v-else-if="item.status === 'error'" class="h-4 w-4 text-red-500 shrink-0" />
          <CopyX v-else-if="item.status === 'duplicate'" class="h-4 w-4 text-amber-500 shrink-0" />
          <FileText v-else class="h-4 w-4 text-muted-foreground shrink-0" />

          <span class="flex-1 font-mono text-xs truncate">{{ item.name }}</span>
          <span class="text-xs text-muted-foreground shrink-0">{{ (item.size / 1024).toFixed(0) }} KB</span>

          <span v-if="item.status === 'done'" class="text-xs text-emerald-700 shrink-0">
            {{ item.txCount }} transaç{{ item.txCount !== 1 ? 'ões' : 'ão' }}
          </span>
          <span v-else-if="item.status === 'duplicate'" class="text-xs text-amber-700 shrink-0">
            duplicada
          </span>
          <span v-else-if="item.status === 'error'" class="text-xs text-red-600 shrink-0 max-w-48 text-right truncate" :title="item.error">
            {{ item.error }}
          </span>

          <button
            v-if="item.status === 'pending'"
            type="button"
            class="p-0.5 rounded text-muted-foreground hover:text-destructive transition-colors shrink-0"
            @click.stop="removeItem(item.name)"
          >
            <X class="h-3.5 w-3.5" />
          </button>
        </li>
      </ul>

      <!-- Optional PDF password (for encrypted notes, e.g. Clear via e-mail) -->
      <div class="border-t pt-3">
        <button
          type="button"
          class="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          @click="showPassword = !showPassword"
        >
          <Lock class="h-3 w-3" />
          PDF protegido por senha?
          <span class="opacity-50">{{ showPassword ? '▲' : '▼' }}</span>
        </button>
        <div v-if="showPassword" class="mt-2 flex items-center gap-2">
          <input
            v-model="pdfPassword"
            type="password"
            placeholder="Senha (ex: CPF sem pontuação)"
            class="h-9 flex-1 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            autocomplete="off"
          />
          <button
            v-if="pdfPassword"
            type="button"
            class="text-xs text-muted-foreground hover:text-foreground"
            @click="pdfPassword = ''"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3">
        <button
          v-if="queue.length"
          type="button"
          class="text-sm text-muted-foreground hover:text-foreground transition-colors"
          @click="clearQueue"
        >
          Limpar tudo
        </button>
        <div class="flex-1" />
        <Button
          type="button"
          :disabled="uploading || !pendingCount"
          class="gap-2 min-w-36"
          @click="uploadAll"
        >
          <Loader2 v-if="uploading" class="h-4 w-4 animate-spin" />
          <Upload v-else class="h-4 w-4" />
          {{ uploading ? `Importando ${uploadingIndex + 1}/${pendingCount + uploadingIndex}…` : `Importar${pendingCount > 1 ? ' ' + pendingCount + ' PDFs' : ' PDF'}` }}
        </Button>
      </div>
    </Card>

    <!-- Summary alert after batch completes -->
    <Alert v-if="batchSummary" :variant="batchSummary.variant" class="animate-in fade-in">
      <CheckCircle v-if="batchSummary.variant === 'success'" class="h-4 w-4 shrink-0 mt-0.5" />
      <AlertTriangle v-else class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ batchSummary.message }}</span>
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

    <!-- Transactions table -->
    <Card class="overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b">
        <div class="flex items-center gap-2">
          <BarChart2 class="h-4 w-4 text-muted-foreground" />
          <span class="font-semibold text-sm">Transações Importadas</span>
          <Badge v-if="transactions.length > 0" variant="secondary">{{ transactions.length }}</Badge>
        </div>
        <button
          class="text-muted-foreground hover:text-foreground transition-colors"
          title="Atualizar"
          type="button"
          @click="loadTransactions"
        >
          <RefreshCw class="h-4 w-4" :class="loadingTx ? 'animate-spin' : ''" />
        </button>
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
            <tr v-if="transactions.length === 0">
              <td colspan="6" class="px-4 py-12 text-center text-muted-foreground">
                <div class="flex flex-col items-center gap-2">
                  <InboxIcon class="h-8 w-8 opacity-30" />
                  <span>Nenhuma transação importada.</span>
                </div>
              </td>
            </tr>
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
              <td class="px-4 py-3 text-right tabular-nums">{{ tx.quantity.toLocaleString('pt-BR') }}</td>
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
import { computed, onMounted, ref } from 'vue'
import {
  AlertTriangle,
  BarChart2,
  CheckCircle,
  CopyX,
  FileText,
  Loader2,
  Lock,
  RefreshCw,
  Upload,
  UploadCloud,
  X,
  Inbox as InboxIcon,
} from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import Alert from './ui/Alert.vue'
import Badge from './ui/Badge.vue'
import Button from './ui/Button.vue'
import Card from './ui/Card.vue'

const API_BASE = '/api'

const fileInputRef = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadingIndex = ref(0)
const loadingTx = ref(false)
const transactions = ref([])
const batchSummary = ref(null)
const pdfPassword = ref('')
const showPassword = ref(false)
const hasPendingAliases = ref(false)

// queue item: { name, size, file, status: 'pending'|'uploading'|'done'|'error'|'duplicate', txCount, error }
const queue = ref([])

const pendingCount = computed(() => queue.value.filter(i => i.status === 'pending').length)

const addFiles = (files) => {
  const existing = new Set(queue.value.map(i => i.name))
  for (const f of files) {
    if (!f.name.toLowerCase().endsWith('.pdf')) continue
    if (existing.has(f.name)) continue
    queue.value.push({ name: f.name, size: f.size, file: f, status: 'pending', txCount: 0, error: '' })
    existing.add(f.name)
  }
}

const onSelectFiles = (e) => {
  addFiles(Array.from(e.target.files ?? []))
  e.target.value = ''
}

const onDrop = (e) => {
  isDragging.value = false
  addFiles(Array.from(e.dataTransfer?.files ?? []))
}

const removeItem = (name) => {
  queue.value = queue.value.filter(i => i.name !== name)
}

const clearQueue = () => {
  queue.value = []
  batchSummary.value = null
}

const uploadAll = async () => {
  const pending = queue.value.filter(i => i.status === 'pending')
  if (!pending.length) return

  uploading.value = true
  uploadingIndex.value = 0
  batchSummary.value = null

  let done = 0, dupes = 0, errors = 0, totalTx = 0

  for (const item of pending) {
    item.status = 'uploading'

    try {
      const formData = new FormData()
      formData.append('file', item.file)
      if (pdfPassword.value) formData.append('password', pdfPassword.value)

      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })

      if (res.status === 409) {
        item.status = 'duplicate'
        dupes++
      } else if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        item.error = body.detail || `Erro ${res.status}`
        item.status = 'error'
        errors++
      } else {
        const data = await res.json()
        item.txCount = data.transactions_created
        item.status = 'done'
        done++
        totalTx += data.transactions_created
        if (data.pending_aliases?.length) {
          hasPendingAliases.value = true
        }
      }
    } catch (e) {
      item.error = e.message
      item.status = 'error'
      errors++
    }

    uploadingIndex.value++
  }

  uploading.value = false

  const parts = []
  if (done) parts.push(`${done} importado${done !== 1 ? 's' : ''} (${totalTx} transações)`)
  if (dupes) parts.push(`${dupes} duplicado${dupes !== 1 ? 's' : ''}`)
  if (errors) parts.push(`${errors} erro${errors !== 1 ? 's' : ''}`)
  batchSummary.value = {
    message: parts.join(' · '),
    variant: errors ? 'destructive' : dupes && !done ? 'default' : 'success',
  }

  if (done) await loadTransactions()
}

const formatDate = (d) => {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const loadTransactions = async () => {
  loadingTx.value = true
  try {
    const res = await fetch(`${API_BASE}/transactions`)
    transactions.value = await res.json()
  } finally {
    loadingTx.value = false
  }
}

onMounted(async () => {
  const MAX = 5
  for (let attempt = 1; attempt <= MAX; attempt++) {
    try {
      await loadTransactions()
      return
    } catch {
      if (attempt === MAX) {
        batchSummary.value = { message: 'Backend unavailable — please refresh', variant: 'destructive' }
      } else {
        await new Promise((r) => setTimeout(r, attempt * 1000))
      }
    }
  }
})
</script>
