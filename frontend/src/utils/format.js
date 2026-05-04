export const formatDate = (iso) => {
  if (!iso) return '—'
  const [y, m, d] = iso.split('T')[0].split('-')
  return `${d}/${m}/${y}`
}

export const formatDatetime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export const formatCurrency = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export const formatQty = (v) => {
  const n = Number(v)
  return Number.isInteger(n)
    ? n.toLocaleString('pt-BR')
    : n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 8 })
}

export const pnlClass = (v) =>
  Number(v) > 0 ? 'text-emerald-600' : Number(v) < 0 ? 'text-red-500' : ''

export const assetTypeClass = (type) => {
  switch (type) {
    case 'STOCK':      return 'text-blue-700 border-blue-200 bg-blue-50'
    case 'FII':        return 'text-emerald-700 border-emerald-200 bg-emerald-50'
    case 'BDR':        return 'text-purple-700 border-purple-200 bg-purple-50'
    case 'ETF_RV':     return 'text-indigo-700 border-indigo-200 bg-indigo-50'
    case 'SUBSCRICAO': return 'text-orange-700 border-orange-200 bg-orange-50'
    case 'ETF_RF':
    case 'RF_POS':
    case 'RF_PRE':     return 'text-slate-600 border-slate-200 bg-slate-50'
    case 'TD':         return 'text-cyan-700 border-cyan-200 bg-cyan-50'
    case 'CDB':
    case 'LCI':
    case 'LCA':
    case 'LCF':
    case 'LIG':        return 'text-teal-700 border-teal-200 bg-teal-50'
    case 'CRI':
    case 'CRA':        return 'text-amber-700 border-amber-200 bg-amber-50'
    case 'DEB':        return 'text-rose-700 border-rose-200 bg-rose-50'
    default:           return ''
  }
}
