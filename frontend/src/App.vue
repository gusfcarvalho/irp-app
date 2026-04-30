<template>
  <div class="min-h-screen bg-background">
    <header class="border-b bg-card sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-6 h-14 flex items-center gap-4">
        <div class="flex items-center gap-2 shrink-0">
          <div class="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
            <FileText class="h-4 w-4 text-primary-foreground" />
          </div>
          <span class="font-semibold text-base tracking-tight">SINACOR</span>
          <span class="text-muted-foreground text-sm hidden sm:inline">IRPF · BTG</span>
        </div>

        <nav class="flex items-center gap-1 ml-2">
          <RouterLink
            to="/import"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="route.path === '/import'
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
          >
            <Upload class="h-3.5 w-3.5" />
            Importar
          </RouterLink>
          <RouterLink
            to="/notas"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="route.path === '/notas'
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
          >
            <BookOpen class="h-3.5 w-3.5" />
            Notas
          </RouterLink>
          <RouterLink
            to="/transacoes"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="route.path === '/transacoes'
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
          >
            <PenLine class="h-3.5 w-3.5" />
            Manual
          </RouterLink>
          <RouterLink
            to="/posicao"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="route.path === '/posicao'
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
          >
            <BarChart2 class="h-3.5 w-3.5" />
            Posição
          </RouterLink>
          <RouterLink
            to="/resultados"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="route.path === '/resultados'
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
          >
            <TrendingUp class="h-3.5 w-3.5" />
            Resultados
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-6 py-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRoute, RouterLink, RouterView } from 'vue-router'
import { BarChart2, BookOpen, FileText, PenLine, TrendingUp, Upload } from 'lucide-vue-next'

const route = useRoute()
</script>
