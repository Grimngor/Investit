import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
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
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-05-16T12:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('formats chart labels as DD/MM/YY', () => {
    const wrapper = mount(LineInvestedVsCurrent, {
      props: { timeSeries },
    })

    expect(chartLabels(wrapper)).toEqual(['01/01/24', '20/03/24', '15/04/24'])
  })

  it('keeps short ranges visible when data is sparse', async () => {
    const wrapper = mount(LineInvestedVsCurrent, {
      props: { timeSeries },
    })

    await wrapper.get('button').trigger('click')

    expect(chartLabels(wrapper)).toEqual(['16/04/24', '16/05/24'])
  })

  it('parses DD/MM/YYYY dates before falling back to browser date parsing', () => {
    const wrapper = mount(LineInvestedVsCurrent, {
      props: {
        timeSeries: [
          { date: '15/04/2024', invested_value: 100, current_value: 120 },
          { date: '16/05/2024', invested_value: 200, current_value: 240 },
        ],
      },
    })

    expect(chartLabels(wrapper)).toEqual(['15/04/24', '16/05/24'])
  })
})
