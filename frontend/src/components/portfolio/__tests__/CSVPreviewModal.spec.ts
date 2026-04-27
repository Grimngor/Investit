import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CSVPreviewModal from '@/components/portfolio/CSVPreviewModal.vue'

vi.mock('@/stores/toast', () => ({
  useToastStore: vi.fn(() => ({
    addToast: vi.fn(),
  })),
}))

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('CSVPreviewModal', () => {
  const csvContent = `Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado
25/10/2025;IE00B4L5Y983;850.50;10;Finalizada
26/10/2025;LU0274208692;1200.00;5;Finalizada`

  function mountModal(props: { file: File | null; isOpen: boolean }) {
    return mount(CSVPreviewModal, {
      props,
      global: {
        stubs: {
          Teleport: true,
        },
      },
    })
  }

  async function waitForCsvParse() {
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }

  beforeEach(() => {
    vi.clearAllMocks()
    global.File.prototype.text = vi.fn(async function (this: File) {
      return csvContent
    })
  })

  it('renders when isOpen is true', () => {
    const wrapper = mountModal({
      file: null,
      isOpen: true,
    })

    expect(wrapper.find('h2').text()).toBe('Preview & Edit CSV Import')
    expect(wrapper.isVisible()).toBe(true)
  })

  it('does not render when isOpen is false', () => {
    const wrapper = mountModal({
      file: null,
      isOpen: false,
    })

    expect(wrapper.find('.fixed').exists()).toBe(false)
  })

  it('parses CSV file with semicolon delimiter', async () => {
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForCsvParse()

    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBeGreaterThan(0)
  })

  it('converts DD/MM/YYYY dates to YYYY-MM-DD internally', async () => {
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForCsvParse()

    const component = wrapper.vm as unknown as { parsedOrders: Array<{ date: string }> }
    expect(component.parsedOrders[0].date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('allows inline editing of order rows', async () => {
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForCsvParse()

    const editButtons = wrapper.findAll('button[title="Edit"]')
    await editButtons[0].trigger('click')

    const isinInput = wrapper.find('input[type="text"][maxlength="12"]')
    expect(isinInput.exists()).toBe(true)
  })

  it('allows removing orders from preview', async () => {
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForCsvParse()

    const component = wrapper.vm as unknown as { parsedOrders: unknown[] }
    const initialCount = component.parsedOrders.length

    const removeButtons = wrapper.findAll('button[title="Remove"]')
    await removeButtons[0].trigger('click')
    await wrapper.vm.$nextTick()

    expect(component.parsedOrders.length).toBe(initialCount - 1)
  })

  it('disables import button when no orders', async () => {
    const wrapper = mountModal({
      file: null,
      isOpen: true,
    })

    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const importButton = buttons.find((btn) => btn.text().includes('Import'))
    expect(importButton?.attributes('disabled')).toBeDefined()
  })

  it('emits close event when cancel clicked', async () => {
    const wrapper = mountModal({
      file: null,
      isOpen: true,
    })

    const cancelButton = wrapper.findAll('button').find((btn) => btn.text() === 'Cancel')
    await cancelButton?.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('handles malformed CSV rows gracefully', async () => {
    const malformedCsv = `Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado
25/10/2025;IE00B4L5Y983;850.50;10;Finalizada
INVALID_ROW
26/10/2025;LU0274208692;1200.00;5;Finalizada`

    global.File.prototype.text = vi.fn(async function (this: File) {
      return malformedCsv
    })
    const file = new File([malformedCsv], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForCsvParse()

    const component = wrapper.vm as unknown as { parsedOrders: unknown[] }
    expect(component.parsedOrders.length).toBe(2)
  })
})
