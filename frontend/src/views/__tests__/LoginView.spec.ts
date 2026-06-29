import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginView from '../LoginView.vue'

const push = vi.fn()
const replace = vi.fn()
const fetchAuthModes = vi.fn()
const login = vi.fn()
const trustedProxyLogin = vi.fn()
const startGoogleLogin = vi.fn()
const completeExternalLogin = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace }),
  useRoute: () => ({ path: '/login', query: {}, hash: '' }),
  RouterLink: {
    name: 'RouterLink',
    template: '<a><slot /></a>',
  },
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    error: null,
    trustedProxyAvailable: true,
    googleAvailable: false,
    fetchAuthModes,
    login,
    trustedProxyLogin,
    startGoogleLogin,
    completeExternalLogin,
  }),
}))

vi.mock('@/stores/toast', () => ({
  useToastStore: () => ({
    addToast: vi.fn(),
  }),
}))

function mountLoginView() {
  return mount(LoginView, {
    global: {
      stubs: {
        AuthLayout: {
          template: '<section><slot name="title" /><slot /><slot name="footer" /></section>',
        },
        'router-link': {
          template: '<a><slot /></a>',
        },
      },
    },
  })
}

describe('LoginView', () => {
  beforeEach(() => {
    push.mockReset()
    replace.mockReset()
    fetchAuthModes.mockReset()
    login.mockReset()
    trustedProxyLogin.mockReset()
    startGoogleLogin.mockReset()
    completeExternalLogin.mockReset()
  })

  it('loads auth modes and shows trusted proxy login when available', () => {
    const wrapper = mountLoginView()

    expect(fetchAuthModes).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Continue with Tailscale')
  })

  it('routes to dashboard after trusted proxy login succeeds', async () => {
    trustedProxyLogin.mockResolvedValue(true)
    const wrapper = mountLoginView()

    await wrapper.get('button[type="button"]').trigger('click')

    expect(trustedProxyLogin).toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith('/dashboard')
  })
})
