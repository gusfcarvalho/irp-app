<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="$emit('close')"
    >
      <div class="bg-background rounded-xl border border-border shadow-xl w-full mx-4" :class="widthClass">
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border">
          <h3 class="font-semibold text-foreground">{{ title }}</h3>
          <button
            type="button"
            class="p-1 rounded hover:bg-muted text-muted-foreground transition-colors"
            @click="$emit('close')"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <form class="px-6 py-4 overflow-y-auto max-h-[80vh]" @submit.prevent="$emit('submit')">
          <slot />

          <div v-if="error" class="mt-4 text-sm text-red-500">{{ error }}</div>

          <div class="flex justify-end gap-2 mt-6">
            <button
              type="button"
              class="px-4 py-2 text-sm rounded-lg border border-border hover:bg-muted transition-colors"
              @click="$emit('close')"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 text-sm rounded-lg font-medium bg-primary hover:bg-primary/90 text-primary-foreground transition-colors disabled:opacity-50"
            >
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin inline mr-1" />
              {{ saveLabel }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { Loader2, X } from 'lucide-vue-next'

defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, required: true },
  saveLabel: { type: String, default: 'Salvar' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
  widthClass: { type: String, default: 'max-w-lg' },
})

defineEmits(['close', 'submit'])
</script>
