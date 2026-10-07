import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  X,
} from 'lucide-react'
import { useAuth } from '@/auth'
import {
  changeStatus,
  getAppointments,
  type Appointment,
  type AppointmentStatus,
} from '@/lib/api/client'
import { dateTimeLabel, dayInSalon, money, statusLabels } from '@/lib/dates'
import { invalidateBookings, useEmployees, useSalon, useServices } from '@/lib/query'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  ConfirmDialog,
  EmptyState,
  ErrorNotice,
  Field,
  Loading,
  PageHeading,
  QueryError,
} from '@/components/shared'

const statusClasses = {
  pending: 'bg-amber-50 text-amber-800 border-amber-200',
  confirmed: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  completed: 'bg-slate-100 text-slate-600 border-slate-200',
  cancelled: 'bg-red-50 text-red-700 border-red-200',
}
const transitions: Record<AppointmentStatus, AppointmentStatus[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['completed', 'cancelled'],
  cancelled: [],
  completed: [],
}
const actionLabels = {
  confirmed: 'Potwierdź',
  completed: 'Zakończ',
  cancelled: 'Anuluj',
  pending: 'Oczekująca',
}
type Mode = 'client' | 'staff' | 'admin'

export function AppointmentsPage({ mode }: { mode: Mode }) {
  const { user } = useAuth()
  const salon = useSalon()
  const services = useServices()
  const employees = useEmployees()
  const [search, setSearch] = useSearchParams()
  const [action, setAction] = useState<{ appointment: Appointment; status: AppointmentStatus }>()
  const [notice, setNotice] = useState('')
  const today = salon.data ? dayInSalon(salon.data.timezone) : ''
  const from = search.get('from') ?? (mode === 'client' ? '' : today)
  const to = search.get('to') ?? (mode === 'client' ? '' : today)
  const status = search.get('status') ?? 'any'
  const employee = search.get('employee') ?? 'any'
  const requestedOffset = Number(search.get('offset') ?? 0)
  const offset = Number.isSafeInteger(requestedOffset) && requestedOffset >= 0 ? requestedOffset : 0
  const dateError = !!from && !!to && from > to
  const filters = {
    date_from: from || undefined,
    date_to: to || undefined,
    status: status in statusLabels ? (status as AppointmentStatus) : undefined,
    employee_id:
      mode === 'staff'
        ? (user?.employee_id ?? undefined)
        : mode === 'admin' && employee !== 'any'
          ? Number(employee)
          : undefined,
    limit: 20,
    offset,
  }
  const appointments = useQuery({
    queryKey: ['appointments', mode, user?.id, filters],
    queryFn: ({ signal }) => getAppointments(filters, mode === 'client', signal),
    enabled: !!salon.data && !dateError,
  })
  const mutation = useMutation({
    mutationFn: ({
      appointment,
      status,
    }: {
      appointment: Appointment
      status: AppointmentStatus
    }) => changeStatus(appointment.id, status),
    onSuccess: async () => {
      setAction(undefined)
      setNotice('Status wizyty został zmieniony.')
      await invalidateBookings()
    },
    onError: () => {
      void invalidateBookings()
    },
  })
  const headings = {
    client: [
      'Twoje konto',
      'Twoje wizyty.',
      'Nadchodzące terminy i historia wizyt w jednym miejscu.',
    ],
    staff: [
      'Panel pracownika',
      'Twój dzień w salonie.',
      'Sprawdź rezerwacje klientów i zarządzaj statusami wizyt.',
    ],
    admin: [
      'Panel administratora',
      'Wszystko pod kontrolą.',
      'Przeglądaj rezerwacje salonu, filtruj terminy i zarządzaj wizytami.',
    ],
  }
  function updateFilter(key: string, value: string) {
    setSearch(
      (previous) => {
        const next = new URLSearchParams(previous)
        next.set(key, value)
        if (key !== 'offset') next.set('offset', '0')
        return next
      },
      { replace: true },
    )
  }
  function openAction(appointment: Appointment, status: AppointmentStatus) {
    mutation.reset()
    setAction({ appointment, status })
  }

  return (
    <>
      <PageHeading
        eyebrow={headings[mode][0]}
        title={headings[mode][1]}
        description={headings[mode][2]}
        action={
          <Button asChild>
            <Link to="/">
              Nowa rezerwacja
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        }
      />
      {mode === 'client' && user && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white px-5 py-4 text-xs">
          <span>
            {user.first_name} {user.last_name}{' '}
            <span className="ml-2 text-muted-foreground">{user.email}</span>
          </span>
          <span className="text-muted-foreground">ID konta: #{user.id}</span>
        </div>
      )}
      {(search.has('booked') || notice) && (
        <div
          role="status"
          className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          <span className="flex items-center gap-2">
            <Check className="size-4" />
            {notice || 'Wizyta została zarezerwowana. Salon oczekuje na jej potwierdzenie.'}
          </span>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Zamknij komunikat"
            onClick={() => {
              setNotice('')
              setSearch(
                (previous) => {
                  const next = new URLSearchParams(previous)
                  next.delete('booked')
                  return next
                },
                { replace: true },
              )
            }}
          >
            <X className="size-4" />
          </Button>
        </div>
      )}
      {mode === 'admin' && (
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          {[
            {
              label: 'Wizyty w wybranym widoku',
              value: appointments.data?.total,
              icon: CalendarDays,
            },
            { label: 'Usługi w ofercie', value: services.data?.length, icon: Check },
            { label: 'Osoby w zespole', value: employees.data?.length, icon: CalendarDays },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="rounded-xl border bg-white p-5">
              <div className="flex justify-between">
                <p className="text-xs text-muted-foreground">{label}</p>
                <Icon className="size-4 text-muted-foreground" />
              </div>
              <p className="mt-4 text-3xl font-semibold">{value ?? '—'}</p>
            </div>
          ))}
        </div>
      )}
      <section className="panel">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">
            {mode === 'client' ? 'Lista wizyt' : 'Rezerwacje'}
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void appointments.refetch()}
            disabled={appointments.isFetching || dateError}
          >
            <RotateCw className={cn('size-3.5', appointments.isFetching && 'animate-spin')} />
            Odśwież
          </Button>
        </div>
        <div className={cn('mb-6 grid gap-4 sm:grid-cols-3', mode === 'admin' && 'xl:grid-cols-4')}>
          <Field label="Od dnia" id="date-from">
            <Input
              id="date-from"
              type="date"
              value={from}
              onChange={(event) => updateFilter('from', event.target.value)}
            />
          </Field>
          <Field label="Do dnia" id="date-to">
            <Input
              id="date-to"
              type="date"
              value={to}
              onChange={(event) => updateFilter('to', event.target.value)}
            />
          </Field>
          <Field label="Status" id="status-filter">
            <select
              id="status-filter"
              className="native-select"
              value={status}
              onChange={(event) => updateFilter('status', event.target.value)}
            >
              <option value="any">Wszystkie statusy</option>
              {Object.entries(statusLabels).map(([value, label]) => (
                <option value={value} key={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
          {mode === 'admin' && (
            <Field label="Pracownik" id="employee-filter">
              <select
                id="employee-filter"
                className="native-select"
                value={employee}
                onChange={(event) => updateFilter('employee', event.target.value)}
              >
                <option value="any">Cały zespół</option>
                {employees.data?.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </Field>
          )}
        </div>
        {dateError ? (
          <ErrorNotice message="Data końcowa musi być równa lub późniejsza od daty początkowej." />
        ) : salon.isError ? (
          <QueryError error={salon.error} retry={salon.refetch} />
        ) : appointments.isPending ? (
          <Loading />
        ) : appointments.isError ? (
          <QueryError error={appointments.error} retry={appointments.refetch} />
        ) : appointments.data.items.length === 0 ? (
          <EmptyState
            title="Tu jest jeszcze spokojnie"
            description="Nie ma wizyt pasujących do wybranych filtrów. Możesz zmienić zakres dat lub zaplanować nową wizytę."
            action={
              offset > 0 ? (
                <Button variant="outline" onClick={() => updateFilter('offset', '0')}>
                  Wróć na pierwszą stronę
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div>
            {appointments.data.items.map((appointment) => {
              const service = services.data?.find((item) => item.id === appointment.service_id)
              const employee = employees.data?.find((item) => item.id === appointment.employee_id)
              const actions =
                mode === 'client'
                  ? transitions[appointment.status].filter((status) => status === 'cancelled')
                  : transitions[appointment.status]
              return (
                <article
                  key={appointment.id}
                  className="flex flex-wrap items-center justify-between gap-4 border-t py-5 first:border-t-0 first:pt-0"
                >
                  <div className="flex min-w-0 flex-1 gap-4">
                    <div className="hidden size-11 shrink-0 items-center justify-center rounded-xl bg-secondary sm:flex">
                      <CalendarDays className="size-5" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold">
                        {service?.name ?? `Usługa #${appointment.service_id}`}
                      </h3>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {dateTimeLabel(appointment.start_at, salon.data!.timezone)} ·{' '}
                        {appointment.duration_minutes} min
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {employee?.name ?? `Pracownik #${appointment.employee_id}`}
                        {mode !== 'client' && ` · ${appointment.client_name}`}
                      </p>
                      {mode !== 'client' && (
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          {appointment.client_email} · {appointment.client_phone}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-medium">{money(appointment.price)}</span>
                    <Badge variant="outline" className={statusClasses[appointment.status]}>
                      {statusLabels[appointment.status]}
                    </Badge>
                    <div className="flex gap-1.5">
                      {actions.map((status) => (
                        <Button
                          key={status}
                          size="sm"
                          variant="outline"
                          className={
                            status === 'cancelled' ? 'text-destructive hover:bg-red-50' : ''
                          }
                          onClick={() => openAction(appointment, status)}
                        >
                          {actionLabels[status]}
                        </Button>
                      ))}
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
        {appointments.data && !dateError && (
          <div className="mt-5 flex items-center justify-between gap-3 border-t pt-5 text-xs text-muted-foreground">
            <span>
              {appointments.data.total === 0
                ? '0 wizyt'
                : `${Math.min(offset + 1, appointments.data.total)}–${Math.min(offset + appointments.data.items.length, appointments.data.total)} z ${appointments.data.total} wizyt`}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                aria-label="Poprzednia strona"
                disabled={offset === 0 || appointments.isFetching}
                onClick={() => updateFilter('offset', String(Math.max(0, offset - 20)))}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                aria-label="Następna strona"
                disabled={offset + 20 >= appointments.data.total || appointments.isFetching}
                onClick={() => updateFilter('offset', String(offset + 20))}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        )}
      </section>
      <ConfirmDialog
        open={!!action}
        onOpenChange={(open) => {
          if (!open) setAction(undefined)
        }}
        title={action ? `${actionLabels[action.status]} wizytę?` : 'Zmień status'}
        description={
          action
            ? `Wizyta #${action.appointment.id} — ${dateTimeLabel(action.appointment.start_at, salon.data!.timezone)}. ${action.status === 'cancelled' ? 'Anulowanie zwolni termin w kalendarzu.' : 'Zmiana zostanie zapisana w kalendarzu salonu.'}`
            : ''
        }
        destructive={action?.status === 'cancelled'}
        pending={mutation.isPending}
        error={mutation.error}
        onConfirm={() => {
          if (action) mutation.mutate(action)
        }}
      />
    </>
  )
}
