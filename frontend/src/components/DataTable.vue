<template>
  <div class="overflow-x-auto rounded-lg border border-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border bg-muted/50">
          <th
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-3 text-left font-medium text-muted-foreground whitespace-nowrap"
            :class="[col.align === 'right' ? 'text-right' : '', col.headerClass]"
          >
            <button
              v-if="col.sortable"
              class="inline-flex items-center gap-1 hover:text-foreground transition-colors"
              @click="$emit('sort', col.key)"
            >
              {{ col.label }}
              <component
                :is="sortIcon(col.key)"
                class="h-3.5 w-3.5"
                :class="sortBy === col.key ? 'text-foreground' : 'text-muted-foreground/50'"
              />
            </button>
            <span v-else>{{ col.label }}</span>
          </th>
          <th v-if="$slots.actions" class="px-4 py-3" />
        </tr>
      </thead>
      <tbody>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-12 text-center text-muted-foreground">
            <slot name="empty">
              <span>Nenhum registro encontrado.</span>
            </slot>
          </td>
        </tr>
        <tr
          v-for="(row, i) in rows"
          :key="rowKey ? row[rowKey] : i"
          class="border-b border-border last:border-0 transition-colors"
          :class="rowClass ? rowClass(row) : 'hover:bg-muted/30'"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-2.5"
            :class="[col.align === 'right' ? 'text-right tabular-nums' : '', col.cellClass]"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ col.format ? col.format(row[col.key], row) : row[col.key] }}
            </slot>
          </td>
          <td v-if="$slots.actions" class="px-4 py-2 text-right">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-vue-next'

const props = defineProps({
  columns: {
    type: Array,
    required: true,
    // [{ key, label, align?: 'right', sortable?: true, format?: fn, headerClass?, cellClass? }]
  },
  rows: { type: Array, required: true },
  rowKey: { type: String, default: null },
  sortBy: { type: String, default: null },
  sortDir: { type: String, default: 'asc' },
  rowClass: { type: Function, default: null },
})

defineEmits(['sort'])

const sortIcon = (field) => {
  if (props.sortBy !== field) return ArrowUpDown
  return props.sortDir === 'asc' ? ArrowUp : ArrowDown
}
</script>
