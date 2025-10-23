import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AuthLayout from '../AuthLayout.vue'

describe('AuthLayout', () => {
  it('renders title and footer slots', () => {
    const wrapper = mount(AuthLayout, {
      slots: {
        title: 'My Title',
        default: '<form><input /></form>',
        footer: 'Footer content'
      }
    })
    expect(wrapper.text()).toContain('My Title')
    expect(wrapper.text()).toContain('Footer content')
    expect(wrapper.find('form').exists()).toBe(true)
  })
})
