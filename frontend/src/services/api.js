const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let detail = `Erro ${res.status}`
    try { detail = (await res.json()).detail ?? detail } catch {}
    throw new Error(detail)
  }
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

function json(method, body) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

// ── Uploads & Transactions ────────────────────────────────────────────────────
export const getUploads = () => request('/uploads')
export const getTransactions = () => request('/transactions')
export const uploadFile = (formData) =>
  request('/upload', { method: 'POST', body: formData })
export const deleteUpload = (id) =>
  request(`/uploads/${id}`, { method: 'DELETE' })

// ── B3 Imports ────────────────────────────────────────────────────────────────
export const importB3Posicao = (formData) =>
  request('/b3/posicao', { method: 'POST', body: formData })
export const importB3Movimentacao = (formData) =>
  request('/b3/movimentacao', { method: 'POST', body: formData })

// ── Positions ─────────────────────────────────────────────────────────────────
export const getPositions = (asOf) =>
  request('/positions' + (asOf ? `?as_of=${asOf}` : ''))
export const recalculatePositions = () =>
  request('/positions/recalculate', { method: 'POST' })
export const getPositionBreakdown = (ticker, asOf) =>
  request(`/positions/${encodeURIComponent(ticker)}/breakdown` + (asOf ? `?as_of=${asOf}` : ''))
export const updatePositionOverride = (ticker, data) =>
  request(`/positions/${encodeURIComponent(ticker)}`, json('PATCH', data))
export const deletePositionOverride = (ticker) =>
  request(`/positions/${encodeURIComponent(ticker)}/override`, { method: 'DELETE' })

// ── Closed Positions ──────────────────────────────────────────────────────────
export const getClosedPositions = (fromDate, toDate) => {
  const params = new URLSearchParams()
  if (fromDate) params.set('from_date', fromDate)
  if (toDate) params.set('to_date', toDate)
  const qs = params.toString()
  return request('/closed-positions' + (qs ? `?${qs}` : ''))
}

// ── Manual Transactions ───────────────────────────────────────────────────────
export const getManualTransactions = () => request('/manual-transactions')
export const createManualTransaction = (data) =>
  request('/manual-transactions', json('POST', data))
export const updateManualTransaction = (id, data) =>
  request(`/manual-transactions/${id}`, json('PUT', data))
export const deleteManualTransaction = (id) =>
  request(`/manual-transactions/${id}`, { method: 'DELETE' })

// ── Ticker Classifications ────────────────────────────────────────────────────
export const getTickerClassifications = () => request('/ticker-classifications')
export const setTickerClassification = (ticker, assetType) =>
  request(`/ticker-classifications/${encodeURIComponent(ticker)}`, json('PUT', { asset_type: assetType }))

// ── Ticker Aliases ────────────────────────────────────────────────────────────
export const getTickerAliases = () => request('/ticker-aliases')
export const createTickerAlias = (data) =>
  request('/ticker-aliases', json('POST', data))
export const updateTickerAlias = (rawName, data) =>
  request(`/ticker-aliases/${encodeURIComponent(rawName)}`, json('PATCH', data))
export const deleteTickerAlias = (rawName) =>
  request(`/ticker-aliases/${encodeURIComponent(rawName)}`, { method: 'DELETE' })

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getPortfolioHistory = (mode = 'monthly') => request(`/portfolio-history?mode=${mode}`)

// ── Quotes ───────────────────────────────────────────────────────────────────
// Both return QuoteOut[]: [{ticker, date, close_price, fetched_at}, ...]
export const getQuotes = (tickers) =>
  request(`/quotes?${tickers.map(t => `tickers=${encodeURIComponent(t)}`).join('&')}`)
export const refreshQuotes = (tickers = [], full = false) => {
  const params = new URLSearchParams()
  if (full) params.set('full', 'true')
  tickers.forEach(t => params.append('tickers', t))
  const qs = params.toString()
  return request(`/quotes/refresh${qs ? `?${qs}` : ''}`, { method: 'POST' })
}

// ── Tax ───────────────────────────────────────────────────────────────────────
export const getTaxReport = (month) => request(`/tax?month=${month}`)
export const calculateTaxReport = (month) => request(`/tax/calculate?month=${month}`, { method: 'POST' })
export const upsertTaxPayment = (month, data) =>
  request(`/tax-payments/${month}`, json('PUT', data))
export const deleteTaxPayment = (month) =>
  request(`/tax-payments/${month}`, { method: 'DELETE' })
