import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import PieAllocations from '../PieAllocations.vue'

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  ArcElement: {},
  Tooltip: {},
  Legend: {},
}))

vi.mock('vue-chartjs', () => ({
  Pie: {
    name: 'Pie',
    props: ['data', 'options'],
    template: '<div data-testid="pie" :data-options="JSON.stringify(options)">{{ JSON.stringify(data.labels) }}</div>',
  },
}))

function mountChart(allocations: Record<string, number>, type: 'instrument' | 'geography' | 'sector' | 'asset_type' = 'geography') {
  return mount(PieAllocations, {
    props: {
      allocations,
      type,
      title: 'By Geography',
    },
    global: {
      plugins: [createPinia()],
    },
  })
}

function labels(wrapper: ReturnType<typeof mountChart>): string[] {
  return JSON.parse(wrapper.get('[data-testid="pie"]').text())
}

describe('PieAllocations', () => {
  it('collapses smallest entries when there are more than 15 labels', () => {
    const allocations = Object.fromEntries(Array.from({ length: 16 }, (_, i) => [`Country ${i + 1}`, 16 - i]))

    const wrapper = mountChart(allocations)
    const chartLabels = labels(wrapper)

    expect(chartLabels).toHaveLength(15)
    expect(chartLabels).toContain('Others')
    expect(chartLabels).not.toContain('Country 16')
  })

  it('does not collapse entries when there are exactly 15 labels', () => {
    const allocations = Object.fromEntries(Array.from({ length: 15 }, (_, i) => [`Country ${i + 1}`, 15 - i]))

    const wrapper = mountChart(allocations)
    const chartLabels = labels(wrapper)

    expect(chartLabels).toHaveLength(15)
    expect(chartLabels).not.toContain('Others')
  })

  it('collapses Europe before overflow and keeps Europe out of Others', async () => {
    const allocations = {
      France: 1,
      Germany: 1,
      Spain: 1,
      ...Object.fromEntries(Array.from({ length: 15 }, (_, i) => [`Country ${i + 1}`, 100 - i])),
    }
    const wrapper = mountChart(allocations)

    await wrapper.get('button').trigger('click')
    const chartLabels = labels(wrapper)

    expect(chartLabels).toHaveLength(15)
    expect(chartLabels).toContain('Europe')
    expect(chartLabels).toContain('Others')
    expect(chartLabels).not.toContain('France')
    expect(chartLabels).not.toContain('Germany')
    expect(chartLabels).not.toContain('Spain')
  })

  it('hides legends by default and renders external legends when enabled', async () => {
    const wrapper = mountChart({ Spain: 70, France: 30 })

    expect(wrapper.find('.legend-panel').exists()).toBe(false)
    expect(JSON.parse(wrapper.get('[data-testid="pie"]').attributes('data-options')).plugins.legend.display).toBe(false)

    await wrapper.setProps({ showLegend: true })

    expect(wrapper.find('.legend-panel').exists()).toBe(true)
    expect(wrapper.text()).toContain('Spain')
    expect(wrapper.text()).toContain('70.0%')
  })
})
