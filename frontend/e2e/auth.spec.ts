import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveTitle(/InvestIt/)
    await expect(page.getByRole('button', { name: /login/i })).toBeVisible()
  })

  test('should register new user', async ({ page }) => {
    await page.goto('/register')

    const timestamp = Date.now()
    await page.fill('input[type="text"]', `testuser${timestamp}`)
    await page.fill('input[type="email"]', `test${timestamp}@example.com`)
    await page.fill('input[type="password"]', 'TestPassword123!')

    await page.click('button[type="submit"]')

    // Should redirect to login or home
    await page.waitForURL(/login|\//)
  })

  test('should login with valid credentials', async ({ page }) => {
    // First register a test user
    await page.goto('/register')
    const timestamp = Date.now()
    const username = `testuser${timestamp}`
    const password = 'TestPassword123!'

    await page.fill('input[type="text"]', username)
    await page.fill('input[type="email"]', `test${timestamp}@example.com`)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')

    // Now login
    await page.goto('/login')
    await page.fill('input[type="text"]', username)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')

    // Should redirect to home or portfolio
    await page.waitForURL(/portfolio|\//)
  })

  test('should show error on invalid login', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[type="text"]', 'invaliduser')
    await page.fill('input[type="password"]', 'invalidpassword')
    await page.click('button[type="submit"]')

    // Should show error message (exact text depends on implementation)
    await expect(page.getByText(/invalid|error|incorrect/i)).toBeVisible()
  })

  test('should logout', async ({ page }) => {
    // First login
    await page.goto('/register')
    const timestamp = Date.now()
    const username = `testuser${timestamp}`
    const password = 'TestPassword123!'

    await page.fill('input[type="text"]', username)
    await page.fill('input[type="email"]', `test${timestamp}@example.com`)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')

    await page.goto('/login')
    await page.fill('input[type="text"]', username)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')

    // Now logout
    await page.click('button[aria-label="Logout"]')

    // Should redirect to login or home
    await page.waitForURL(/login|\//)
  })
})
