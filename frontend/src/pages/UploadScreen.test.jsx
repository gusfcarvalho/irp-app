import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { UploadScreen } from './UploadScreen'

describe('UploadScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads and renders empty transaction state', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    render(<UploadScreen />)

    expect(await screen.findByText('No transactions found.')).toBeInTheDocument()
  })

  it('uploads a pdf and refreshes transactions', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'abc', transactions_created: 1 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: 'tx-1',
            upload_id: 'abc',
            ticker: 'PETR4',
            trade_date: '2026-04-01',
            side: 'BUY',
            quantity: 100,
            price: '30.15',
            market_type: 'SWING',
          },
        ],
      })

    const { container } = render(<UploadScreen />)

    const input = container.querySelector('input[type="file"]')
    expect(input).toBeTruthy()
    const file = new File(['%PDF-1.4'], 'nota.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: /upload sinacor pdf/i }))

    await waitFor(() => {
      expect(screen.getByText(/Upload successful/)).toBeInTheDocument()
      expect(screen.getByText('PETR4')).toBeInTheDocument()
    })

    expect(global.fetch).toHaveBeenCalledWith('/api/upload', expect.any(Object))
  })
})
