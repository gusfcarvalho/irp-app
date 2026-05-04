<script setup>
import { cn } from '@/utils/cn'

const props = defineProps({
  variant: { type: String, default: 'default' },
  class: { type: String, default: '' },
})

const variants = {
  default: 'bg-primary text-primary-foreground',
  secondary: 'bg-secondary text-secondary-foreground',
  destructive: 'bg-destructive text-destructive-foreground',
  outline: 'border border-border text-foreground',
  success: 'bg-success text-success-foreground',
}
</script>

<template>
  <span :class="cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors', variants[variant] ?? variants.default, props.class)">
    <slot />
  </span>
</template>
