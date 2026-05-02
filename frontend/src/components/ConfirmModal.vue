<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="$emit('cancel')"
    >
      <div class="bg-background rounded-xl border border-border shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="font-semibold text-foreground mb-2">{{ title }}</h3>
        <p v-if="message" class="text-sm text-muted-foreground mb-6">{{ message }}</p>
        <slot />
        <div class="flex justify-end gap-2 mt-6">
          <button
            type="button"
            class="px-4 py-2 text-sm rounded-lg border border-border hover:bg-muted transition-colors"
            @click="$emit('cancel')"
          >
            {{ cancelLabel }}
          </button>
          <button
            type="button"
            class="px-4 py-2 text-sm rounded-lg font-medium transition-colors"
            :class="destructive
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-primary hover:bg-primary/90 text-primary-foreground'"
            @click="$emit('confirm')"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, required: true },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirmar' },
  cancelLabel: { type: String, default: 'Cancelar' },
  destructive: { type: Boolean, default: false },
})

defineEmits(['confirm', 'cancel'])
</script>
