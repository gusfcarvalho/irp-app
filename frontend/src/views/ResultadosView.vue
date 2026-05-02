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
                  <button
                    type="button"
                    class="tabular-nums text-muted-foreground underline decoration-dotted hover:text-foreground transition-colors"
                    title="Ver detalhamento do cálculo do PM"
                    @click="openBreakdown(pos, pos.open_date)"
                  >
                    {{ formatCurrency(pos.open_mean_price) }}
                  </button>
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  <button
                    type="button"
                    class="tabular-nums text-muted-foreground underline decoration-dotted hover:text-foreground transition-colors"
                    title="Ver detalhamento do PM de fechamento"
                    @click="openBreakdown(pos, pos.close_date)"
                  >
                    {{ formatCurrency(pos.close_price) }}
                  </button>
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

    <!-- PM breakdown drawer -->
    <Transition name="drawer">
      <div v-if="breakdownTicker" class="fixed inset-0 z-50 flex">
        <div class="flex-1 bg-black/40" @click="breakdownTicker = null" />
        <div class="w-full max-w-2xl bg-background border-l shadow-xl flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b shrink-0">
            <div>
              <h2 class="font-semibold text-base">
                Detalhamento — <span class="font-mono">{{ breakdownTicker }}</span>
              </h2>
              <p class="text-xs text-muted-foreground mt-0.5">
                Custo médio ajustado por taxas até {{ formatDate(breakdownAsOf) }}
              </p>
            </div>
            <button type="button" class="p-1.5 rounded hover:bg-muted" @click="breakdownTicker = null">
              <X class="h-4 w-4" />
            </button>
          </div>

          <div v-if="breakdownLoading" class="flex justify-center py-10">
            <Loader2 class="h-5 w-5 animate-spin text-muted-foreground" />
          </div>

          <div v-else class="overflow-auto flex-1">
            <table class="w-full text-xs">
              <thead class="sticky top-0 bg-muted/60 backdrop-blur">
                <tr class="border-b">
                  <th class="px-4 py-2.5 text-left font-medium text-muted-foreground">Data</th>
                  <th class="px-4 py-2.5 text-center font-medium text-muted-foreground">Op</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Qtd</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Preço bruto</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Taxa/un.</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Preço ajustado</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Qtd acum.</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">PM após</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="(step, i) in breakdownSteps" :key="i">
                  <tr class="border-b" :class="stepRowClass(step.side)">
                    <td class="px-4 py-2 tabular-nums text-muted-foreground">{{ formatDate(step.trade_date) }}</td>
                    <td class="px-4 py-2 text-center">
                      <Badge :variant="stepBadgeVariant(step.side)" class="text-xs px-1.5">
                        {{ stepLabel(step.side) }}
                      </Badge>
                    </td>
                    <template v-if="isCorporateAction(step.side)">
                      <td class="px-4 py-2 text-center tabular-nums text-muted-foreground" colspan="4">
                        Proporção {{ step.raw_price }}:{{ step.quantity }}
                      </td>
                    </template>
                    <template v-else>
                      <td class="px-4 py-2 text-right tabular-nums">{{ step.quantity.toLocaleString('pt-BR') }}</td>
                      <td class="px-4 py-2 text-right tabular-nums">{{ formatCurrency(step.raw_price) }}</td>
                      <td class="px-4 py-2 text-right tabular-nums" :class="Number(step.fee_per_unit) > 0 ? 'text-amber-600' : 'text-muted-foreground'">
                        {{ Number(step.fee_per_unit) > 0 ? (step.side === 'BUY' ? '+' : '−') : '' }}{{ formatCurrency(step.fee_per_unit) }}
                      </td>
                      <td class="px-4 py-2 text-right tabular-nums font-medium">{{ formatCurrency(step.adjusted_price) }}</td>
                    </template>
                    <td class="px-4 py-2 text-right tabular-nums">{{ step.qty_after.toLocaleString('pt-BR') }}</td>
                    <td class="px-4 py-2 text-right tabular-nums font-semibold" :class="i === breakdownSteps.length - 1 ? 'text-primary' : ''">
                      {{ formatCurrency(step.mean_price_after) }}
                    </td>
                  </tr>
                  <tr v-if="step.closes_quantity != null" class="bg-muted/30 border-b border-dashed">
                    <td colspan="8" class="px-4 py-1.5">
                      <div class="flex items-center gap-3 text-xs">
                        <span class="font-medium text-muted-foreground">Posição fechada —</span>
                        <span class="text-muted-foreground">{{ step.closes_quantity.toLocaleString('pt-BR') }} ações</span>
                        <span class="font-semibold" :class="Number(step.realized_pnl) >= 0 ? 'text-emerald-600' : 'text-red-500'">
                          {{ Number(step.realized_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(step.realized_pnl) }}
                        </span>
                        <span v-if="step.qty_after !== 0" class="text-muted-foreground italic">
                          {{ Math.abs(step.qty_after).toLocaleString('pt-BR') }} restantes abertos {{ step.qty_after > 0 ? 'long' : 'short' }}
                        </span>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <div class="border-t px-6 py-3 shrink-0 bg-muted/20 flex items-center justify-between text-xs text-muted-foreground">
            <span>{{ breakdownSteps.length }} operação{{ breakdownSteps.length !== 1 ? 'ões' : '' }}</span>
            <span v-if="totalRealizedPnl !== null">
              P&amp;L realizado:
              <strong class="text-sm ml-1" :class="totalRealizedPnl >= 0 ? 'text-emerald-600' : 'text-red-500'">
                {{ totalRealizedPnl >= 0 ? '+' : '' }}{{ formatCurrency(totalRealizedPnl) }}
              </strong>
            </span>
            <span>
              PM na data:
              <strong class="text-foreground text-sm ml-1">
                {{ breakdownSteps.length ? formatCurrency(breakdownSteps.at(-1).mean_price_after) : '—' }}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { AlertTriangle, Inbox as InboxIcon, Loader2, X } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const positions = ref([])
const loading = ref(false)
const error = ref('')

const breakdownTicker = ref(null)
const breakdownAsOf = ref(null)
const breakdownSteps = ref([])
const breakdownLoading = ref(false)

const totalRealizedPnl = computed(() => {
  const closingSteps = breakdownSteps.value.filter(s => s.realized_pnl != null)
  if (!closingSteps.length) return null
  return closingSteps.reduce((sum, s) => sum + Number(s.realized_pnl), 0)
})

const CORPORATE_ACTION_SIDES = new Set(['GROUPING', 'SPLITTING'])
const isCorporateAction = (side) => CORPORATE_ACTION_SIDES.has(side)

const stepRowClass = (side) => {
  if (side === 'BUY' || side === 'BONUS') return 'hover:bg-blue-50/30'
  if (side === 'SELL') return 'hover:bg-red-50/30'
  return 'hover:bg-purple-50/30'
}
const stepBadgeVariant = (side) => {
  if (side === 'BUY' || side === 'BONUS') return 'default'
  if (side === 'SELL') return 'destructive'
  return 'outline'
}
const stepLabel = (side) => {
  switch (side) {
    case 'BUY': return 'C'
    case 'SELL': return 'V'
    case 'BONUS': return 'Bônus'
    case 'GROUPING': return 'Grup.'
    case 'SPLITTING': return 'Desdo.'
    default: return side
  }
}

const openBreakdown = async (pos, asOf) => {
  breakdownTicker.value = pos.ticker
  breakdownAsOf.value = asOf
  breakdownSteps.value = []
  breakdownLoading.value = true
  try {
    const url = `/api/positions/${pos.ticker}/breakdown` + (asOf ? `?as_of=${asOf}` : '')
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    breakdownSteps.value = await res.json()
  } catch (e) {
    error.value = e.message
    breakdownTicker.value = null
  } finally {
    breakdownLoading.value = false
  }
}

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

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
