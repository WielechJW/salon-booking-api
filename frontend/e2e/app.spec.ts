import { expect, test, type Page } from '@playwright/test'
import { TZDate } from '@date-fns/tz'
import { addDays, format } from 'date-fns'

const tomorrow = format(addDays(new TZDate(Date.now(), 'Europe/Warsaw'), 1), 'yyyy-MM-dd')
const later = format(addDays(new TZDate(Date.now(), 'Europe/Warsaw'), 3), 'yyyy-MM-dd')

async function login(page: Page, email: string, next = '/account') {
  await page.goto(`/login?next=${encodeURIComponent(next)}`)
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Hasło', { exact: true }).fill('TestPassword123!')
  await page.getByRole('button', { name: 'Zaloguj się', exact: true }).click()
  await expect(page).toHaveURL(new RegExp(next.split('?')[0] + '(\\?|$)'))
}

test('client books through login, keeps the chosen slot and cancels their appointment', async ({
  page,
}) => {
  await page.goto(`/?service=1&date=${tomorrow}`)
  await page.getByRole('button', { name: '09:00 — Anna Nowak', exact: true }).click()
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: 'test-results/studio-desktop.png', fullPage: true })
  await page.getByRole('link', { name: 'Zaloguj się i zarezerwuj' }).click()
  await page.getByLabel('Email', { exact: true }).fill('client@example.com')
  await page.getByLabel('Hasło', { exact: true }).fill('TestPassword123!')
  await page.getByRole('button', { name: 'Zaloguj się', exact: true }).click()
  await expect(page.getByLabel('Imię i nazwisko', { exact: true })).toHaveValue('Jan Kowalski')
  await page.getByRole('button', { name: 'Zarezerwuj wizytę', exact: true }).click()
  await expect(
    page.getByRole('status').filter({ hasText: 'Wizyta została zarezerwowana' }),
  ).toBeVisible()
  await expect(page.getByRole('article').getByText('Oczekująca', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Anuluj', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Potwierdź', exact: true }).click()
  await expect(page.getByRole('article').getByText('Anulowana', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Anuluj', exact: true })).toHaveCount(0)
})

test('registration validates data and creates a working client session', async ({ page }) => {
  await page.goto('/register')
  await page.getByRole('button', { name: 'Stwórz konto', exact: true }).click()
  await expect(page.getByText('Wpisz co najmniej 2 znaki.').first()).toBeVisible()
  await page.getByLabel('Imię', { exact: true }).fill('Nowy')
  await page.getByLabel('Nazwisko', { exact: true }).fill('Klient')
  await page.getByLabel('Email', { exact: true }).fill('new-client@example.com')
  await page.getByLabel('Telefon', { exact: true }).fill('+48 (555) 123-456')
  await page.getByLabel('Hasło', { exact: true }).fill('TestPassword123!')
  await page.getByRole('button', { name: 'Stwórz konto', exact: true }).click()
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByText('ID konta:', { exact: false })).toBeVisible()
  await expect(page.getByText('Tu jest jeszcze spokojnie')).toBeVisible()
  await page.goto('/admin')
  await expect(page.getByText('Ten widok wymaga innej roli')).toBeVisible()
})

test('a conflicting booking refreshes availability and asks for another slot', async ({ page }) => {
  await login(page, 'client@example.com', `/?service=1&date=${tomorrow}`)
  await page.getByRole('button', { name: '09:00 — Anna Nowak', exact: true }).click()
  await page.route('**/api/appointments', async (route) => {
    if (route.request().method() === 'POST')
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Employee already has an appointment at this time' }),
      })
    else await route.continue()
  })
  await page.getByRole('button', { name: 'Zarezerwuj wizytę', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Ten termin został już zarezerwowany')
  await expect(page.getByRole('button', { name: 'Wybierz usługę i godzinę' })).toBeDisabled()
})

