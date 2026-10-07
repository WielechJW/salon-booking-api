import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

export type User = components['schemas']['UserResponse']
export type Service = components['schemas']['ServiceResponse']
export type Employee = components['schemas']['EmployeeResponse']
export type Appointment = components['schemas']['AppointmentResponse']
export type AppointmentStatus = Appointment['status']
export type Slot = components['schemas']['ServiceAvailabilitySlotResponse']
export type Schedule = components['schemas']['ScheduleResponse']
export type TimeOff = components['schemas']['EmployeeTimeOffResponse']

const TOKEN_KEY = 'studio.access-token'
export const SESSION_EXPIRED_EVENT = 'studio:session-expired'
let accessToken: string | null = null
try {
  accessToken = sessionStorage.getItem(TOKEN_KEY)
} catch {
  /* Storage may be disabled. */
}

export function getAccessToken() {
  return accessToken
}
export function setAccessToken(token: string | null) {
  accessToken = token
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* In-memory sessions still work. */
  }
}

export const api = createClient<paths>({ baseUrl: '/api' })
api.use({
  onRequest({ request }) {
    if (accessToken) request.headers.set('Authorization', `Bearer ${accessToken}`)
    return request
  },
  onResponse({ request, response }) {
    if (
      response.status === 401 &&
      accessToken &&
      request.headers.get('Authorization') === `Bearer ${accessToken}` &&
      !request.url.includes('/auth/login')
    ) {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    }
    return response
  },
})

const translations: Record<string, string> = {
  'Invalid or expired credentials': 'Niepoprawny email lub hasło. Spróbuj ponownie.',
  'Email is already registered': 'Konto z tym adresem email już istnieje.',
  'Email already registered': 'Konto z tym adresem email już istnieje.',
  'Employee already has an appointment at this time':
    'Ten termin został już zarezerwowany. Wybierz inną godzinę.',
  'Employee is unavailable at this time': 'Pracownik nie jest już dostępny w tym terminie.',
  'Employee does not provide this service': 'Pracownik nie wykonuje wybranej usługi.',
  'Cannot book an appointment in the past': 'Ten termin już minął. Wybierz późniejszą godzinę.',
  'Time off overlaps an existing appointment':
    'W tym czasie jest aktywna wizyta. Najpierw zmień jej status.',
  'Time off overlaps an existing time off': 'W tym czasie istnieje już blokada.',
  'Service has appointments and cannot be deleted':
    'Usługa ma przypisane wizyty i nie może zostać usunięta.',
  'Employee has appointments and cannot be deleted':
    'Pracownik ma przypisane wizyty i nie może zostać usunięty.',
  'Employee already has an account': 'Pracownik ma już przypisane konto.',
  'Account is already assigned to another employee':
    'To konto jest już przypisane do innego pracownika.',
  'Account cannot be assigned to an employee': 'Nie można przypisać tego konta do pracownika.',
  'User not found': 'Nie znaleziono konta o podanym ID.',
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    let message =
      status === 409
        ? 'Operacja koliduje z istniejącymi danymi. Odśwież widok i spróbuj ponownie.'
        : 'Nie udało się wykonać operacji. Spróbuj ponownie.'
    if (status === 401) message = 'Sesja wygasła. Zaloguj się ponownie.'
    if (status === 403) message = 'Nie masz uprawnień do tej operacji.'
    if (status === 404) message = 'Nie znaleziono danych. Odśwież widok.'
    if (status === 422) message = 'Sprawdź dane formularza. Serwer odrzucił niepoprawną wartość.'
    if (typeof detail === 'string') {
      message = translations[detail] ?? message
      if (detail.startsWith('Schedule change would leave'))
        message = 'Nowe godziny pracy kolidują z aktywną wizytą.'
      if (detail.startsWith('Cannot change appointment status'))
        message = 'Nie można już zmienić statusu tej wizyty. Odśwież listę.'
    }
    super(message)
    this.name = 'ApiError'
  }
}

export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (!result.response.ok) {
    const detail =
      result.error && typeof result.error === 'object' && 'detail' in result.error
        ? result.error.detail
        : undefined
    throw new ApiError(result.response.status, detail)
  }
  return result.data as T
}

export function errorMessage(error: unknown) {
  return error instanceof ApiError
    ? error.message
    : 'Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie.'
}

export const getServices = async (signal?: AbortSignal) =>
  unwrap(await api.GET('/services', { signal }))
export const getEmployees = async (signal?: AbortSignal) =>
  unwrap(await api.GET('/employees', { signal }))
export const getSalon = async (signal?: AbortSignal) => unwrap(await api.GET('/salon', { signal }))
export const getMe = async (signal?: AbortSignal) => unwrap(await api.GET('/users/me', { signal }))
export const getAvailability = async (service_id: number, date: string, signal?: AbortSignal) =>
  unwrap(await api.GET('/availability', { params: { query: { service_id, date } }, signal }))

export type AppointmentFilters = {
  employee_id?: number
  status?: AppointmentStatus
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}
export async function getAppointments(
  filters: AppointmentFilters,
  own = false,
  signal?: AbortSignal,
) {
  const result = own
    ? await api.GET('/users/me/appointments', { params: { query: filters }, signal })
    : await api.GET('/appointments', { params: { query: filters }, signal })
  const items = unwrap(result)
  return { items, total: Number(result.response.headers.get('X-Total-Count') ?? items.length) }
}

export const createAppointment = async (body: components['schemas']['Appointment']) =>
  unwrap(await api.POST('/appointments', { body }))
export const changeStatus = async (id: number, status: AppointmentStatus) =>
  unwrap(
    await api.PATCH('/appointments/{appointment_id}/status', {
      params: { path: { appointment_id: id } },
      body: { status },
    }),
  )
export const getSchedule = async (id: number, signal?: AbortSignal) =>
  unwrap(
    await api.GET('/employees/{employee_id}/schedule', {
      params: { path: { employee_id: id } },
      signal,
    }),
  )
export const getTimeOffs = async (id: number, signal?: AbortSignal) =>
  unwrap(
    await api.GET('/employees/{employee_id}/time-off', {
      params: { path: { employee_id: id } },
      signal,
    }),
  )
export const getEmployeeServices = async (id: number, signal?: AbortSignal) =>
  unwrap(
    await api.GET('/employees/{employee_id}/services', {
      params: { path: { employee_id: id } },
      signal,
    }),
  )
