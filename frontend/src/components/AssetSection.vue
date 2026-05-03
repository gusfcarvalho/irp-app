<template>
  <Card class="overflow-hidden">
    <button
      type="button"
      class="w-full flex items-center justify-between px-4 py-3 border-b hover:bg-muted/20 transition-colors"
      @click="open = !open"
    >
      <div class="flex items-center gap-2">
        <span class="font-semibold text-sm">{{ title }}</span>
        <Badge v-if="data.exempt" variant="outline" class="text-[10px] px-1.5 py-0">Isento</Badge>
      </div>
      <span class="text-xs text-muted-foreground">{{ open ? '▲' : '▼' }}</span>
    </button>

    <!-- Row 1: P&L and accumulated loss flow -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 px-4 py-3 border-b text-sm">
      <div>
        <p class="text-xs text-muted-foreground">Total vendido</p>
        <p class="font-semibold tabular-nums">{{ formatCurrency(data.total_sold_value) }}</p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground">Resultado bruto</p>
        <p class="font-semibold tabular-nums" :class="pnlClass(data.profit_loss)">
          {{ Number(data.profit_loss) >= 0 ? '+' : '' }}{{ formatCurrency(data.profit_loss) }}
        </p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground">Prejuízo acumulado</p>
        <p
          class="font-semibold tabular-nums"
          :class="Number(data.accumulated_loss_before) > 0 ? 'text-amber-600' : 'text-muted-foreground'"
        >
          {{ formatCurrency(data.accumulated_loss_before) }}
        </p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground">Compensado</p>
        <p
          class="font-semibold tabular-nums"
          :class="Number(data.accumulated_loss_applied) > 0 ? 'text-emerald-600' : 'text-muted-foreground'"
        >
          {{ Number(data.accumulated_loss_applied) > 0 ? '-' : '' }}{{ formatCurrency(data.accumulated_loss_applied) }}
        </p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground">Base tributável</p>
        <p class="font-semibold tabular-nums" :class="pnlClass(data.taxable_profit)">
          {{ Number(data.taxable_profit) >= 0 ? '+' : '' }}{{ formatCurrency(data.taxable_profit) }}
        </p>
      </div>
    </div>

    <!-- Row 2: Tax computation and carry-forward result -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 px-4 py-3 border-b text-sm bg-muted/20">
      <div>
        <p class="text-xs text-muted-foreground">Imposto bruto ({{ taxRateLabel }})</p>
        <p class="font-semibold tabular-nums">{{ formatCurrency(data.gross_tax) }}</p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground">IRRF retido</p>
        <p class="font-semibold tabular-nums">{{ formatCurrency(data.irrf_withheld) }}</p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground font-medium">A pagar</p>
        <p
          class="font-bold tabular-nums"
          :class="Number(data.tax_due) > 0 ? 'text-red-500' : 'text-emerald-600'"
        >
          {{ formatCurrency(data.tax_due) }}
        </p>
      </div>
      <div class="col-span-2 sm:col-span-2">
        <p class="text-xs text-muted-foreground">Prejuízo a compensar (próx. meses)</p>
        <p
          class="font-semibold tabular-nums"
          :class="Number(data.accumulated_loss_after) > 0 ? 'text-amber-600' : 'text-muted-foreground'"
        >
          {{ formatCurrency(data.accumulated_loss_after) }}
        </p>
      </div>
    </div>

    <!-- Closed positions table -->
    <template v-if="open">
      <p v-if="!data.closed_positions.length" class="px-4 py-3 text-sm text-muted-foreground">
        Nenhuma posição fechada neste mês.
      </p>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-muted/40 border-b">
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Ticker</th>
              <th class="px-4 py-2 text-center font-medium text-muted-foreground">Dir.</th>
              <th class="px-4 py-2 text-right font-medium text-muted-foreground">Fechamento</th>
              <th class="px-4 py-2 text-right font-medium text-muted-foreground">Qtd</th>
              <th class="px-4 py-2 text-right font-medium text-muted-foreground">PM abertura</th>
              <th class="px-4 py-2 text-right font-medium text-muted-foreground">PM fechamento</th>
              <th class="px-4 py-2 text-right font-medium text-muted-foreground">Resultado</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(pos, i) in data.closed_positions"
              :key="i"
              class="border-b last:border-0 hover:bg-muted/20 transition-colors"
            >
              <td class="px-4 py-2 font-semibold font-mono">{{ pos.ticker }}</td>
              <td class="px-4 py-2 text-center">
                <Badge :variant="pos.direction === 'LONG' ? 'default' : 'outline'" class="text-xs">
                  {{ pos.direction === 'LONG' ? 'Long' : 'Short' }}
                </Badge>
              </td>
              <td class="px-4 py-2 text-right tabular-nums text-muted-foreground">
                {{ formatDate(pos.close_date) }}
              </td>
              <td class="px-4 py-2 text-right tabular-nums">
                {{ formatQty(pos.quantity) }}
              </td>
              <td class="px-4 py-2 text-right tabular-nums">
                <button
                  type="button"
                  class="tabular-nums text-muted-foreground underline decoration-dotted hover:text-foreground transition-colors"
                  title="Ver detalhamento do PM de abertura"
                  @click="$emit('pm-click', { ticker: pos.ticker, asOf: pos.open_date })"
                >{{ formatCurrency(pos.open_mean_price) }}</button>
              </td>
              <td class="px-4 py-2 text-right tabular-nums">
                <button
                  type="button"
                  class="tabular-nums text-muted-foreground underline decoration-dotted hover:text-foreground transition-colors"
                  title="Ver detalhamento do PM de fechamento"
                  @click="$emit('pm-click', { ticker: pos.ticker, asOf: pos.close_date })"
                >{{ formatCurrency(pos.close_price) }}</button>
              </td>
              <td
                class="px-4 py-2 text-right tabular-nums font-semibold"
                :class="pnlClass(pos.realized_pnl)"
              >
                {{ Number(pos.realized_pnl) >= 0 ? '+' : '' }}{{ formatCurrency(pos.realized_pnl) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </Card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatCurrency, formatDate, formatQty, pnlClass } from '@/utils/format.js'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'

const props = defineProps({ data: Object, title: String })
defineEmits(['pm-click'])

const open = ref(true)

const taxRateLabel = computed(() => (Number(props.data.tax_rate) * 100).toFixed(0) + '%')

</script>
