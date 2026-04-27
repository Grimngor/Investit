import type { APIRequestContext, Page, TestInfo } from '@playwright/test'

const API_BASE_URL = process.env.PLAYWRIGHT_API_URL || 'http://127.0.0.1:8000'
const PASSWORD = 'Password123'

export async function authenticateTestUser(page: Page, request: APIRequestContext, testInfo: TestInfo) {
  const safeProjectName = testInfo.project.name.replace(/[^a-z0-9]/gi, '').toLowerCase()
  const username = `user${safeProjectName}${testInfo.workerIndex}${Date.now()}`
  const email = `${username}@example.com`

  const registerResponse = await request.post(`${API_BASE_URL}/api/auth/register`, {
    data: {
      username,
      email,
      password: PASSWORD,
    },
  })

  if (!registerResponse.ok()) {
    throw new Error(`Registration failed for ${username}: ${registerResponse.status()} ${await registerResponse.text()}`)
  }

  const loginResponse = await request.post(`${API_BASE_URL}/api/auth/login`, {
    form: {
      username,
      password: PASSWORD,
    },
  })

  if (!loginResponse.ok()) {
    throw new Error(`Login failed for ${username}: ${loginResponse.status()} ${await loginResponse.text()}`)
  }

  const tokenData = await loginResponse.json()
  const token = tokenData.access_token

  await page.addInitScript(
    ({ storedToken, storedUsername, storedEmail }) => {
      window.localStorage.setItem('token', storedToken)
      window.localStorage.setItem(
        'user',
        JSON.stringify({
          username: storedUsername,
          email: storedEmail,
          disabled: false,
        }),
      )
    },
    { storedToken: token, storedUsername: username, storedEmail: email },
  )

  return { username, password: PASSWORD, token }
}
