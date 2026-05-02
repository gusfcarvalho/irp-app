<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Imposto de Renda</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Apuração mensal de IRPF sobre renda variável — Ações, BDRs e FIIs.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <label class="text-sm font-medium text-muted-foreground whitespace-nowrap">Mês</label>
        <select
          v-model="selectedMonth"
          class="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
        <select
          v-model="selectedYear"
          class="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <button
          type="button"
          class="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          :disabled="loading"
          @click="load"
        >
          Calcular
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

    <template v-else-if="report">
      <!-- Divergence alert -->
      <Alert v-if="report.payment_diverges" variant="destructive">
        <AlertTriangle class="h-4 w-4 shrink-0 mt-0.5" />
        <span>
          Valor pago <strong>{{ formatCurrency(report.amount_paid) }}</strong> difere do calculado
          <strong>{{ formatCurrency(report.total_tax_due) }}</strong> para este mês.
        </span>
      </Alert>

      <!-- Payment status bar -->
      <div class="flex items-center gap-3 rounded-md border px-4 py-2.5 bg-muted/30 text-sm">
        <template v-if="report.amount_paid != null">
          <CheckCircle2 class="h-4 w-4 text-emerald-600 shrink-0" />
          <span class="text-muted-foreground">Pago em {{ currentMonthLabel }}:</span>
          <span class="font-semibold">{{ formatCurrency(report.amount_paid) }}</span>
          <button
            type="button"
            class="ml-auto text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
            @click="openPaymentModal(report.amount_paid, '')"
          >Editar</button>
          <button
            type="button"
            class="text-xs text-red-500 hover:text-red-600 underline-offset-2 hover:underline"
            @click="deletePayment"
          >Remover</button>
        </template>
        <template v-else>
          <CreditCard class="h-4 w-4 text-muted-foreground shrink-0" />
          <span class="text-muted-foreground">Nenhum pagamento registrado para {{ currentMonthLabel }}.</span>
          <button
            type="button"
            class="ml-auto h-7 px-3 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors"
            @click="openPaymentModal(report.total_tax_due, '')"
          >Marcar como pago</button>
        </template>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card class="px-4 py-3 col-span-2 sm:col-span-1">
          <p class="text-xs text-muted-foreground">Total a pagar</p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="Number(report.total_tax_due) > 0 ? 'text-red-500' : 'text-emerald-600'"
          >
            {{ formatCurrency(report.total_tax_due) }}
          </p>
        </Card>

        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground flex items-center gap-1">
            Ações
            <Badge v-if="report.stocks.exempt" variant="outline" class="text-[10px] px-1 py-0">Isento</Badge>
          </p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="Number(report.stocks.tax_due) > 0 ? 'text-red-500' : 'text-muted-foreground'"
          >
            {{ formatCurrency(report.stocks.tax_due) }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">
            vendas {{ formatCurrency(report.stocks.total_sold_value) }}
          </p>
        </Card>

        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">BDRs</p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="Number(report.bdr.tax_due) > 0 ? 'text-red-500' : 'text-muted-foreground'"
          >
            {{ formatCurrency(report.bdr.tax_due) }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">
            vendas {{ formatCurrency(report.bdr.total_sold_value) }}
          </p>
        </Card>

        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">FIIs</p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="Number(report.fii.tax_due) > 0 ? 'text-red-500' : 'text-muted-foreground'"
          >
            {{ formatCurrency(report.fii.tax_due) }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">
            vendas {{ formatCurrency(report.fii.total_sold_value) }}
          </p>
        </Card>
      </div>

      <!-- Per-asset sections -->
      <div class="space-y-4">
        <AssetSection
          v-for="section in sections"
          :key="section.key"
          :data="section.data"
          :title="section.title"
          @pm-click="openBreakdown"
        />
      </div>
    </template>

    <!-- Initial empty state -->
    <div v-else class="flex flex-col items-center gap-3 py-16 text-muted-foreground">
      <Calculator class="h-10 w-10 opacity-25" />
      <p class="text-sm">Selecione o mês e clique em Calcular.</p>
    </div>

    <!-- Payment modal -->
    <Transition name="fade">
      <div v-if="paymentModalOpen" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50" @click="paymentModalOpen = false" />
        <div class="relative z-10 w-full max-w-sm bg-background rounded-lg border shadow-xl p-6 space-y-4">
          <h2 class="font-semibold text-base">Registrar pagamento</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-muted-foreground mb-1">Valor pago (R$)</label>
              <input
                v-model="paymentAmount"
                type="number"
                step="0.01"
                min="0"
                class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-muted-foreground mb-1">Observações (opcional)</label>
              <input
                v-model="paymentNotes"
                type="text"
                class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          </div>
          <Alert v-if="paymentError" variant="destructive" class="text-xs py-2">
            <AlertTriangle class="h-3.5 w-3.5 shrink-0" />
            <span>{{ paymentError }}</span>
          </Alert>
          <div class="flex gap-2 justify-end">
            <button
              type="button"
              class="h-8 px-4 rounded-md border text-sm hover:bg-muted transition-colors"
              @click="paymentModalOpen = false"
            >Cancelar</button>
            <button
              type="button"
              class="h-8 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              :disabled="paymentSaving"
              @click="savePayment"
            >{{ paymentSaving ? 'Salvando…' : 'Salvar' }}</button>
          </div>
        </div>
      </div>
    </Transition>

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
import { computed, ref } from 'vue'
import { AlertTriangle, Calculator, CheckCircle2, CreditCard, Loader2, X } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import AssetSection from '@/components/AssetSection.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const now = new Date()
const selectedMonth = ref(String(now.getMonth() + 1).padStart(2, '0'))
const selectedYear = ref(now.getFullYear())

const months = [
  { value: '01', label: 'Janeiro' },
  { value: '02', label: 'Fevereiro' },
  { value: '03', label: 'Março' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Maio' },
  { value: '06', label: 'Junho' },
  { value: '07', label: 'Julho' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Setembro' },
  { value: '10', label: 'Outubro' },
  { value: '11', label: 'Novembro' },
  { value: '12', label: 'Dezembro' },
]

const currentYear = now.getFullYear()
const years = Array.from({ length: 6 }, (_, i) => currentYear - 5 + i).reverse()

const report = ref(null)
const loading = ref(false)
const error = ref('')

const sections = computed(() => {
  if (!report.value) return []
  return [
    { key: 'stocks', title: 'Ações', data: report.value.stocks },
    { key: 'bdr', title: 'BDRs', data: report.value.bdr },
    { key: 'fii', title: 'FIIs', data: report.value.fii },
  ].filter(s => s.data.closed_positions.length > 0 || Number(s.data.total_sold_value) > 0)
})

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatDate = (iso) => {
  if (!iso) return '—'
  const [y, m, d] = iso.split('T')[0].split('-')
  return `${d}/${m}/${y}`
}

// ── PM breakdown drawer ───────────────────────────────────────────────────────
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

const openBreakdown = async ({ ticker, asOf }) => {
  breakdownTicker.value = ticker
  breakdownAsOf.value = asOf
  breakdownSteps.value = []
  breakdownLoading.value = true
  try {
    const url = `/api/positions/${ticker}/breakdown` + (asOf ? `?as_of=${asOf}` : '')
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

// ── Tax payment modal ─────────────────────────────────────────────────────────
const paymentModalOpen = ref(false)
const paymentAmount = ref('')
const paymentNotes = ref('')
const paymentSaving = ref(false)
const paymentError = ref('')

const currentMonthLabel = computed(() => {
  const m = months.find(x => x.value === selectedMonth.value)
  return m ? `${m.label} ${selectedYear.value}` : ''
})

const openPaymentModal = (defaultAmount, defaultNotes) => {
  paymentAmount.value = defaultAmount != null ? Number(defaultAmount).toFixed(2) : ''
  paymentNotes.value = defaultNotes || ''
  paymentError.value = ''
  paymentModalOpen.value = true
}

const savePayment = async () => {
  paymentError.value = ''
  const amount = parseFloat(paymentAmount.value)
  if (isNaN(amount) || amount < 0) {
    paymentError.value = 'Informe um valor válido.'
    return
  }
  paymentSaving.value = true
  try {
    const month = `${selectedYear.value}-${selectedMonth.value}`
    const res = await fetch(`/api/tax-payments/${month}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_paid: amount, notes: paymentNotes.value || null }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Erro ${res.status}`)
    }
    paymentModalOpen.value = false
    await load()
  } catch (e) {
    paymentError.value = e.message
  } finally {
    paymentSaving.value = false
  }
}

const deletePayment = async () => {
  if (!confirm('Remover registro de pagamento?')) return
  try {
    const month = `${selectedYear.value}-${selectedMonth.value}`
    const res = await fetch(`/api/tax-payments/${month}`, { method: 'DELETE' })
    if (!res.ok && res.status !== 404) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Erro ${res.status}`)
    }
    await load()
  } catch (e) {
    error.value = e.message
  }
}

const load = async () => {
  loading.value = true
  error.value = ''
  report.value = null
  try {
    const month = `${selectedYear.value}-${selectedMonth.value}`
    const res = await fetch(`/api/tax?month=${month}`)
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Erro ${res.status}`)
    }
    report.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

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
