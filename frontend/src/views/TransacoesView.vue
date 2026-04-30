<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-end gap-4">
      <div class="flex-1">
        <h1 class="text-2xl font-bold tracking-tight">Transacoes Manuais</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Adicione transacoes manualmente: compra, venda, desdobramento, grupamento ou bonificacao.
        </p>
      </div>
      <button
        type="button"
        class="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
        @click="openCreate"
      >
        <Plus class="h-4 w-4" />
        Nova Transacao
      </button>
    </div>

    <Alert v-if="error" variant="destructive">
      <AlertTriangle class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ error }}</span>
    </Alert>

    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
    </div>

    <div v-else-if="!transactions.length" class="flex flex-col items-center gap-3 py-16 text-muted-foreground">
      <InboxIcon class="h-10 w-10 opacity-25" />
      <p class="text-sm">Nenhuma transacao manual cadastrada.</p>
      <button
        type="button"
        class="text-sm text-primary hover:underline"
        @click="openCreate"
      >
        Adicionar primeira transacao
      </button>
    </div>

    <Card v-else class="overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-muted/40 border-b">
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Data</th>
              <th class="px-4 py-3 text-left font-medium text-muted-foreground">Ticker</th>
              <th class="px-4 py-3 text-center font-medium text-muted-foreground">Tipo</th>
              <th class="px-4 py-3 text-right font-medium text-muted-foreground">Detalhes</th>
              <th class="px-4 py-3 text-center font-medium text-muted-foreground">Acoes</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="txn in transactions"
              :key="txn.id"
              class="border-b last:border-0 hover:bg-muted/20 transition-colors"
            >
              <td class="px-4 py-3 tabular-nums text-muted-foreground">
                {{ formatDate(txn.trade_date) }}
              </td>
              <td class="px-4 py-3 font-semibold font-mono">
                {{ txn.ticker }}
              </td>
              <td class="px-4 py-3 text-center">
                <Badge :variant="getTypeVariant(txn.transaction_type)">
                  {{ getTypeLabel(txn.transaction_type) }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right tabular-nums">
                <span v-if="txn.transaction_type === 'BUY' || txn.transaction_type === 'SELL'">
                  {{ txn.quantity }} x {{ formatCurrency(txn.price) }}
                </span>
                <span v-else-if="txn.transaction_type === 'BONUS'">
                  {{ txn.quantity }} acoes
                  <span v-if="txn.price && Number(txn.price) > 0"> x {{ formatCurrency(txn.price) }}</span>
                </span>
                <span v-else>
                  {{ txn.ratio_from }}:{{ txn.ratio_to }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button
                    type="button"
                    class="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                    title="Editar"
                    @click="openEdit(txn)"
                  >
                    <Pencil class="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    class="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-red-500 transition-colors"
                    title="Excluir"
                    @click="confirmDelete(txn)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Create/Edit Modal -->
    <div
      v-if="showForm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showForm = false"
    >
      <Card class="w-full max-w-md mx-4 p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div>
          <h2 class="font-semibold text-base">
            {{ editingId ? 'Editar' : 'Nova' }} Transacao
          </h2>
        </div>

        <div class="space-y-4">
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Tipo de Transacao</label>
            <select
              v-model="form.transaction_type"
              class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="BUY">Compra</option>
              <option value="SELL">Venda</option>
              <option value="SPLITTING">Desdobramento</option>
              <option value="GROUPING">Grupamento</option>
              <option value="BONUS">Bonificacao</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">Ticker</label>
              <input
                v-model="form.ticker"
                type="text"
                placeholder="PETR4"
                class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring uppercase"
              />
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">Data</label>
              <input
                v-model="form.trade_date"
                type="date"
                class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          </div>

          <!-- BUY/SELL fields -->
          <template v-if="form.transaction_type === 'BUY' || form.transaction_type === 'SELL'">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">Quantidade</label>
                <input
                  v-model.number="form.quantity"
                  type="number"
                  min="1"
                  placeholder="100"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">Preco (R$)</label>
                <input
                  v-model="form.price"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="30.50"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>

            <!-- Fees accordion -->
            <details class="border rounded-md">
              <summary class="px-3 py-2 text-sm font-medium cursor-pointer hover:bg-muted/50">
                Taxas (opcional)
              </summary>
              <div class="px-3 pb-3 pt-1 grid grid-cols-2 gap-2">
                <div>
                  <label class="text-xs text-muted-foreground">Taxa de liquidacao</label>
                  <input v-model="form.settlement_fee" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground">Taxa de registro</label>
                  <input v-model="form.registration_fee" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground">Emolumentos</label>
                  <input v-model="form.emoluments" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground">Corretagem</label>
                  <input v-model="form.operational_fee" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground">ISS</label>
                  <input v-model="form.taxes" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground">Outras taxas</label>
                  <input v-model="form.other_fees" type="number" step="0.01" class="w-full h-8 rounded border px-2 text-sm" />
                </div>
              </div>
            </details>
          </template>

          <!-- SPLITTING/GROUPING fields -->
          <template v-if="form.transaction_type === 'SPLITTING' || form.transaction_type === 'GROUPING'">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">De (ratio)</label>
                <input
                  v-model.number="form.ratio_from"
                  type="number"
                  min="1"
                  placeholder="1"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">Para (ratio)</label>
                <input
                  v-model.number="form.ratio_to"
                  type="number"
                  min="1"
                  placeholder="2"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>
            <p class="text-xs text-muted-foreground">
              <template v-if="form.transaction_type === 'SPLITTING'">
                Desdobramento: cada {{ form.ratio_from || 1 }} acao se torna {{ form.ratio_to || 2 }} acoes.
              </template>
              <template v-else>
                Grupamento: cada {{ form.ratio_from || 2 }} acoes se tornam {{ form.ratio_to || 1 }} acao.
              </template>
            </p>
          </template>

          <!-- BONUS fields -->
          <template v-if="form.transaction_type === 'BONUS'">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">Quantidade de acoes bonificadas</label>
                <input
                  v-model.number="form.quantity"
                  type="number"
                  min="1"
                  placeholder="10"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">Preco de bonificacao (R$)</label>
                <input
                  v-model="form.price"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>
            <p class="text-xs text-muted-foreground">
              Deixe o preco em branco ou zero para bonificacao sem custo declarado.
            </p>
          </template>
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            class="px-4 py-2 rounded-md border text-sm hover:bg-muted transition-colors"
            @click="showForm = false"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm hover:bg-primary/90 transition-colors"
            :disabled="saving"
            @click="saveTransaction"
          >
            {{ saving ? 'Salvando...' : 'Salvar' }}
          </button>
        </div>
      </Card>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="deleteTarget"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="deleteTarget = null"
    >
      <Card class="w-full max-w-sm mx-4 p-6 space-y-4">
        <div>
          <h2 class="font-semibold text-base">Confirmar exclusao</h2>
          <p class="text-sm text-muted-foreground mt-2">
            Tem certeza que deseja excluir esta transacao de
            <strong>{{ deleteTarget.ticker }}</strong>?
          </p>
        </div>
        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="px-4 py-2 rounded-md border text-sm hover:bg-muted transition-colors"
            @click="deleteTarget = null"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="px-4 py-2 rounded-md bg-destructive text-destructive-foreground text-sm hover:bg-destructive/90 transition-colors"
            @click="deleteTransaction"
          >
            Excluir
          </button>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { AlertTriangle, Inbox as InboxIcon, Loader2, Pencil, Plus, Trash2 } from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const transactions = ref([])
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const showForm = ref(false)
const editingId = ref(null)
const deleteTarget = ref(null)

const defaultForm = () => ({
  ticker: '',
  trade_date: new Date().toISOString().slice(0, 10),
  transaction_type: 'BUY',
  quantity: null,
  price: null,
  ratio_from: 1,
  ratio_to: 2,
  settlement_fee: 0,
  registration_fee: 0,
  term_fee: 0,
  ana_fee: 0,
  emoluments: 0,
  operational_fee: 0,
  execution: 0,
  custody_fee: 0,
  taxes: 0,
  irrf: 0,
  other_fees: 0,
})

const form = ref(defaultForm())

const formatDate = (iso) => {
  if (!iso) return '-'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const getTypeLabel = (type) => {
  const labels = {
    BUY: 'Compra',
    SELL: 'Venda',
    SPLITTING: 'Desdobramento',
    GROUPING: 'Grupamento',
    BONUS: 'Bonificacao',
  }
  return labels[type] || type
}

const getTypeVariant = (type) => {
  if (type === 'BUY' || type === 'BONUS') return 'default'
  if (type === 'SELL') return 'destructive'
  return 'outline'
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/manual-transactions')
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    transactions.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  form.value = defaultForm()
  showForm.value = true
}

const openEdit = (txn) => {
  editingId.value = txn.id
  form.value = {
    ticker: txn.ticker,
    trade_date: txn.trade_date,
    transaction_type: txn.transaction_type,
    quantity: txn.quantity,
    price: txn.price,
    ratio_from: txn.ratio_from || 1,
    ratio_to: txn.ratio_to || 2,
    settlement_fee: txn.settlement_fee || 0,
    registration_fee: txn.registration_fee || 0,
    term_fee: txn.term_fee || 0,
    ana_fee: txn.ana_fee || 0,
    emoluments: txn.emoluments || 0,
    operational_fee: txn.operational_fee || 0,
    execution: txn.execution || 0,
    custody_fee: txn.custody_fee || 0,
    taxes: txn.taxes || 0,
    irrf: txn.irrf || 0,
    other_fees: txn.other_fees || 0,
  }
  showForm.value = true
}

const saveTransaction = async () => {
  saving.value = true
  error.value = ''
  try {
    const body = { ...form.value }
    body.ticker = body.ticker.toUpperCase()

    const url = editingId.value
      ? `/api/manual-transactions/${editingId.value}`
      : '/api/manual-transactions'
    const method = editingId.value ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || `Erro ${res.status}`)
    }

    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

const confirmDelete = (txn) => {
  deleteTarget.value = txn
}

const deleteTransaction = async () => {
  if (!deleteTarget.value) return
  try {
    const res = await fetch(`/api/manual-transactions/${deleteTarget.value.id}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    deleteTarget.value = null
    await load()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>
