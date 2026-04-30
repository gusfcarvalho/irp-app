import { createRouter, createWebHashHistory } from 'vue-router'
import ImportView from '@/views/ImportView.vue'
import NotasView from '@/views/NotasView.vue'
import PosicaoView from '@/views/PosicaoView.vue'
import ResultadosView from '@/views/ResultadosView.vue'
import TransacoesView from '@/views/TransacoesView.vue'

const routes = [
  { path: '/', redirect: '/import' },
  { path: '/import', component: ImportView },
  { path: '/notas', component: NotasView },
  { path: '/transacoes', component: TransacoesView },
  { path: '/posicao', component: PosicaoView },
  { path: '/resultados', component: ResultadosView },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