test('staff sees only their calendar and can confirm and complete a visit', async ({ page }) => {
  await login(page, 'staff@example.com', `/staff?from=${tomorrow}&to=${tomorrow}`)
  const appointment = page.getByRole('article').filter({ hasText: 'other@example.com' })
  await expect(appointment).toHaveCount(1)
  await expect(page.getByRole('article').filter({ hasText: 'Bartek Kowalski' })).toHaveCount(0)
  await expect(appointment).toContainText('11:00')
  await appointment.getByRole('button', { name: 'Potwierdź', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Potwierdź', exact: true }).click()
  await expect(appointment.getByText('Potwierdzona', { exact: true })).toBeVisible()
  await appointment.getByRole('button', { name: 'Zakończ', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Potwierdź', exact: true }).click()
  await expect(appointment.getByText('Zakończona', { exact: true })).toBeVisible()
  await page.goto('/staff/schedule')
  await expect(page.getByText('Anna Nowak', { exact: true }).last()).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Tygodniowy grafik' })).toBeVisible()
})

test('admin adds and edits services and employees, assigns a service, saves hours and a break', async ({
  page,
}) => {
  await login(page, 'admin@example.com', '/admin/services')
  await page.getByRole('button', { name: 'Dodaj usługę', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Nazwa usługi').fill('Broda testowa')
  await dialog.getByLabel('Opis').fill('Precyzyjne modelowanie brody.')
  await dialog.getByLabel('Czas trwania (min)').fill('30')
  await dialog.getByLabel('Cena (PLN)').fill('55,50')
  await dialog.getByRole('button', { name: 'Zapisz usługę' }).click()
  await expect(page.getByRole('heading', { name: 'Broda testowa' })).toBeVisible()
  await page.getByRole('button', { name: 'Edytuj Broda testowa' }).click()
  await dialog.getByLabel('Cena (PLN)').fill('60,00')
  await dialog.getByRole('button', { name: 'Zapisz usługę' }).click()
  await expect(page.getByRole('article').filter({ hasText: 'Broda testowa' })).toContainText(
    '60,00',
  )

  await page.goto('/admin/employees')
  await page.getByRole('button', { name: 'Dodaj pracownika', exact: true }).click()
  await dialog.getByLabel('Imię i nazwisko / nazwa').fill('Ola Testowa')
  await dialog.getByRole('button', { name: 'Zapisz pracownika' }).click()
  const employee = page.getByRole('article').filter({ hasText: 'Ola Testowa' })
  await employee.getByRole('button', { name: 'Usługi i konto' }).click()
  await dialog.getByRole('checkbox', { name: /Broda testowa/ }).click()
  await expect(dialog.getByRole('checkbox', { name: /Broda testowa/ })).toBeChecked()
  await dialog.getByLabel('ID konta użytkownika').fill('2')
  await dialog.getByRole('button', { name: 'Przypisz konto' }).click()
  await expect(dialog.getByText('Konto zostało przypisane do pracownika.')).toBeVisible()
  await page.keyboard.press('Escape')

  await page.goto('/admin/schedule')
  await page.getByLabel('Wybierz pracownika').selectOption({ label: 'Ola Testowa' })
  await page.getByLabel('Początek pracy — Poniedziałek').fill('10:00')
  await page.getByLabel('Koniec pracy — Poniedziałek').fill('16:00')
  await page
    .locator('form')
    .filter({ hasText: 'Poniedziałek' })
    .getByRole('button', { name: 'Dodaj', exact: true })
    .click()
  await expect(page.locator('form').filter({ hasText: 'Poniedziałek' })).toContainText(
    'Godziny ustawione',
  )
  await page.getByLabel('Początek blokady').fill(`${later}T12:00`)
  await page.getByLabel('Koniec blokady').fill(`${later}T13:00`)
  await page.getByLabel('Powód', { exact: true }).fill('Przerwa testowa')
  await page.getByRole('button', { name: 'Dodaj blokadę' }).click()
  await expect(page.getByRole('heading', { name: 'Przerwa testowa' })).toBeVisible()
  await page.getByRole('button', { name: 'Edytuj blokadę Przerwa testowa' }).click()
  await page.getByLabel('Powód', { exact: true }).fill('Przerwa zmieniona')
  await page.getByRole('button', { name: 'Zapisz blokadę' }).click()
  await expect(page.getByRole('heading', { name: 'Przerwa zmieniona' })).toBeVisible()
  await page.getByRole('button', { name: 'Usuń blokadę Przerwa zmieniona' }).click()
  await dialog.getByRole('button', { name: 'Potwierdź', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Przerwa zmieniona' })).toHaveCount(0)
})

test('session expiry clears protected data and asks to sign in again', async ({ page }) => {
  await login(page, 'other@example.com')
  await page.route('**/api/users/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Invalid or expired credentials' }),
    }),
  )
  await page.reload()
  await expect(page).toHaveURL(/\/login\?next=/)
  await expect(
    page.getByText('Sesja wygasła. Zaloguj się ponownie, aby kontynuować.'),
  ).toBeVisible()
  expect(await page.evaluate(() => sessionStorage.getItem('studio.access-token'))).toBeNull()
})

test('mobile booking and navigation fit a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`/?service=1&date=${tomorrow}`)
  await expect(page.getByRole('button', { name: '09:00 — Anna Nowak', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.screenshot({ path: 'test-results/studio-mobile.png', fullPage: true })
  await page.getByRole('button', { name: 'Otwórz menu' }).click()
  await page.getByRole('link', { name: 'Nasze usługi', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Znajdź coś dla siebie.' })).toBeVisible()
})
