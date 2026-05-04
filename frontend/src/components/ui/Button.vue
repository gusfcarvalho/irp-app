<script setup>
import { cn } from '@/utils/cn'

const props = defineProps({
  variant: { type: String, default: 'default' },
  size: { type: String, default: 'default' },
  disabled: { type: Boolean, default: false },
  class: { type: String, default: '' },
})

const base = 'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50'

const variants = {
  default: 'bg-primary text-primary-foreground shadow hover:opacity-90',
  destructive: 'bg-destructive text-destructive-foreground shadow-sm hover:opacity-90',
  outline: 'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground',
  secondary: 'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  link: 'text-primary underline-offset-4 hover:underline',
}

const sizes = {
  default: 'h-9 px-4 py-2',
  sm: 'h-8 rounded-md px-3 text-xs',
  lg: 'h-10 rounded-md px-8',
  icon: 'h-9 w-9',
}

const classes = cn(base, variants[props.variant] ?? variants.default, sizes[props.size] ?? sizes.default, props.class)
</script>

<template>
  <button :class="classes" :disabled="disabled" v-bind="$attrs">
    <slot />
  </button>
</template>
