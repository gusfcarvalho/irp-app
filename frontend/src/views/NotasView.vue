<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Notas de Corretagem</h1>
        <p class="text-muted-foreground text-sm mt-1">
          Todas as notas importadas, com suas transações.
        </p>
      </div>
      <button
        class="text-muted-foreground hover:text-foreground transition-colors"
        title="Atualizar"
        type="button"
        @click="load"
      >
        <RefreshCw class="h-4 w-4" :class="loading ? 'animate-spin' : ''" />
      </button>
    </div>

    <Alert v-if="error" variant="destructive">
      <AlertTriangle class="h-4 w-4 shrink-0 mt-0.5" />
      <span>{{ error }}</span>
    </Alert>

    <div v-if="loading && !notas.length" class="flex justify-center py-16">
      <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
    </div>

    <div v-else-if="!notas.length" class="flex flex-col items-center gap-3 py-16 text-muted-foreground">
      <InboxIcon class="h-10 w-10 opacity-25" />
      <p class="text-sm">Nenhuma nota importada ainda.</p>
      <RouterLink to="/import">
        <Button variant="outline" size="sm" class="gap-2">
          <Upload class="h-4 w-4" />
          Importar primeira nota
        </Button>
      </RouterLink>
    </div>

    <div v-else class="space-y-4">
      <Card
        v-for="nota in notas"
        :key="nota.id"
        class="overflow-hidden"
      >
        <button
          class="w-full flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors text-left"
          type="button"
          @click="toggle(nota.id)"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10">
              <FileText class="h-4 w-4 text-primary" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-semibold text-sm truncate">{{ nota.filename }}</span>
                <Badge v-if="nota.note_number" variant="secondary" class="font-mono text-xs">
                  #{{ nota.note_number }}
                </Badge>
                <Badge variant="outline" class="text-xs">{{ nota.broker }}</Badge>
              </div>
              <p class="text-xs text-muted-foreground mt-0.5">
                {{ formatDatetime(nota.uploaded_at) }} &middot;
                {{ nota.transactions.length }} transaç{{ nota.transactions.length === 1 ? 'ão' : 'ões' }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0 ml-4">
            <span class="text-sm font-semibold tabular-nums hidden sm:block">
              {{ formatCurrency(totalValue(nota)) }}
            </span>
            <ChevronDown
              class="h-4 w-4 text-muted-foreground transition-transform duration-200"
              :class="expanded.has(nota.id) ? 'rotate-180' : ''"
            />
          </div>
        </button>

        <div v-if="expanded.has(nota.id)" class="border-t">
          <div v-if="totalFees(nota) > 0" class="px-5 py-3 bg-muted/20 border-b flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
            <span v-if="+nota.settlement_fee">Liquidação: <strong class="text-foreground">{{ formatCurrency(nota.settlement_fee) }}</strong></span>
            <span v-if="+nota.registration_fee">Registro: <strong class="text-foreground">{{ formatCurrency(nota.registration_fee) }}</strong></span>
            <span v-if="+nota.term_fee">Termo/Opções: <strong class="text-foreground">{{ formatCurrency(nota.term_fee) }}</strong></span>
            <span v-if="+nota.ana_fee">ANA: <strong class="text-foreground">{{ formatCurrency(nota.ana_fee) }}</strong></span>
            <span v-if="+nota.emoluments">Emolumentos: <strong class="text-foreground">{{ formatCurrency(nota.emoluments) }}</strong></span>
            <span v-if="+nota.operational_fee">Taxa Operacional: <strong class="text-foreground">{{ formatCurrency(nota.operational_fee) }}</strong></span>
            <span v-if="+nota.execution">Execução: <strong class="text-foreground">{{ formatCurrency(nota.execution) }}</strong></span>
            <span v-if="+nota.custody_fee">Custódia: <strong class="text-foreground">{{ formatCurrency(nota.custody_fee) }}</strong></span>
            <span v-if="+nota.taxes">Impostos: <strong class="text-foreground">{{ formatCurrency(nota.taxes) }}</strong></span>
            <span v-if="+nota.irrf">IRRF: <strong class="text-foreground">{{ formatCurrency(nota.irrf) }}</strong></span>
            <span v-if="+nota.other_fees">Outros: <strong class="text-foreground">{{ formatCurrency(nota.other_fees) }}</strong></span>
            <span v-if="+nota.depositary_fee">Taxa Depositária: <strong class="text-foreground">{{ formatCurrency(nota.depositary_fee) }}</strong></span>
            <span class="font-medium text-foreground">Total taxas: {{ formatCurrency(totalFees(nota)) }}</span>
            <span class="ml-auto font-semibold tabular-nums" :class="valorLiquido(nota) >= 0 ? 'text-blue-600' : 'text-red-600'">
              Valor Líquido: {{ formatCurrency(Math.abs(valorLiquido(nota))) }} {{ valorLiquido(nota) >= 0 ? 'C' : 'D' }}
            </span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-muted/40 border-b">
                  <th class="px-4 py-2.5 text-left font-medium text-muted-foreground">Data</th>
                  <th class="px-4 py-2.5 text-left font-medium text-muted-foreground">Ticker</th>
                  <th class="px-4 py-2.5 text-left font-medium text-muted-foreground">Operação</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Qtd</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Preço Unit.</th>
                  <th class="px-4 py-2.5 text-right font-medium text-muted-foreground">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="tx in nota.transactions"
                  :key="tx.id"
                  class="border-b last:border-0 hover:bg-muted/20 transition-colors"
                >
                  <td class="px-4 py-2.5 text-muted-foreground tabular-nums">{{ formatDate(tx.trade_date) }}</td>
                  <td class="px-4 py-2.5 font-semibold font-mono">{{ tx.ticker }}</td>
                  <td class="px-4 py-2.5">
                    <Badge :variant="tx.side === 'BUY' ? 'default' : 'destructive'">
                      {{ tx.side === 'BUY' ? 'Compra' : 'Venda' }}
                    </Badge>
                  </td>
                  <td class="px-4 py-2.5 text-right tabular-nums">{{ tx.quantity.toLocaleString('pt-BR') }}</td>
                  <td class="px-4 py-2.5 text-right tabular-nums">{{ formatCurrency(tx.price) }}</td>
                  <td class="px-4 py-2.5 text-right tabular-nums font-medium">
                    {{ formatCurrency(Number(tx.price) * tx.quantity) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  AlertTriangle,
  ChevronDown,
  FileText,
  Loader2,
  RefreshCw,
  Upload,
  Inbox as InboxIcon,
} from 'lucide-vue-next'
import Alert from '@/components/ui/Alert.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'

const notas = ref([])
const loading = ref(false)
const error = ref('')
const expanded = ref(new Set())

const toggle = (id) => {
  if (expanded.value.has(id)) {
    expanded.value.delete(id)
  } else {
    expanded.value.add(id)
  }
  expanded.value = new Set(expanded.value)
}

const formatDate = (d) => {
  if (!d) return ''
  const [y, m, day] = String(d).split('-')
  return `${day}/${m}/${y}`
}

const formatDatetime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const totalValue = (nota) =>
  nota.transactions.reduce((sum, t) => sum + Number(t.price) * t.quantity, 0)

const totalFees = (nota) =>
  ['settlement_fee', 'registration_fee', 'term_fee', 'ana_fee', 'emoluments',
   'operational_fee', 'execution', 'custody_fee', 'taxes', 'irrf', 'other_fees', 'depositary_fee']
    .reduce((sum, k) => sum + Number(nota[k] ?? 0), 0)

// Valor Líquido: net settlement cash flow — IRRF is withheld separately and does not
// affect the D+2 settlement amount, so it is excluded here.
const valorLiquido = (nota) => {
  const tradeNet = nota.transactions.reduce((sum, t) => {
    const val = Number(t.price) * t.quantity
    return sum + (t.side === 'SELL' ? val : -val)
  }, 0)
  const fees = ['settlement_fee', 'registration_fee', 'term_fee', 'ana_fee', 'emoluments',
    'operational_fee', 'execution', 'custody_fee', 'taxes', 'other_fees', 'depositary_fee']
    .reduce((sum, k) => sum + Number(nota[k] ?? 0), 0)
  return tradeNet - fees
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/uploads')
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    notas.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
