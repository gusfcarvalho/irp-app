<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Posição</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Custo médio ajustado por taxas de corretagem, do início até a data selecionada.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <label class="text-sm font-medium text-muted-foreground whitespace-nowrap">Data de referência</label>
        <input
          v-model="asOf"
          type="date"
          class="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          @change="load"
        />
        <button
          type="button"
          class="h-9 px-3 rounded-md border border-input text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="Hoje"
          @click="setToday"
        >
          Hoje
        </button>
        <button
          type="button"
          class="h-9 px-3 rounded-md border border-input text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          :disabled="quotesRefreshing || !positions.length"
          :title="quotesDate ? `Cotações de ${formatDate(quotesDate)}` : 'Buscar cotações do Yahoo Finance'"
          @click="doRefreshQuotes"
        >
          <span v-if="quotesRefreshing">Atualizando…</span>
          <span v-else>{{ quotesDate ? `Cotações ${formatDate(quotesDate)}` : 'Atualizar cotações' }}</span>
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

    <div v-else-if="!positions.length" class="flex flex-col items-center gap-3 py-16 text-muted-foreground">
      <InboxIcon class="h-10 w-10 opacity-25" />
      <p class="text-sm">Nenhuma posição para a data selecionada.</p>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Ativos</p>
          <p class="text-xl font-bold mt-0.5">{{ positions.length }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Patrimônio (PM)</p>
          <p class="text-xl font-bold mt-0.5">{{ formatCurrency(totalPatrimony) }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Patrimônio (mercado)</p>
          <p class="text-xl font-bold mt-0.5" :class="quotesLoading ? 'text-muted-foreground' : ''">
            {{ quotesLoading ? '…' : totalMarketValue != null ? formatCurrency(totalMarketValue) : '—' }}
          </p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Resultado aberto</p>
          <p
            class="text-xl font-bold mt-0.5"
            :class="quotesLoading ? 'text-muted-foreground' : totalUnrealizedPnl > 0 ? 'text-emerald-600' : totalUnrealizedPnl < 0 ? 'text-red-500' : ''"
          >
            {{ quotesLoading ? '…' : totalUnrealizedPnl != null ? (totalUnrealizedPnl >= 0 ? '+' : '') + formatCurrency(totalUnrealizedPnl) : '—' }}
          </p>
        </Card>
        <Card class="px-4 py-3 col-span-2 sm:col-span-1">
          <p class="text-xs text-muted-foreground">Data base</p>
          <p class="text-xl font-bold mt-0.5">{{ formatDate(asOf) }}</p>
        </Card>
      </div>

      <Card class="overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-muted/40 border-b">
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 hover:text-foreground transition-colors" @click="toggleSort('ticker')">
                    Ticker <SortIcon field="ticker" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">Tipo</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 ml-auto hover:text-foreground transition-colors" @click="toggleSort('qty')">
                    Qtd <SortIcon field="qty" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 ml-auto hover:text-foreground transition-colors" @click="toggleSort('pm')">
                    PM Calculado <SortIcon field="pm" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">PM Efetivo</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 ml-auto hover:text-foreground transition-colors" @click="toggleSort('total')">
                    Custo total <SortIcon field="total" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 ml-auto hover:text-foreground transition-colors" @click="toggleSort('price')">
                    Cotação <SortIcon field="price" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">
                  <button type="button" class="flex items-center gap-1 ml-auto hover:text-foreground transition-colors" @click="toggleSort('upnl')">
                    Resultado aberto <SortIcon field="upnl" :sort-by="sortBy" :sort-dir="sortDir" />
                  </button>
                </th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Var %</th>
                <th class="px-4 py-3 text-center font-medium text-muted-foreground">Ajuste</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="pos in sortedPositions"
                :key="pos.ticker"
                class="border-b last:border-0 hover:bg-muted/20 transition-colors"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <span class="font-semibold font-mono">{{ pos.ticker }}</span>
                    <Badge v-if="pos.is_overridden" variant="outline" class="text-xs text-amber-600 border-amber-300">
                      manual
                    </Badge>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <select
                    :value="pos.asset_type"
                    class="text-xs rounded border border-input bg-background px-1.5 py-0.5 focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer"
                    :class="assetTypeClass(pos.asset_type)"
                    @change="setAssetType(pos.ticker, $event.target.value)"
                  >
                    <option v-for="opt in assetTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ formatQty(pos.effective_quantity) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    type="button"
                    class="tabular-nums text-muted-foreground underline decoration-dotted hover:text-foreground transition-colors"
                    title="Ver detalhamento do cálculo"
                    @click="openBreakdown(pos)"
                  >
                    {{ formatCurrency(pos.computed_mean_price) }}
                  </button>
                </td>
                <td class="px-4 py-3 text-right tabular-nums font-medium">
                  {{ formatCurrency(pos.effective_mean_price) }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ formatCurrency(pos.effective_quantity * Number(pos.effective_mean_price)) }}
                </td>
                <td class="px-4 py-3 text-right tabular-nums group" :class="quotesLoading ? 'text-muted-foreground/50' : ''">
                  <div v-if="editingQuoteTicker !== pos.ticker" class="flex items-center justify-end gap-1">
                    <span>{{ quotesLoading ? '…' : quotes[pos.ticker] != null ? formatCurrency(quotes[pos.ticker]) : '—' }}</span>
                    <button
                      type="button"
                      class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
                      title="Editar cotação manualmente"
                      @click="startEditQuote(pos.ticker)"
                    >
                      <Pencil class="h-3 w-3" />
                    </button>
                  </div>
                  <div v-else class="flex items-center justify-end gap-1">
                    <input
                      v-model="editingQuoteValue"
                      type="number"
                      step="0.01"
                      min="0"
                      class="w-24 h-6 text-xs rounded border border-primary px-1.5 text-right tabular-nums focus:outline-none focus:ring-1 focus:ring-ring"
                      @keydown.enter="saveQuote(pos.ticker)"
                      @keydown.escape="editingQuoteTicker = null"
                      @blur="saveQuote(pos.ticker)"
                    />
                  </div>
                </td>
                <td
                  class="px-4 py-3 text-right tabular-nums font-semibold"
                  :class="unrealizedPnl(pos) == null ? 'text-muted-foreground' : unrealizedPnl(pos) > 0 ? 'text-emerald-600' : unrealizedPnl(pos) < 0 ? 'text-red-500' : ''"
                >
                  {{ unrealizedPnl(pos) == null ? (quotesLoading ? '…' : '—') : (unrealizedPnl(pos) >= 0 ? '+' : '') + formatCurrency(unrealizedPnl(pos)) }}
                </td>
                <td
                  class="px-4 py-3 text-right tabular-nums"
                  :class="unrealizedPct(pos) == null ? 'text-muted-foreground' : unrealizedPct(pos) > 0 ? 'text-emerald-600' : unrealizedPct(pos) < 0 ? 'text-red-500' : ''"
                >
                  {{ unrealizedPct(pos) == null ? '—' : (unrealizedPct(pos) >= 0 ? '+' : '') + unrealizedPct(pos).toFixed(2) + '%' }}
                </td>
                <td class="px-4 py-3 text-center">
                  <div class="flex items-center justify-center gap-1">
                    <button
                      type="button"
                      class="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                      title="Editar ajuste manual"
                      @click="openEdit(pos)"
                    >
                      <Pencil class="h-3.5 w-3.5" />
                    </button>
                    <button
                      v-if="pos.is_overridden"
                      type="button"
                      class="p-1.5 rounded hover:bg-muted text-amber-500 hover:text-red-500 transition-colors"
                      title="Remover ajuste manual"
                      @click="clearOverride(pos.ticker)"
                    >
                      <RotateCcw class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </template>

    <Transition name="drawer">
      <div
        v-if="breakdownTicker"
        class="fixed inset-0 z-50 flex"
      >
        <div class="flex-1 bg-black/40" @click="breakdownTicker = null" />
        <div class="w-full max-w-2xl bg-background border-l shadow-xl flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b shrink-0">
            <div>
              <h2 class="font-semibold text-base">
                Detalhamento — <span class="font-mono">{{ breakdownTicker }}</span>
              </h2>
              <p class="text-xs text-muted-foreground mt-0.5">
                Custo médio ajustado por taxas (IRRF excluído) até {{ formatDate(asOf) }}
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
                  <tr
                    class="border-b"
                    :class="stepRowClass(step.side)"
                  >
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
                      <td class="px-4 py-2 text-right tabular-nums">{{ formatQty(step.quantity) }}</td>
                      <td class="px-4 py-2 text-right tabular-nums">{{ formatCurrency(step.raw_price) }}</td>
                      <td class="px-4 py-2 text-right tabular-nums" :class="Number(step.fee_per_unit) > 0 ? 'text-amber-600' : 'text-muted-foreground'">
                        {{ Number(step.fee_per_unit) > 0 ? (step.side === 'BUY' ? '+' : '−') : '' }}{{ formatCurrency(step.fee_per_unit) }}
                      </td>
                      <td class="px-4 py-2 text-right tabular-nums font-medium">{{ formatCurrency(step.adjusted_price) }}</td>
                    </template>
                    <td class="px-4 py-2 text-right tabular-nums">{{ formatQty(step.qty_after) }}</td>
                    <td class="px-4 py-2 text-right tabular-nums font-semibold" :class="i === breakdownSteps.length - 1 ? 'text-primary' : ''">
                      {{ formatCurrency(step.mean_price_after) }}
                    </td>
                  </tr>
                  <!-- Closed position banner inserted after a step that crosses zero -->
                  <tr v-if="step.closes_quantity != null" class="bg-muted/30 border-b border-dashed">
                    <td colspan="8" class="px-4 py-1.5">
                      <div class="flex items-center gap-3 text-xs">
                        <span class="font-medium text-muted-foreground">Posição fechada —</span>
                        <span class="text-muted-foreground">{{ formatQty(step.closes_quantity) }} ações</span>
                        <span
                          class="font-semibold"
                          :class="Number(step.realized_pnl) >= 0 ? 'text-emerald-600' : 'text-red-500'"
                        >
                          {{ Number(step.realized_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(step.realized_pnl) }}
                        </span>
                        <span v-if="step.qty_after !== 0" class="text-muted-foreground italic">
                          {{ formatQty(Math.abs(step.qty_after)) }} restantes abertos {{ step.qty_after > 0 ? 'long' : 'short' }}
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
              PM final:
              <strong class="text-foreground text-sm ml-1">
                {{ breakdownSteps.length ? formatCurrency(breakdownSteps.at(-1).mean_price_after) : '—' }}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </Transition>

    <div
      v-if="editTarget"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="editTarget = null"
    >
      <Card class="w-full max-w-sm mx-4 p-6 space-y-4">
        <div>
          <h2 class="font-semibold text-base">Ajuste manual — <span class="font-mono">{{ editTarget.ticker }}</span></h2>
          <p class="text-xs text-muted-foreground mt-1">Deixe em branco para usar o valor calculado.</p>
        </div>
        <div class="space-y-3">
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Quantidade</label>
            <input
              v-model="editQty"
              type="number"
              min="0"
              placeholder="{{ editTarget.computed_quantity }}"
              class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Preço médio (R$)</label>
            <input
              v-model="editPrice"
              type="number"
              min="0"
              step="0.01"
              placeholder="{{ editTarget.computed_mean_price }}"
              class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            class="px-4 py-2 rounded-md border text-sm hover:bg-muted transition-colors"
            @click="editTarget = null"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm hover:bg-primary/90 transition-colors"
            :disabled="saving"
            @click="saveOverride"
          >
            {{ saving ? 'Salvando…' : 'Salvar' }}
          </button>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useSortable } from '@/composables/useSortable.js'
import { assetTypeClass, formatCurrency, formatDate, formatQty } from '@/utils/format.js'
import {
  deletePositionOverride,
  getPositionBreakdown,
  getPositions,
  getQuotes,
  refreshQuotes,
  setTickerClassification,
  updatePositionOverride,
  upsertQuote,
} from '@/services/api.js'
import { AlertTriangle, ArrowDown, ArrowUp, ArrowUpDown, Inbox as InboxIcon, Loader2, Pencil, RotateCcw, X } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

// Inline sort-indicator component
const SortIcon = {
  props: ['field', 'sortBy', 'sortDir'],
  components: { ArrowUp, ArrowDown, ArrowUpDown },
  template: `
    <ArrowUp v-if="sortBy === field && sortDir === 'asc'" class="h-3 w-3 shrink-0" />
    <ArrowDown v-else-if="sortBy === field && sortDir === 'desc'" class="h-3 w-3 shrink-0" />
    <ArrowUpDown v-else class="h-3 w-3 shrink-0 opacity-30" />
  `,
}

const positions = ref([])
const loading = ref(false)
const error = ref('')
const saving = ref(false)

// ticker → { price: number, date: string } | undefined
const quotesMap = ref({})
const quotesLoading = ref(false)
const quotesRefreshing = ref(false)

// Convenience: quotes[ticker] is the price number (or null)
const quotes = computed(() =>
  Object.fromEntries(Object.entries(quotesMap.value).map(([t, q]) => [t, q?.price ?? null]))
)
const quotesDate = computed(() => {
  const dates = Object.values(quotesMap.value).map(q => q?.date).filter(Boolean)
  if (!dates.length) return null
  return dates.sort().at(-1)  // most recent date across all tickers
})
const editingQuoteTicker = ref(null)
const editingQuoteValue = ref('')

const startEditQuote = (ticker) => {
  editingQuoteTicker.value = ticker
  editingQuoteValue.value = quotes.value[ticker] != null ? String(quotes.value[ticker]) : ''
  // autofocus the input on next tick
  setTimeout(() => {
    const el = document.querySelector('input[type="number"][min="0"][step="0.01"]')
    el?.focus()
    el?.select()
  }, 30)
}

const saveQuote = async (ticker) => {
  if (editingQuoteTicker.value !== ticker) return
  editingQuoteTicker.value = null
  const val = parseFloat(editingQuoteValue.value)
  if (!isFinite(val) || val < 0) return
  try {
    const q = await upsertQuote(ticker, asOf.value, val)
    quotesMap.value = { ...quotesMap.value, [ticker]: { price: Number(q.close_price), date: q.date } }
  } catch (e) {
    error.value = e.message
  }
}

const editTarget = ref(null)
const editQty = ref('')
const editPrice = ref('')

const breakdownTicker = ref(null)
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

const assetTypeOptions = [
  { value: 'STOCK',      label: 'Ações' },
  { value: 'FII',        label: 'FII' },
  { value: 'BDR',        label: 'BDR' },
  { value: 'ETF_RV',     label: 'ETF RV' },
  { value: 'SUBSCRICAO', label: 'Subscrição' },
  { value: 'ETF_RF',     label: 'ETF RF' },
  { value: 'TD',         label: 'Tesouro Direto' },
  { value: 'CDB',        label: 'CDB' },
  { value: 'LCI',        label: 'LCI' },
  { value: 'LCA',        label: 'LCA' },
  { value: 'LCF',        label: 'LCF' },
  { value: 'LIG',        label: 'LIG' },
  { value: 'CRI',        label: 'CRI' },
  { value: 'CRA',        label: 'CRA' },
  { value: 'DEB',        label: 'Debênture' },
  { value: 'RF_POS',     label: 'RF Pós' },
  { value: 'RF_PRE',     label: 'RF Pré' },
]


const setAssetType = async (ticker, assetType) => {
  try {
    await setTickerClassification(ticker, assetType)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

const openBreakdown = async (pos) => {
  breakdownTicker.value = pos.ticker
  breakdownSteps.value = []
  breakdownLoading.value = true
  try {
    breakdownSteps.value = await getPositionBreakdown(pos.ticker, asOf.value)
  } catch (e) {
    error.value = e.message
    breakdownTicker.value = null
  } finally {
    breakdownLoading.value = false
  }
}

const today = () => new Date().toISOString().slice(0, 10)
const asOf = ref(today())

const setToday = () => {
  asOf.value = today()
  load()
}

const totalPatrimony = computed(() =>
  positions.value.reduce(
    (sum, p) => sum + p.effective_quantity * Number(p.effective_mean_price),
    0,
  ),
)

const unrealizedPnl = (pos) => {
  const price = quotes.value[pos.ticker]
  if (price == null) return null
  return (price - Number(pos.effective_mean_price)) * pos.effective_quantity
}

const unrealizedPct = (pos) => {
  const pm = Number(pos.effective_mean_price)
  const price = quotes.value[pos.ticker]
  if (price == null || !pm) return null
  return ((price - pm) / pm) * 100
}

const totalMarketValue = computed(() => {
  const list = positions.value
  if (!list.length || !Object.keys(quotes.value).length) return null
  let total = 0
  let hasAny = false
  for (const p of list) {
    const price = quotes.value[p.ticker]
    if (price != null) { total += price * p.effective_quantity; hasAny = true }
    else total += p.effective_quantity * Number(p.effective_mean_price)
  }
  return hasAny ? total : null
})

const totalUnrealizedPnl = computed(() => {
  const list = positions.value
  if (!list.length) return null
  let total = 0
  let hasAny = false
  for (const p of list) {
    const pnl = unrealizedPnl(p)
    if (pnl != null) { total += pnl; hasAny = true }
  }
  return hasAny ? total : null
})

const { sortBy, sortDir, sorted: sortedPositions, toggleSort } = useSortable(positions, {
  ticker: (a, b) => a.ticker.localeCompare(b.ticker),
  qty:    (a, b) => a.effective_quantity - b.effective_quantity,
  pm:     (a, b) => Number(a.computed_mean_price) - Number(b.computed_mean_price),
  total:  (a, b) =>
    a.effective_quantity * Number(a.effective_mean_price) -
    b.effective_quantity * Number(b.effective_mean_price),
  price:  (a, b) => (quotes.value[a.ticker] ?? -Infinity) - (quotes.value[b.ticker] ?? -Infinity),
  upnl:   (a, b) => (unrealizedPnl(a) ?? -Infinity) - (unrealizedPnl(b) ?? -Infinity),
})
sortBy.value = 'ticker'


const buildQuotesMap = (rows) =>
  Object.fromEntries(rows.map(r => [r.ticker, { price: Number(r.close_price), date: r.date }]))

const loadQuotes = async () => {
  const tickers = positions.value.map(p => p.ticker)
  if (!tickers.length) return
  quotesLoading.value = true
  try {
    const rows = await getQuotes(tickers, asOf.value)
    quotesMap.value = buildQuotesMap(rows)
  } catch {
    // quotes are best-effort
  } finally {
    quotesLoading.value = false
  }
}

const doRefreshQuotes = async () => {
  quotesRefreshing.value = true
  try {
    const rows = await refreshQuotes()
    quotesMap.value = buildQuotesMap(rows)
  } catch (e) {
    error.value = e.message
  } finally {
    quotesRefreshing.value = false
  }
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    positions.value = await getPositions(asOf.value)
    loadQuotes() // fire-and-forget so positions appear immediately
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const openEdit = (pos) => {
  editTarget.value = pos
  editQty.value = pos.manual_quantity ?? ''
  editPrice.value = pos.manual_mean_price ?? ''
}

const saveOverride = async () => {
  saving.value = true
  try {
    const body = {}
    if (editQty.value !== '') body.manual_quantity = Number(editQty.value)
    if (editPrice.value !== '') body.manual_mean_price = editPrice.value
    await updatePositionOverride(editTarget.value.ticker, body)
    editTarget.value = null
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

const clearOverride = async (ticker) => {
  try {
    await deletePositionOverride(ticker)
    await load()
  } catch (e) {
    error.value = e.message
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
