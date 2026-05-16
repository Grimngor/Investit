import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import LineInvestedVsCurrent from '../LineInvestedVsCurrent.vue'

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: {},
  LinearScale: {},
  PointElement: {},
  LineElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
  Filler: {},
}))

vi.mock('vue-chartjs', () => ({
  Line: {
    name: 'Line',
    props: ['data', 'options'],
    template: '<div data-testid="line-chart">{{ JSON.stringify(data.labels) }}</div>',
  },
}))

const timeSeries = [
  { date: '2024-01-01', invested_value: 100, current_value: 110 },
  { date: '2024-03-20', invested_value: 200, current_value: 220 },
  { date: '2024-04-15', invested_value: 300, current_value: 330 },
]

function chartLabels(wrapper: ReturnType<typeof mount>): string[] {
  return JSON.parse(wrapper.get('[data-testid="line-chart"]').text())
}

describe('LineInvestedVsCurrent', () => {
  it('formats chart labels as DD/MM/YY', () => {
    const wrapper = mount(LineInvestedVsCurrent, {
      props: { timeSeries },
    })

    expect(chartLabels(wrapper)).toEqual(['01/01/24', '20/03/24', '15/04/24'])
  })

  it('filters visible points with range buttons', async () => {
    const wrapper = mount(LineInvestedVsCurrent, {
      props: { timeSeries },
    })

    await wrapper.get('button').trigger('click')

    expect(chartLabels(wrapper)).toEqual(['20/03/24', '15/04/24'])
  })
})
