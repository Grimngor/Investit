import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import OrderEditModal from '@/components/orders/OrderEditModal.vue'
import { useToastStore } from '@/stores/toast'
import { apiClient } from '@/services/api'

vi.mock('@/stores/toast', () => ({
	useToastStore: vi.fn(() => ({
		addToast: vi.fn()
	}))
}))

vi.mock('@/services/api', () => ({
	apiClient: {
		updateOrder: vi.fn()
	}
}))

describe('OrderEditModal', () => {
	const mockOrder = {
		id: '123',
		date: '25/10/2025',
		isin: 'IE00B4L5Y983',
		ticker: 'IWDA',
		shares: 10,
		amount_eur: 850.5,
		order_type: 'buy',
		status: 'Finalizada',
		notes: 'Test order'
	}

	beforeEach(() => {
		vi.clearAllMocks()
	})

	it('renders when isOpen is true', () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		expect(wrapper.find('h2').text()).toBe('Edit Order')
		expect(wrapper.isVisible()).toBe(true)
	})

	it('does not render when isOpen is false', () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: false
			}
		})

		expect(wrapper.find('.fixed').exists()).toBe(false)
	})

	it('populates form with order data', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		await wrapper.vm.$nextTick()

		const isinInput = wrapper.find('input[type="text"][maxlength="12"]')
		expect(isinInput.element.value).toBe('IE00B4L5Y983')
	})

	it('converts DD/MM/YYYY to YYYY-MM-DD for date input', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		await wrapper.vm.$nextTick()

		const dateInput = wrapper.find('input[type="date"]')
		expect(dateInput.element.value).toBe('2025-10-25')
	})

	it('calculates price per share correctly', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		await wrapper.vm.$nextTick()

		const priceDisplay = wrapper.find('.text-lg.font-semibold')
		expect(priceDisplay.text()).toBe('€85.0500')
	})

	it('emits close event when cancel button clicked', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		await wrapper.find('button[type="button"]').trigger('click')
		expect(wrapper.emitted('close')).toBeTruthy()
	})

	it('submits form and emits saved event on successful update', async () => {
		vi.mocked(apiClient.updateOrder).mockResolvedValue({ success: true })

		const wrapper = mount(OrderEditModal, {
			props: {
				order: mockOrder,
				isOpen: true
			}
		})

		await wrapper.find('form').trigger('submit.prevent')
		await wrapper.vm.$nextTick()
		await new Promise((resolve) => setTimeout(resolve, 10))

		expect(apiClient.updateOrder).toHaveBeenCalledWith(
			'123',
			expect.objectContaining({
				date: '25/10/2025',
				isin: 'IE00B4L5Y983'
			})
		)

		expect(wrapper.emitted('saved')).toBeTruthy()
		expect(wrapper.emitted('close')).toBeTruthy()
	})

	it('validates ISIN length', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: { ...mockOrder, isin: 'INVALID' },
				isOpen: true
			}
		})

		await wrapper.vm.$nextTick()

		const submitButton = wrapper.find('button[type="submit"]')
		expect(submitButton.attributes('disabled')).toBeDefined()
	})

	it('validates positive amount and shares', async () => {
		const wrapper = mount(OrderEditModal, {
			props: {
				order: { ...mockOrder, amount_eur: 0 },
				isOpen: true
			}
		})

		await wrapper.vm.$nextTick()

		const submitButton = wrapper.find('button[type="submit"]')
		expect(submitButton.attributes('disabled')).toBeDefined()
	})
})
