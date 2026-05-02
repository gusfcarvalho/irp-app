<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Evolução do patrimônio por categoria — valor de mercado vs. custo investido.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="flex items-center gap-1.5 h-9 px-3 rounded-md border border-input text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          :disabled="refreshing || loading"
          @click="doRefreshQuotes"
        >
          <RefreshCw class="h-3.5 w-3.5" :class="refreshing ? 'animate-spin' : ''" />
          {{ refreshing ? 'Atualizando…' : lastQuoteDate ? `Cotações ${lastQuoteDate}` : 'Atualizar cotações' }}
        </button>

        <div class="flex items-center gap-1 rounded-lg border p-1">
        <button
          v-for="m in MODES"
          :key="m.value"
          type="button"
          class="px-3 py-1 rounded-md text-sm font-medium transition-colors"
          :class="mode === m.value
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:text-foreground'"
          @click="setMode(m.value)"
        >
          {{ m.label }}
        </button>
        </div>
      </div>
    </div>

    <Alert v-if="error" variant="destructive">
      <AlertTriangle class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ error }}</span>
    </Alert>

    <!-- Chart card -->
    <Card class="p-4">
      <!-- Breadcrumb when drilled down -->
      <div v-if="drillCategory" class="flex items-center gap-2 mb-3">
        <button
          type="button"
          class="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          @click="exitDrill"
        >
          <ChevronLeft class="h-4 w-4" />
          Voltar
        </button>
        <span class="text-muted-foreground text-sm">/</span>
        <span class="text-sm font-medium" :style="{ color: categoryColor(drillCategory) }">
          {{ categoryLabel(drillCategory) }}
        </span>
        <span class="text-xs text-muted-foreground ml-1">· clique no gráfico para voltar</span>
      </div>

      <div v-if="loading" class="flex justify-center items-center h-72">
        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
      <div v-else-if="!points.length" class="flex flex-col items-center gap-3 h-72 justify-center text-muted-foreground">
        <BarChart2 class="h-10 w-10 opacity-25" />
        <p class="text-sm">Nenhuma transação encontrada.</p>
      </div>
      <div v-else class="relative" style="height: 340px;">
        <canvas ref="chartCanvas" />
      </div>
    </Card>

    <!-- Legend -->
    <div v-if="points.length" class="flex flex-wrap gap-3">
      <template v-if="!drillCategory">
        <div v-for="cat in assetTypes" :key="cat" class="flex items-center gap-1.5 text-sm">
          <span class="inline-block w-3 h-3 rounded-sm shrink-0" :style="{ background: categoryColor(cat) }" />
          <span class="text-muted-foreground">{{ categoryLabel(cat) }}</span>
        </div>
        <div class="flex items-center gap-1.5 text-sm">
          <span class="inline-block w-5 border-t-2 border-dashed shrink-0" style="border-color: #0f172a" />
          <span class="text-muted-foreground">Custo total</span>
        </div>
      </template>
      <template v-else>
        <div v-for="(ticker, i) in drillTickers" :key="ticker" class="flex items-center gap-1.5 text-sm">
          <span class="inline-block w-3 h-3 rounded-sm shrink-0" :style="{ background: tickerColor(i) }" />
          <span class="text-muted-foreground font-mono">{{ ticker }}</span>
        </div>
        <div class="flex items-center gap-1.5 text-sm">
          <span
            class="inline-block w-5 border-t-2 shrink-0"
            :style="{ borderColor: categoryColor(drillCategory) }"
          />
          <span class="text-muted-foreground">Total {{ categoryLabel(drillCategory) }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { formatCurrency } from '@/utils/format.js'
import { getPortfolioHistory, refreshQuotes } from '@/services/api.js'
import { AlertTriangle, BarChart2, ChevronLeft, Loader2, RefreshCw } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Card from '@/components/ui/Card.vue'

Chart.register(CategoryScale, LinearScale, BarController, BarElement, LineController, LineElement, PointElement, Tooltip, Legend)

// ── Constants ─────────────────────────────────────────────────────────────────

const MODES = [
  { value: 'daily',   label: 'Diário' },
  { value: 'weekly',  label: 'Semanal' },
  { value: 'monthly', label: 'Mensal' },
]

const CATEGORY_COLORS = {
  STOCK:      '#3b82f6',
  BDR:        '#8b5cf6',
  FII:        '#10b981',
  ETF_RV:     '#f59e0b',
  ETF_RF:     '#94a3b8',
  SUBSCRICAO: '#ec4899',
  RF_POS:     '#64748b',
  RF_PRE:     '#475569',
}

const CATEGORY_LABELS = {
  STOCK:      'Ações',
  BDR:        'BDRs',
  FII:        'FIIs',
  ETF_RV:     'ETF RV',
  ETF_RF:     'ETF RF',
  SUBSCRICAO: 'Subscrição',
  RF_POS:     'RF Pós',
  RF_PRE:     'RF Pré',
}

const TICKER_PALETTE = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
  '#14b8a6', '#a855f7', '#eab308', '#22c55e', '#0ea5e9',
  '#d946ef', '#fb923c', '#4ade80', '#38bdf8', '#c084fc',
]

