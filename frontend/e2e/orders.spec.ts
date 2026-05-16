import { test, expect } from '@playwright/test'
import { authenticateTestUser } from './helpers/auth'

test.describe('Orders', () => {
  test.beforeEach(async ({ page, request }, testInfo) => {
    await authenticateTestUser(page, request, testInfo)
    await page.goto('/portfolio')
    await page.waitForURL(/\/portfolio/)

    await page.locator('input[placeholder*="IE00BYX5NX33"]').fill('IE00B4L5Y983')
    await page.locator('input[placeholder*="300.00"]').fill('250')
    await page.locator('input[placeholder*="24.624"]').fill('5')
    await page.getByRole('button', { name: /add order/i }).click()

    const holdings = page.getByTestId('index-funds-holdings')
    const holdingsSurface = page.viewportSize()?.width && page.viewportSize()!.width < 1024
      ? holdings.locator('.lg\\:hidden')
      : holdings.locator('.hidden.lg\\:block')
    await expect(holdingsSurface.getByText(/IE00B4L5Y983/i).first()).toBeVisible()
  })

  test('shows the orders list on desktop and mobile layouts', async ({ page }) => {
    await page.goto('/orders')

    await expect(page.locator('h1.page-title')).toHaveText(/Orders/i)

    const viewport = page.viewportSize()
    if (viewport && viewport.width < 1024) {
      await expect(page.locator('table').first()).toBeHidden()
      await expect(page.locator('.lg\\:hidden').getByText('IE00B4L5Y983').first()).toBeVisible()
      await expect(page.getByRole('button', { name: /edit/i }).first()).toBeVisible()
    } else {
      await expect(page.locator('table').first()).toBeVisible()
      await expect(page.locator('table').first().getByText('IE00B4L5Y983')).toBeVisible()
    }
  })
})
