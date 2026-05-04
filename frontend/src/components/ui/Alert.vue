<script setup>
import { cn } from '@/utils/cn'

const props = defineProps({
  variant: { type: String, default: 'default' },
  class: { type: String, default: '' },
})

const variants = {
  default: 'bg-secondary text-secondary-foreground border-border',
  destructive: 'border-destructive/50 text-destructive bg-destructive/10',
  success: 'border-success/50 text-success bg-success/10',
}
</script>

<template>
  <div :class="cn('relative w-full rounded-lg border px-4 py-3 text-sm flex items-start gap-3', variants[variant] ?? variants.default, props.class)">
    <slot />
  </div>
</template>
