import { useEffect, useState } from 'react'

const API_BASE = '/api'

export function UploadScreen() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [transactions, setTransactions] = useState([])

  const loadTransactions = async () => {
    const res = await fetch(`${API_BASE}/transactions`)
    const data = await res.json()
    setTransactions(data)
  }

  useEffect(() => {
    loadTransactions().catch(() => setMessage('Failed to load transactions'))
  }, [])

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setMessage('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const data = await res.json()
      setMessage(
        `Upload successful (ID: ${data.id}). Parsed transactions: ${data.transactions_created}.`
      )
      setFile(null)
      await loadTransactions()
    } catch (err) {
      setMessage(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>Upload Screen</h2>
      <form onSubmit={onSubmit}>
        <input
          type="file"
          accept="application/pdf,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={loading || !file}>
          {loading ? 'Uploading...' : 'Upload SINACOR PDF'}
        </button>
      </form>
      {message ? <p>{message}</p> : null}

      <h3>Imported Transactions</h3>
      <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Ticker</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Upload ID</th>
          </tr>
        </thead>
        <tbody>
          {transactions.length === 0 ? (
            <tr>
              <td colSpan="6">No transactions found.</td>
            </tr>
          ) : (
            transactions.map((tx) => (
              <tr key={tx.id}>
                <td>{new Date(tx.trade_date).toLocaleString()}</td>
                <td>{tx.ticker}</td>
                <td>{tx.side}</td>
                <td>{tx.quantity}</td>
                <td>{tx.price}</td>
                <td>{tx.upload_id}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  )
}
