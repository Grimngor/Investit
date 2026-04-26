import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

test.describe('CSV Import', () => {
  let username = ''
  let password = 'Password123'

  test.beforeEach(async ({ page }) => {
    // Register and login before each test
    await page.goto('/register')
    const timestamp = Date.now()
    username = `user${timestamp}`

    await page.locator('#username').fill(username)
    await page.locator('#email').fill(`test${timestamp}@example.com`)
    await page.locator('#password').fill(password)
    await page.getByRole('button', { name: /register/i }).click()

    await page.waitForURL(/\/login/)
    await page.locator('#username').fill(username)
    await page.locator('#password').fill(password)
    await page.getByRole('button', { name: /login/i }).click()

    await page.waitForURL(/\/dashboard/)
    await page.goto('/portfolio')
  })

  test('should import orders from CSV', async ({ page }) => {
    // Create a dummy CSV file for testing
    const csvContent = 'Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado\n' +
                       '01/01/2024;IE00B4L5Y983;1000.50;10.5;Finalizada'
    const csvPath = path.resolve('test-orders.csv')
    fs.writeFileSync(csvPath, csvContent)

    // Upload the file
    // The input is hidden, but we can use setInputFiles on the ref
    // Or we can just use the file chooser
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('.border-dashed').click(); // Drop zone
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(csvPath);

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
    await expect(page.getByText('IE00B4L5Y983').first()).toBeVisible()

    // Cleanup
    fs.unlinkSync(csvPath)
  })
})
