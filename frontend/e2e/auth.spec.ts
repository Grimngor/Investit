import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  function uniqueUsername(prefix: string, testInfo: { workerIndex: number }) {
    return `${prefix}${testInfo.workerIndex}${Date.now()}`
  }

  test('should display login page', async ({ page }) => {
    await page.goto('/login')

    await expect(page).toHaveTitle(/InvestIt/)
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible()
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
  })

  test('should register new user', async ({ page }, testInfo) => {
    await page.goto('/register')

    const timestamp = Date.now()
    const username = uniqueUsername('testuser', testInfo)

    await page.locator('#username').fill(username)
    await page.locator('#email').fill(`test${timestamp}@example.com`)
    await page.locator('#password').fill('TestPassword123!')

    await page.getByRole('button', { name: /register/i }).click()

    // Should redirect to login
    await page.waitForURL(/\/login/)
    await expect(page.getByRole('heading', { name: /login/i })).toBeVisible()
  })

  test('should login with valid credentials', async ({ page }, testInfo) => {
    // First register a test user
    await page.goto('/register')
    const timestamp = Date.now()
    const username = uniqueUsername('user', testInfo)
    const password = 'Password123'

    await page.locator('#username').fill(username)
    await page.locator('#email').fill(`user${timestamp}@test.com`)
    await page.locator('#password').fill(password)
    await page.getByRole('button', { name: /register/i }).click()
    await page.waitForURL(/\/login/)

    // Now login
    await page.locator('#username').fill(username)
    await page.locator('#password').fill(password)
    await page.getByRole('button', { name: /login/i }).click()

    // Should redirect to dashboard (based on LoginView.vue redirect)
    await page.waitForURL(/\/dashboard/)
    await expect(page.getByText(/total invested/i)).toBeVisible()
  })

  test('should show error on invalid login', async ({ page }) => {
    await page.goto('/login')

    await page.locator('#username').fill('nonexistentuser')
    await page.locator('#password').fill('wrongpassword')
    await page.getByRole('button', { name: /login/i }).click()

    // Should show error toast or message
    // Note: Depends on toast implementation, usually a text appears
    await expect(page.getByText(/incorrect|invalid|failed/i).first()).toBeVisible({ timeout: 15000 })
  })
})
