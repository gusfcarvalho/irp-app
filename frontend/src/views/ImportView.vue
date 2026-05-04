<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Importar</h1>
      <p class="text-muted-foreground text-sm mt-1">
        Importe transações a partir de arquivos da B3 ou notas de corretagem.
      </p>
    </div>

    <!-- Tab bar -->
    <div class="flex gap-1 border-b">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px"
        :class="activeTab === tab.id
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <UploadScreen v-if="activeTab === 'nota'" />
    <B3PosicaoUpload v-else-if="activeTab === 'posicao'" />
    <B3MovimentacaoUpload v-else-if="activeTab === 'movimentacao'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UploadScreen from '@/components/UploadScreen.vue'
import B3PosicaoUpload from '@/components/B3PosicaoUpload.vue'
import B3MovimentacaoUpload from '@/components/B3MovimentacaoUpload.vue'

const tabs = [
  { id: 'nota', label: 'Nota de Corretagem' },
  { id: 'posicao', label: 'Posição B3' },
  { id: 'movimentacao', label: 'Movimentações B3' },
]

const activeTab = ref('nota')
</script>
