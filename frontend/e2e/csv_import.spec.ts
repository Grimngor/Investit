import { test, expect } from '@playwright/test'
import fs from 'fs'
import { authenticateTestUser } from './helpers/auth'

test.describe('CSV Import', () => {
  test.beforeEach(async ({ page, request }, testInfo) => {
    await authenticateTestUser(page, request, testInfo)
    await page.goto('/portfolio')
  })

  test('should import orders from CSV', async ({ page }, testInfo) => {
    // Create a dummy CSV file for testing
    const csvContent =
      'Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado\n' +
      '01/01/2024;IE00B4L5Y983;1000.50;10.5;Finalizada'
    const csvPath = testInfo.outputPath('test-orders.csv')
    fs.writeFileSync(csvPath, csvContent)

    // Upload the file
    // The input is hidden, but we can use setInputFiles on the ref
    // Or we can just use the file chooser
    const fileChooserPromise = page.waitForEvent('filechooser')
    await page.locator('.border-dashed').click() // Drop zone
    const fileChooser = await fileChooserPromise
    await fileChooser.setFiles(csvPath)

    // Verify file name appears
    await expect(page.getByText('test-orders.csv')).toBeVisible()

    // Click Preview & Import
    await page.getByRole('button', { name: /preview & import/i }).click()

    // Verify Modal contents
    await expect(page.getByRole('heading', { name: /preview & edit csv/i })).toBeVisible()
    await expect(page.getByText('IE00B4L5Y983')).toBeVisible()

    // Click Import
    await page.getByRole('button', { name: /import orders/i }).click()

    // Verify success and page update
    await expect(page.getByText(/successfully imported/i)).toBeVisible({ timeout: 15000 })
    const holdings = page.getByTestId('index-funds-holdings')
    const holdingsSurface = page.viewportSize()?.width && page.viewportSize()!.width < 1024
      ? holdings.locator('.lg\\:hidden')
      : holdings.locator('.hidden.lg\\:block')

    await expect(holdingsSurface.getByText('IE00B4L5Y983').first()).toBeVisible()
  })
})
