import { test, expect } from '@playwright/test'
import { authenticateTestUser } from './helpers/auth'

test.describe('Portfolio', () => {
  test.beforeEach(async ({ page, request }, testInfo) => {
    await authenticateTestUser(page, request, testInfo)
    await page.goto('/portfolio')
    await page.waitForURL(/\/portfolio/)
  })

  test('should display portfolio page', async ({ page }) => {
    await expect(page).toHaveTitle(/InvestIt/)
    await expect(page.locator('h1.page-title')).toHaveText(/My Portfolio/i)
    await expect(page.getByText(/total invested/i)).toBeVisible()
  })

  test('should add a manual order (Investment)', async ({ page }) => {
    // Fill the OrderForm
    await page.locator('input[type="date"]').fill('2024-01-01')
    await page.locator('input[placeholder*="IE00BYX5NX33"]').fill('IE00B4L5Y983')
    await page.locator('input[placeholder*="300.00"]').fill('500')
    await page.locator('input[placeholder*="24.624"]').fill('10')

    await page.getByRole('button', { name: /add order/i }).click()

    // Should show success toast and reflect in table
    // Table is in HoldingsTable.vue
    await expect(page.getByText(/IE00B4L5Y983/i).first()).toBeVisible()
    await expect(page.getByText(/500.00/).first()).toBeVisible()
  })

  test('should toggle sections', async ({ page }) => {
    // Add an order first to make section visible
    await page.locator('input[placeholder*="IE00BYX5NX33"]').fill('IE00B4L5Y983')
    await page.locator('input[placeholder*="300.00"]').fill('100')
    await page.locator('input[placeholder*="24.624"]').fill('1')
    await page.getByRole('button', { name: /add order/i }).click()

    const sectionButton = page.getByRole('button', { name: /index funds/i })
    await expect(sectionButton).toBeVisible()

    // Toggle
    await sectionButton.click()
    await expect(page.locator('.holdings-table')).not.toBeVisible() // Assuming class
  })
})
