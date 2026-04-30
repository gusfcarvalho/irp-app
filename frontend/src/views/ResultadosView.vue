<template>
  <div class="space-y-6">
    <!-- Header + date range -->
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Resultados</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Posições fechadas no período — inclui carrego de posições abertas antes da data inicial.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <label class="text-sm font-medium text-muted-foreground whitespace-nowrap">De</label>
        <input
          v-model="fromDate"
          type="date"
          class="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          @change="load"
        />
        <label class="text-sm font-medium text-muted-foreground whitespace-nowrap">Até</label>
        <input
          v-model="toDate"
          type="date"
          class="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          @change="load"
        />
        <button
          type="button"
          class="h-9 px-3 rounded-md border border-input text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="Ano atual"
          @click="setCurrentYear"
        >
          {{ currentYear }}
        </button>
      </div>
    </div>

    <Alert v-if="error" variant="destructive">
      <AlertTriangle class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ error }}</span>
    </Alert>

    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
    </div>

    <template v-else>
      <!-- Summary cards -->
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <Card class="px-4 py-3 col-span-2 sm:col-span-1">
          <p class="text-xs text-muted-foreground">Resultado total</p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="summary.totalPnl > 0 ? 'text-emerald-600' : summary.totalPnl < 0 ? 'text-red-500' : ''"
          >
            {{ summary.totalPnl >= 0 ? '+' : '' }}{{ formatCurrency(summary.totalPnl) }}
          </p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Posições fechadas</p>
          <p class="text-xl font-bold mt-0.5">{{ summary.total }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Ganhadoras</p>
          <p class="text-xl font-bold mt-0.5 text-emerald-600">{{ summary.winners }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Perdedoras</p>
          <p class="text-xl font-bold mt-0.5 text-red-500">{{ summary.losers }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Taxa de acerto</p>
          <p class="text-xl font-bold mt-0.5">
            {{ summary.total ? (summary.winners / summary.total * 100).toFixed(0) + '%' : '—' }}
          </p>
        </Card>
      </div>

      <!-- Empty state -->
      <div v-if="!positions.length" class="flex flex-col items-center gap-3 py-16 text-muted-foreground">
        <InboxIcon class="h-10 w-10 opacity-25" />
        <p class="text-sm">Nenhuma posição fechada no período selecionado.</p>
      </div>

      <!-- Results table -->
      <Card v-else class="overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-muted/40 border-b">
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">Ticker</th>
                <th class="px-4 py-3 text-center font-medium text-muted-foreground">Dir.</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Abertura</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Fechamento</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Qtd</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">PM abertura</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">PM fechamento</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Resultado</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Var %</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(pos, i) in positions"
                :key="i"
                class="border-b last:border-0 hover:bg-muted/20 transition-colors"
                :class="Number(pos.realized_pnl) > 0 ? 'hover:bg-emerald-50/20' : Number(pos.realized_pnl) < 0 ? 'hover:bg-red-50/20' : ''"
              >
                <td class="px-4 py-3 font-semibold font-mono">{{ pos.ticker }}</td>
                <td class="px-4 py-3 text-center">
                  <Badge :variant="pos.direction === 'LONG' ? 'default' : 'outline'" class="text-xs">
                    {{ pos.direction === 'LONG' ? 'Long' : 'Short' }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right tabular-nums text-muted-foreground">
                  {{ pos.open_date ? formatDate(pos.open_date) : '—' }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums text-muted-foreground">
                  {{ formatDate(pos.close_date) }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ pos.quantity.toLocaleString('pt-BR') }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ formatCurrency(pos.open_mean_price) }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ formatCurrency(pos.close_price) }}
                </td>
                <td
                  class="px-4 py-3 text-right tabular-nums font-semibold"
                  :class="Number(pos.realized_pnl) > 0 ? 'text-emerald-600' : Number(pos.realized_pnl) < 0 ? 'text-red-500' : ''"
                >
                  {{ Number(pos.realized_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(pos.realized_pnl) }}
                </td>
                <td
                  class="px-4 py-3 text-right tabular-nums"
                  :class="pnlPct(pos) > 0 ? 'text-emerald-600' : pnlPct(pos) < 0 ? 'text-red-500' : 'text-muted-foreground'"
                >
                  {{ Number(pos.realized_pnl) >= 0 ? '+' : '' }}{{ pnlPct(pos).toFixed(2) }}%
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-muted/40 border-t font-medium">
                <td colspan="7" class="px-4 py-3 text-right text-muted-foreground text-sm">Total</td>
                <td
                  class="px-4 py-3 text-right tabular-nums font-bold"
                  :class="summary.totalPnl > 0 ? 'text-emerald-600' : summary.totalPnl < 0 ? 'text-red-500' : ''"
                >
                  {{ summary.totalPnl >= 0 ? '+' : '' }}{{ formatCurrency(summary.totalPnl) }}
                </td>
                <td class="px-4 py-3" />
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { AlertTriangle, Inbox as InboxIcon, Loader2 } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const positions = ref([])
const loading = ref(false)
const error = ref('')

const currentYear = new Date().getFullYear()

const fromDate = ref(`${currentYear}-01-01`)
const toDate = ref(`${currentYear}-12-31`)

const setCurrentYear = () => {
  fromDate.value = `${currentYear}-01-01`
  toDate.value = `${currentYear}-12-31`
  load()
}

const summary = computed(() => {
  const list = positions.value
  return {
    total: list.length,
    winners: list.filter(p => Number(p.realized_pnl) > 0).length,
    losers: list.filter(p => Number(p.realized_pnl) < 0).length,
    totalPnl: list.reduce((sum, p) => sum + Number(p.realized_pnl), 0),
  }
})

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatDate = (iso) => {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const pnlPct = (pos) => {
  const open = Number(pos.open_mean_price)
  if (!open) return 0
  const close = Number(pos.close_price)
  if (pos.direction === 'LONG') return ((close - open) / open) * 100
  return ((open - close) / open) * 100
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams()
    if (fromDate.value) params.set('from_date', fromDate.value)
    if (toDate.value) params.set('to_date', toDate.value)
    const res = await fetch(`/api/closed-positions?${params}`)
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    positions.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
