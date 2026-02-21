import { test, expect } from '@playwright/test'

test.describe('Portfolio', () => {
  test.beforeEach(async ({ page }) => {
    // Register and login before each test
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

    await page.waitForURL(/portfolio|\//)
  })

  test('should display portfolio page', async ({ page }) => {
    await page.goto('/portfolio')

    await expect(page).toHaveTitle(/Portfolio|InvestIt/)
    // Portfolio page should have add investment button or similar
    await expect(page.getByRole('button', { name: /add|new/i })).toBeVisible()
  })

  test('should add new investment', async ({ page }) => {
    await page.goto('/portfolio')

    // Click add investment button
    await page.click('button[aria-label="Add Investment"]')

    // Fill investment form
    await page.fill('input[placeholder*="AAPL"]', 'AAPL')
    await page.fill('input[type="number"]', '10') // quantity
    await page.fill('input[placeholder*="price"]', '150.00')

    await page.click('button[type="submit"]')

    // Should show the new investment in the list
    await expect(page.getByText(/AAPL/i)).toBeVisible()
  })

  test('should view portfolio data', async ({ page }) => {
    await page.goto('/portfolio')

    // Portfolio should display some data (charts, tables, etc.)
    // Even if empty, it should show the structure
    await expect(page.locator('table, canvas, svg')).toBeVisible()
  })

  test('should edit existing investment', async ({ page }) => {
    await page.goto('/portfolio')

    // Add an investment first
    await page.click('button[aria-label="Add Investment"]')
    await page.fill('input[placeholder*="AAPL"]', 'MSFT')
    await page.fill('input[type="number"]', '5')
    await page.fill('input[placeholder*="price"]', '200.00')
    await page.click('button[type="submit"]')

    // Edit the investment
    await page.click('button[aria-label="Edit"]')
    await page.fill('input[type="number"]', '10')
    await page.click('button[type="submit"]')

    // Should reflect the change
    await expect(page.getByText(/10/)).toBeVisible()
  })

  test('should delete investment', async ({ page }) => {
    await page.goto('/portfolio')

    // Add an investment first
    await page.click('button[aria-label="Add Investment"]')
    await page.fill('input[placeholder*="AAPL"]', 'TSLA')
    await page.fill('input[type="number"]', '3')
    await page.fill('input[placeholder*="price"]', '250.00')
    await page.click('button[type="submit"]')

    // Delete the investment
    await page.click('button[aria-label="Delete"]')
    await page.click('button[aria-label="Confirm"]')

    // Should no longer show the investment
    await expect(page.getByText(/TSLA/)).not.toBeVisible()
  })
})