const categoryColor = (cat) => CATEGORY_COLORS[cat] ?? '#cbd5e1'
const categoryLabel = (cat) => CATEGORY_LABELS[cat] ?? cat
const tickerColor = (i) => TICKER_PALETTE[i % TICKER_PALETTE.length]

// ── State ─────────────────────────────────────────────────────────────────────

const mode = ref('monthly')
const points = ref([])
const assetTypes = ref([])
const loading = ref(false)
const refreshing = ref(false)
const error = ref('')
const drillCategory = ref(null)
const lastQuoteDate = ref(null)

const chartCanvas = ref(null)
let chartInstance = null

// Tickers in the drilled category, sorted by total value descending
const drillTickers = computed(() => {
  if (!drillCategory.value) return []
  const cat = drillCategory.value
  const totals = {}
  for (const p of points.value) {
    for (const [t, v] of Object.entries(p.breakdown[cat] ?? {})) {
      totals[t] = (totals[t] ?? 0) + v
    }
  }
  return Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .map(([t]) => t)
})

// ── Data loading ──────────────────────────────────────────────────────────────

const load = async () => {
  loading.value = true
  error.value = ''
  drillCategory.value = null
  try {
    const res = await getPortfolioHistory(mode.value)
    points.value = res.points
    assetTypes.value = res.asset_types
    if (res.last_quote_date) lastQuoteDate.value = res.last_quote_date
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart()
}

const setMode = (m) => {
  mode.value = m
  load()
}

const doRefreshQuotes = async () => {
  refreshing.value = true
  error.value = ''
  try {
    await refreshQuotes([], true)
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    refreshing.value = false
  }
}

const exitDrill = () => {
  drillCategory.value = null
  nextTick(renderChart)
}

// ── Chart helpers ─────────────────────────────────────────────────────────────

const getLabels = () => points.value.map(p => {
  const [y, m, d] = p.date.split('-')
  if (mode.value === 'monthly') return `${m}/${y.slice(2)}`
  if (mode.value === 'weekly')  return `${d}/${m}/${y.slice(2)}`
  return `${d}/${m}`
})

const sharedOptions = () => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'nearest', intersect: true },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`,
      },
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { maxRotation: 45, font: { size: 11 } },
    },
    y: {
      stacked: true,
      ticks: {
        callback: (v) => {
          if (v >= 1_000_000) return `R$${(v / 1_000_000).toFixed(1)}M`
          if (v >= 1_000)     return `R$${(v / 1_000).toFixed(0)}k`
          return `R$${v}`
        },
        font: { size: 11 },
      },
      grid: { color: '#f1f5f9' },
    },
  },
})

// ── Chart rendering ───────────────────────────────────────────────────────────

const renderChart = () => {
  if (!chartCanvas.value || !points.value.length) return
  if (chartInstance) { chartInstance.destroy(); chartInstance = null }
  drillCategory.value ? renderDrillChart() : renderOverviewChart()
}

const renderOverviewChart = () => {
  const sparse = points.value.length > 60

  const barDatasets = assetTypes.value.map(cat => ({
    type: 'bar',
    label: categoryLabel(cat),
    data: points.value.map(p => p.by_category[cat] ?? 0),
    backgroundColor: categoryColor(cat),
    stack: 'portfolio',
    borderRadius: 2,
    borderSkipped: false,
    order: 2,
  }))

  const lineDataset = {
    type: 'line',
    label: 'Custo total',
    data: points.value.map(p => p.cost_total),
    borderColor: '#0f172a',
    borderWidth: 2,
    borderDash: [4, 3],
    pointRadius: sparse ? 0 : 3,
    pointHoverRadius: 5,
    fill: false,
    tension: 0.1,
    order: 1,
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: { labels: getLabels(), datasets: [...barDatasets, lineDataset] },
    options: {
      ...sharedOptions(),
      onClick: (event, _elements, chart) => {
        const hit = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, false)
        if (!hit.length) return
        const { datasetIndex } = hit[0]
        if (datasetIndex >= assetTypes.value.length) return // clicked the line
        drillCategory.value = assetTypes.value[datasetIndex]
        nextTick(renderChart)
      },
    },
  })
}

const renderDrillChart = () => {
  const cat = drillCategory.value
  const tickers = drillTickers.value
  const sparse = points.value.length > 60

  const barDatasets = tickers.map((ticker, i) => ({
    type: 'bar',
    label: ticker,
    data: points.value.map(p => p.breakdown[cat]?.[ticker] ?? 0),
    backgroundColor: tickerColor(i),
    stack: 'category',
    borderRadius: 2,
    borderSkipped: false,
    order: 2,
  }))

  const lineDataset = {
    type: 'line',
    label: categoryLabel(cat),
    data: points.value.map(p => p.by_category[cat] ?? 0),
    borderColor: categoryColor(cat),
    borderWidth: 2.5,
    pointRadius: sparse ? 0 : 3,
    pointHoverRadius: 5,
    fill: false,
    tension: 0.1,
    order: 1,
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: { labels: getLabels(), datasets: [...barDatasets, lineDataset] },
    options: {
      ...sharedOptions(),
      onClick: () => exitDrill(),
    },
  })
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(load)

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>
