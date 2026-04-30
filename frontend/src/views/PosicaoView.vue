<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Posição</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Custo médio ajustado por taxas de corretagem, do início até a data selecionada.
        </p>
      </div>

      <div class="flex items-center gap-2">
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
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Ativos</p>
          <p class="text-xl font-bold mt-0.5">{{ positions.length }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Patrimônio estimado</p>
          <p class="text-xl font-bold mt-0.5">{{ formatCurrency(totalPatrimony) }}</p>
        </Card>
        <Card class="px-4 py-3">
          <p class="text-xs text-muted-foreground">Com ajuste manual</p>
          <p class="text-xl font-bold mt-0.5">{{ positions.filter(p => p.is_overridden).length }}</p>
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
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">Ticker</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Qtd</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">PM Calculado</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">PM Efetivo</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Custo total</th>
                <th class="px-4 py-3 text-center font-medium text-muted-foreground">Ajuste</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="pos in positions"
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
                <td class="px-4 py-3 text-right tabular-nums">
                  {{ pos.effective_quantity.toLocaleString('pt-BR') }}
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
                  <!-- Closed position banner inserted after a step that crosses zero -->
                  <tr v-if="step.closes_quantity != null" class="bg-muted/30 border-b border-dashed">
                    <td colspan="8" class="px-4 py-1.5">
                      <div class="flex items-center gap-3 text-xs">
                        <span class="font-medium text-muted-foreground">Posição fechada —</span>
                        <span class="text-muted-foreground">{{ step.closes_quantity.toLocaleString('pt-BR') }} ações</span>
                        <span
                          class="font-semibold"
                          :class="Number(step.realized_pnl) >= 0 ? 'text-emerald-600' : 'text-red-500'"
                        >
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
import { AlertTriangle, Inbox as InboxIcon, Loader2, Pencil, RotateCcw, X } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const positions = ref([])
const loading = ref(false)
const error = ref('')
const saving = ref(false)
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

const openBreakdown = async (pos) => {
  breakdownTicker.value = pos.ticker
  breakdownSteps.value = []
  breakdownLoading.value = true
  try {
    const url = `/api/positions/${pos.ticker}/breakdown` + (asOf.value ? `?as_of=${asOf.value}` : '')
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

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatDate = (iso) => {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const url = asOf.value ? `/api/positions?as_of=${asOf.value}` : '/api/positions'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    positions.value = await res.json()
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

    const res = await fetch(`/api/positions/${editTarget.value.ticker}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Erro ${res.status}`)
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
    const res = await fetch(`/api/positions/${ticker}/override`, { method: 'DELETE' })
    if (!res.ok) throw new Error(`Erro ${res.status}`)
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
