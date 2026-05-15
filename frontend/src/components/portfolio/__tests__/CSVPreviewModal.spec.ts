import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import axios from 'axios'
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
  const csvContent = `Fecha de la orden;ISIN;Importe estimado;Numero de participaciones;Estado
25/10/2025;IE00B4L5Y983;850.50;10;Finalizada
26/10/2025;LU0274208692;1200.00;5;Finalizada`

  const previewOrders = [
    {
      id: 'new-1',
      date: '2025-10-25',
      isin: 'IE00B4L5Y983',
      amount_eur: 850.5,
      shares: 10,
      order_type: 'buy',
      status: 'Finalizada',
      import_status: 'new',
      existing_order_id: null,
    },
    {
      id: 'new-2',
      date: '2025-10-26',
      isin: 'LU0274208692',
      amount_eur: 1200,
      shares: 5,
      order_type: 'buy',
      status: 'Finalizada',
      import_status: 'new',
      existing_order_id: null,
    },
  ]

  const mockedPost = vi.mocked(axios.post)

  function mockPreview(orders = previewOrders, errors: string[] = []) {
    const clonedOrders = orders.map((order) => ({ ...order }))
    mockedPost.mockResolvedValueOnce({
      data: {
        orders: clonedOrders,
        new_count: clonedOrders.filter((order) => order.import_status === 'new').length,
        skipped_count: clonedOrders.filter((order) => order.import_status === 'already_present').length,
        errors,
      },
    })
  }

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

  async function waitForPreview() {
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }

  beforeEach(() => {
    vi.clearAllMocks()
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

  it('loads preview rows from the backend preview endpoint', async () => {
    mockPreview()
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    expect(mockedPost.mock.calls[0][0]).toContain('/api/orders/import-csv/preview')
    expect(mockedPost.mock.calls[0][1]).toBeInstanceOf(FormData)
    expect(mockedPost.mock.calls[0][2]).toEqual(
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'multipart/form-data' }) }),
    )
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  })

  it('uses normalized backend dates in preview rows', async () => {
    mockPreview()
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const component = wrapper.vm as unknown as { parsedOrders: Array<{ date: string }> }
    expect(component.parsedOrders[0].date).toBe('2025-10-25')
  })

  it('allows inline editing of new order rows', async () => {
    mockPreview()
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const editButtons = wrapper.findAll('button[title="Edit"]')
    await editButtons[0].trigger('click')

    const isinInput = wrapper.find('input[type="text"][maxlength="12"]')
    expect(isinInput.exists()).toBe(true)
  })

  it('allows removing new orders from preview', async () => {
    mockPreview()
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const component = wrapper.vm as unknown as { parsedOrders: unknown[] }
    const initialCount = component.parsedOrders.length

    const removeButtons = wrapper.findAll('button[title="Remove"]')
    await removeButtons[0].trigger('click')
    await wrapper.vm.$nextTick()

    expect(component.parsedOrders.length).toBe(initialCount - 1)
  })

  it('renders Already present badges for duplicate rows', async () => {
    mockPreview([
      { ...previewOrders[0], import_status: 'already_present', existing_order_id: 'existing-1' },
      previewOrders[1],
    ])
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    expect(wrapper.text()).toContain('Already present')
    expect(wrapper.text()).toContain('New')
  })

  it('disables import button when all orders are already present', async () => {
    mockPreview(previewOrders.map((order) => ({ ...order, import_status: 'already_present', existing_order_id: `existing-${order.id}` })))
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const importButton = wrapper.findAll('button').find((btn) => btn.text().includes('Nothing New'))
    expect(importButton?.attributes('disabled')).toBeDefined()
  })

  it('imports only new rows from a mixed preview', async () => {
    mockPreview([{ ...previewOrders[0], import_status: 'already_present', existing_order_id: 'existing-1' }, previewOrders[1]])
    mockedPost.mockResolvedValueOnce({ data: { imported_count: 1, skipped_count: 0, rejected_count: 0 } })
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const importButton = wrapper.findAll('button').find((btn) => btn.text().includes('Import Orders'))
    await importButton?.trigger('click')
    await waitForPreview()

    expect(mockedPost).toHaveBeenCalledTimes(2)
    expect(mockedPost.mock.calls[1][0]).toContain('/api/orders/import-csv')
    const formData = mockedPost.mock.calls[1][1] as FormData
    const uploadedFile = formData.get('file') as Blob
    const uploadedCsv = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result))
      reader.onerror = () => reject(reader.error)
      reader.readAsText(uploadedFile)
    })
    expect(uploadedCsv).toContain('LU0274208692')
    expect(uploadedCsv).not.toContain('IE00B4L5Y983')
  })

  it('disables import button when no orders', async () => {
    const wrapper = mountModal({
      file: null,
      isOpen: true,
    })

    await wrapper.vm.$nextTick()

    const importButton = wrapper.findAll('button').find((btn) => btn.text().includes('Nothing New'))
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

  it('keeps valid preview rows when backend returns parse warnings', async () => {
    mockPreview(previewOrders, ['Row 2: Incomplete row'])
    const file = new File([csvContent], 'orders.csv', { type: 'text/csv' })

    const wrapper = mountModal({
      file,
      isOpen: true,
    })

    await waitForPreview()

    const component = wrapper.vm as unknown as { parsedOrders: unknown[] }
    expect(component.parsedOrders.length).toBe(2)
  })
})
