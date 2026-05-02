import { createRouter, createWebHashHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import ImportView from '@/views/ImportView.vue'
import ImpostosView from '@/views/ImpostosView.vue'
import NotasView from '@/views/NotasView.vue'
import PosicaoView from '@/views/PosicaoView.vue'
import ResultadosView from '@/views/ResultadosView.vue'
import TickersView from '@/views/TickersView.vue'
import TransacoesView from '@/views/TransacoesView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: DashboardView },
  { path: '/import', component: ImportView },
  { path: '/notas', component: NotasView },
  { path: '/transacoes', component: TransacoesView },
  { path: '/posicao', component: PosicaoView },
  { path: '/resultados', component: ResultadosView },
  { path: '/impostos', component: ImpostosView },
  { path: '/tickers', component: TickersView },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
