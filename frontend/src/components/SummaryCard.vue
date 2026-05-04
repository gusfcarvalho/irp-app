<template>
  <div class="rounded-xl border border-border bg-card p-4">
    <p class="text-xs text-muted-foreground font-medium uppercase tracking-wide">{{ label }}</p>
    <p class="text-xl font-bold mt-0.5 tabular-nums" :class="valueClass">
      <slot>{{ value }}</slot>
    </p>
    <p v-if="sub" class="text-xs text-muted-foreground mt-0.5">{{ sub }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  sub: { type: String, default: '' },
  valueClass: { type: String, default: '' },
})
</script>
