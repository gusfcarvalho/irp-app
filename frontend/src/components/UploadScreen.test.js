import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import UploadScreen from './UploadScreen.vue'

describe('UploadScreen', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads and renders empty transaction state', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    const wrapper = mount(UploadScreen)
    await flushPromises()

    expect(wrapper.text()).toContain('No transactions found.')
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

    const wrapper = mount(UploadScreen)
    await flushPromises()

    const input = wrapper.find('input[type="file"]')
    const file = new File(['%PDF-1.4'], 'nota.pdf', { type: 'application/pdf' })
    Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
    await input.trigger('change')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('Upload successful')
    expect(wrapper.text()).toContain('PETR4')
  })
})
