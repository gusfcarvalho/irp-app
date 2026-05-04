import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import TransacoesView from './TransacoesView.vue'

describe('TransacoesView', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads and renders empty transaction state', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    const wrapper = mount(TransacoesView)
    await flushPromises()

    expect(wrapper.text()).toContain('Nenhuma transacao manual cadastrada')
  })

  it('renders list of manual transactions', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: 'tx-1',
          ticker: 'PETR4',
          trade_date: '2026-04-01',
          transaction_type: 'BUY',
          quantity: 100,
          price: '30.50',
          ratio_from: null,
          ratio_to: null,
          created_at: '2026-04-01T10:00:00Z',
        },
        {
          id: 'tx-2',
          ticker: 'ITUB4',
          trade_date: '2026-04-02',
          transaction_type: 'SPLITTING',
          quantity: null,
          price: null,
          ratio_from: 1,
          ratio_to: 2,
          created_at: '2026-04-02T10:00:00Z',
        },
      ],
    })

    const wrapper = mount(TransacoesView)
    await flushPromises()

    expect(wrapper.text()).toContain('PETR4')
    expect(wrapper.text()).toContain('ITUB4')
    expect(wrapper.text()).toContain('Compra')
    expect(wrapper.text()).toContain('Desdobramento')
  })

  it('opens create form when button clicked', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    const wrapper = mount(TransacoesView)
    await flushPromises()

    await wrapper.find('button').trigger('click')

    expect(wrapper.text()).toContain('Nova Transacao')
    expect(wrapper.find('select').exists()).toBe(true)
  })

  it('creates a new BUY transaction', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'tx-new',
          ticker: 'VALE3',
          trade_date: '2026-04-05',
          transaction_type: 'BUY',
          quantity: 50,
          price: '55.00',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: 'tx-new',
            ticker: 'VALE3',
            trade_date: '2026-04-05',
            transaction_type: 'BUY',
            quantity: 50,
            price: '55.00',
            ratio_from: null,
            ratio_to: null,
            created_at: '2026-04-05T10:00:00Z',
          },
        ],
      })

    const wrapper = mount(TransacoesView)
    await flushPromises()

    // Open create form
    await wrapper.find('button').trigger('click')

    // Fill form
    const inputs = wrapper.findAll('input')
    const tickerInput = inputs.find(i => i.attributes('placeholder') === 'PETR4')
    await tickerInput.setValue('VALE3')

    const qtyInput = inputs.find(i => i.attributes('placeholder') === '100')
    await qtyInput.setValue(50)

    const priceInput = inputs.find(i => i.attributes('placeholder') === '30.50')
    await priceInput.setValue('55.00')

    // Submit
    const saveBtn = wrapper.findAll('button').find(b => b.text() === 'Salvar')
    await saveBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('VALE3')
  })

  it('shows transaction type badge with correct variant', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: 'tx-1',
          ticker: 'PETR4',
          trade_date: '2026-04-01',
          transaction_type: 'SELL',
          quantity: 100,
          price: '35.00',
          ratio_from: null,
          ratio_to: null,
          created_at: '2026-04-01T10:00:00Z',
        },
      ],
    })

    const wrapper = mount(TransacoesView)
    await flushPromises()

    expect(wrapper.text()).toContain('Venda')
  })
})
