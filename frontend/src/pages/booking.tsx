import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'
import { addDays, format, isValid, parseISO } from 'date-fns'
import { pl } from 'date-fns/locale'
import { ArrowRight, Check, Clock3, RotateCw, Scissors, ShieldCheck, Users } from 'lucide-react'
import { useAuth } from '@/auth'
import {
  ApiError,
  createAppointment,
  getAvailability,
  type Service,
  type Slot,
  type User,
} from '@/lib/api/client'
import { dayInSalon, dayLabel, money, timeLabel } from '@/lib/dates'
import { invalidateBookings, useEmployees, useSalon, useServices } from '@/lib/query'
import { contactSchema } from '@/lib/validation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  EmptyState,
  ErrorNotice,
  Field,
  Loading,
  PageHeading,
  QueryError,
  SectionHeading,
} from '@/components/shared'

export function BookingPage() {
  const services = useServices()
  const employees = useEmployees()
  const salon = useSalon()
  const { user, loading: authLoading } = useAuth()
  const [search, setSearch] = useSearchParams()
  const [bookingError, setBookingError] = useState<unknown>()
  const location = useLocation()
  const navigate = useNavigate()
  const timezone = salon.data?.timezone
  const serviceList = services.data ?? []
  const employeeList = employees.data ?? []
  const today = timezone ? dayInSalon(timezone) : ''
  const requestedDate = search.get('date') ?? ''
  const parsedDate = parseISO(requestedDate)
  const date =
    /^\d{4}-\d{2}-\d{2}$/.test(requestedDate) &&
    isValid(parsedDate) &&
    format(parsedDate, 'yyyy-MM-dd') === requestedDate &&
    requestedDate >= today
      ? requestedDate
      : today
  const service = serviceList.find((item) => item.id === Number(search.get('service')))
  const employeeId = search.get('employee') || 'any'
  const availability = useQuery({
    queryKey: ['availability', service?.id, date],
    queryFn: ({ signal }) => getAvailability(service!.id, date, signal),
    enabled: !!service && !!timezone && !!date,
    staleTime: 15_000,
  })
  const slots =
    availability.data?.filter(
      (slot) => employeeId === 'any' || slot.employee_id === Number(employeeId),
    ) ?? []
  const selectedSlot = slots.find(
    (slot) =>
      slot.start_at === search.get('start') &&
      slot.employee_id === Number(search.get('slot_employee')),
  )
  const errorQuery = [services, employees, salon].find((query) => query.isError)

  function updateSelection(values: Record<string, string>) {
    setBookingError(undefined)
    setSearch(
      (previous) => {
        const next = new URLSearchParams(previous)
        next.delete('start')
        next.delete('slot_employee')
        Object.entries(values).forEach(([key, value]) => next.set(key, value))
        return next
      },
      { replace: true },
    )
  }

  function selectSlot(slot: Slot) {
    setBookingError(undefined)
    setSearch(
      (previous) => {
        const next = new URLSearchParams(previous)
        next.set('service', String(service!.id))
        next.set('date', date)
        next.set('start', slot.start_at)
        next.set('slot_employee', String(slot.employee_id))
        return next
      },
      { replace: true },
    )
  }

  return (
    <>
      <PageHeading
        eyebrow="Chwila tylko dla Ciebie"
        title="Zaplanuj swój dobry dzień."
        description="Wybierz usługę, znajdź dogodną godzinę i zostaw resztę nam."
      />
      <div className="mb-8 flex flex-wrap gap-x-7 gap-y-3 border-b pb-6 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <Scissors className="size-4" />
          {services.data?.length ?? '—'} usług w ofercie
        </span>
        <span className="flex items-center gap-2">
          <Users className="size-4" />
          {employees.data?.length ?? '—'} osób w zespole
        </span>
        <span className="flex items-center gap-2">
          <ShieldCheck className="size-4" />
          Rezerwacja z własnego konta
        </span>
      </div>
      {errorQuery ? (
        <QueryError error={errorQuery.error} retry={errorQuery.refetch} />
      ) : services.isPending || employees.isPending || salon.isPending ? (
        <Loading />
      ) : serviceList.length === 0 ? (
        <EmptyState
          title="Jeszcze chwila…"
          description="Salon przygotowuje ofertę. Dostępne usługi pojawią się tutaj wkrótce."
        />
      ) : (
        <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="grid gap-6">
            <section className="panel">
              <SectionHeading
                number="01"
                title="Na co masz ochotę?"
                description="Wybierz jedną usługę na tę wizytę."
              />
              <div className="grid gap-3 sm:grid-cols-2">
                {serviceList.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    aria-pressed={service?.id === item.id}
                    onClick={() => updateSelection({ service: String(item.id), employee: 'any' })}
                    className={cn(
                      'relative rounded-xl border p-4 text-left transition-colors hover:border-primary/50 focus-visible:outline-2 focus-visible:outline-primary',
                      service?.id === item.id
                        ? 'border-primary bg-primary/4 ring-1 ring-primary'
                        : 'bg-white',
                    )}
                  >
                    <div className="mb-5 flex items-start justify-between gap-3">
                      <span
                        className={cn(
                          'flex size-9 items-center justify-center rounded-lg',
                          service?.id === item.id ? 'bg-primary text-white' : 'bg-secondary',
                        )}
                      >
                        <Scissors className="size-4" />
                      </span>
                      {service?.id === item.id && <Check className="size-4 text-primary" />}
                    </div>
                    <h3 className="text-sm font-semibold">{item.name}</h3>
                    <p className="mt-2 line-clamp-2 min-h-10 text-xs leading-5 text-muted-foreground">
                      {item.description}
                    </p>
                    <div className="mt-4 flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                        <Clock3 className="size-3" />
                        {item.duration_minutes} min
                      </span>
                      <span className="text-sm font-semibold">{money(item.price)}</span>
                    </div>
                  </button>
                ))}
              </div>
            </section>
            <section className="panel">
              <SectionHeading
                number="02"
                title="Znajdź swój termin"
                description="Godziny są podane w strefie salonu. Możesz wybrać dowolnego pracownika."
              />
              <div className="mb-5 grid gap-4 sm:grid-cols-2">
                <Field label="Dzień wizyty" id="booking-date">
                  <Input
                    id="booking-date"
                    type="date"
                    min={today}
                    value={date}
                    onChange={(event) => updateSelection({ date: event.target.value })}
                  />
                </Field>
                <Field label="Pracownik" id="booking-employee">
                  <select
                    id="booking-employee"
                    className="native-select"
                    value={employeeId}
                    onChange={(event) => updateSelection({ employee: event.target.value })}
                  >
                    <option value="any">Dowolny pracownik</option>
                    {employeeList.map((employee) => (
                      <option key={employee.id} value={employee.id}>
                        {employee.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="mb-6 grid grid-cols-7 gap-1.5">
                {Array.from({ length: 7 }, (_, index) =>
                  addDays(new Date(`${today}T12:00:00`), index),
                ).map((day) => {
                  const value = format(day, 'yyyy-MM-dd')
                  return (
                    <button
                      key={value}
                      type="button"
                      aria-label={dayLabel(value)}
                      aria-pressed={date === value}
                      onClick={() => updateSelection({ date: value })}
                      className={cn(
                        'rounded-lg border py-3 text-center transition-colors focus-visible:outline-2 focus-visible:outline-primary',
                        date === value
                          ? 'border-primary bg-primary text-white'
                          : 'hover:bg-secondary',
                      )}
                    >
                      <span className="block text-[10px] capitalize opacity-65">
                        {format(day, 'EEE', { locale: pl })}
                      </span>
                      <span className="mt-1 block text-lg font-medium">{format(day, 'd')}</span>
                    </button>
                  )
                })}
              </div>
              <div className="mb-3 flex items-center justify-between gap-2">
                <p className="text-xs font-medium capitalize">{dayLabel(date)}</p>
                {service && (
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={availability.isFetching}
                    onClick={() => void availability.refetch()}
                    aria-label="Odśwież dostępne terminy"
                  >
                    <RotateCw
                      className={cn('size-3.5', availability.isFetching && 'animate-spin')}
                    />
                    <span className="hidden sm:inline">Odśwież</span>
                  </Button>
                )}
              </div>
              {!!bookingError && (
                <div className="mb-4">
                  <ErrorNotice error={bookingError} />
                </div>
              )}
              {!service ? (
                <EmptyState
                  title="Najpierw wybierz usługę"
                  description="Pokażemy godziny, w których zmieści się cała Twoja wizyta."
                />
              ) : availability.isPending ? (
                <Loading label="Szukamy wolnych terminów…" />
              ) : availability.isError ? (
                <QueryError error={availability.error} retry={availability.refetch} />
              ) : slots.length === 0 ? (
                <EmptyState
                  title="Brak wolnych terminów"
                  description="Spróbuj wybrać inny dzień lub innego pracownika."
                />
              ) : (
                <div className="grid max-h-96 grid-cols-2 gap-2 overflow-y-auto p-0.5 sm:grid-cols-3">
                  {slots.map((slot) => (
                    <button
                      type="button"
                      key={`${slot.employee_id}-${slot.start_at}`}
                      aria-pressed={selectedSlot === slot}
                      aria-label={`${timeLabel(slot.start_at, timezone!)} — ${slot.employee_name}`}
                      onClick={() => selectSlot(slot)}
                      className={cn(
                        'rounded-lg border px-3 py-3 text-left transition-colors focus-visible:outline-2 focus-visible:outline-primary',
                        selectedSlot === slot
                          ? 'border-primary bg-accent ring-1 ring-primary'
                          : 'hover:border-primary/50 hover:bg-secondary/60',
                      )}
                    >
                      <span className="text-sm font-semibold">
                        {timeLabel(slot.start_at, timezone!)}
                      </span>
                      <span className="mt-1 block truncate text-[10px] text-muted-foreground">
                        {slot.employee_name}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </section>
          </div>
          <aside className="grid gap-4 xl:sticky xl:top-6">
            <div className="overflow-hidden rounded-2xl border bg-white">
              <div className="bg-accent px-6 py-5">
                <p className="eyebrow text-primary/60">Twoja chwila</p>
                <h2 className="mt-2 text-xl font-semibold">Podsumowanie wizyty</h2>
              </div>
              <div className="p-6">
                <div className="mb-6 border-b pb-5">
                  <p className="text-sm font-semibold">{service?.name ?? 'Wybierz usługę'}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {service
                      ? `${service.duration_minutes} minut dla Ciebie`
                      : 'Zacznij od oferty po lewej stronie.'}
                  </p>
                </div>
                <dl className="grid gap-4 text-xs">
                  <div className="flex justify-between gap-3">
                    <dt className="text-muted-foreground">Dzień</dt>
                    <dd className="text-right capitalize">{dayLabel(date)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Godzina</dt>
                    <dd>
                      {selectedSlot ? timeLabel(selectedSlot.start_at, timezone!) : 'Do wyboru'}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-muted-foreground">Pracownik</dt>
                    <dd className="text-right">{selectedSlot?.employee_name ?? 'Do wyboru'}</dd>
                  </div>
                  <div className="mt-2 flex items-center justify-between border-t pt-5">
                    <dt className="text-muted-foreground">Cena usługi</dt>
                    <dd className="text-xl font-semibold">
                      {service ? money(service.price) : '—'}
                    </dd>
                  </div>
                </dl>
                <div className="mt-6">
                  {authLoading ? (
                    <Loading label="Sprawdzanie konta…" />
                  ) : selectedSlot && service && user ? (
                    <BookingContact
                      key={user.id}
                      user={user}
                      service={service}
                      slot={selectedSlot}
                      onSuccess={async (id) => {
                        await invalidateBookings()
                        navigate(`/account?booked=${id}`)
                      }}
                      onError={(error) => {
                        setBookingError(error)
                        if (error instanceof ApiError && error.status === 409) {
                          setSearch(
                            (previous) => {
                              const next = new URLSearchParams(previous)
                              next.delete('start')
                              next.delete('slot_employee')
                              return next
                            },
                            { replace: true },
                          )
                          void availability.refetch()
                        }
                      }}
                    />
                  ) : selectedSlot && !user ? (
                    <>
                      <Button asChild className="w-full">
                        <Link
                          to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
                        >
                          Zaloguj się i zarezerwuj
                          <ArrowRight className="size-4" />
                        </Link>
                      </Button>
                      <p className="mt-3 text-center text-[11px] leading-5 text-muted-foreground">
                        Wybrany termin zachowamy po zalogowaniu.
                      </p>
                    </>
                  ) : (
                    <Button className="w-full" disabled>
                      Wybierz usługę i godzinę
                      <ArrowRight className="size-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
            <p className="px-3 text-center text-[11px] leading-5 text-muted-foreground">
              Wyświetlenie terminu nie blokuje go w kalendarzu. Dostępność sprawdzamy ponownie przy
              rezerwacji.
            </p>
          </aside>
        </div>
      )}
    </>
  )
}

function BookingContact({
  user,
  service,
  slot,
  onSuccess,
  onError,
}: {
  user: User
  service: Service
  slot: Slot
  onSuccess: (id: number) => Promise<void>
  onError: (error: unknown) => void
}) {
  const form = useForm<z.infer<typeof contactSchema>>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      client_name: `${user.first_name} ${user.last_name}`,
      client_email: user.email,
      client_phone: user.phone,
    },
  })
  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof contactSchema>) =>
      createAppointment({
        ...values,
        service_id: service.id,
        employee_id: slot.employee_id,
        start_at: slot.start_at,
      }),
    onSuccess: (appointment) => onSuccess(appointment.id),
    onError,
  })
  return (
    <form
      className="grid gap-4"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      <p className="eyebrow">Dane do wizyty</p>
      <Field
        label="Imię i nazwisko"
        id="client_name"
        error={form.formState.errors.client_name?.message}
      >
        <Input id="client_name" autoComplete="name" {...form.register('client_name')} />
      </Field>
      <Field label="Email" id="client_email" error={form.formState.errors.client_email?.message}>
        <Input
          id="client_email"
          type="email"
          autoComplete="email"
          {...form.register('client_email')}
        />
      </Field>
      <Field label="Telefon" id="client_phone" error={form.formState.errors.client_phone?.message}>
        <Input id="client_phone" type="tel" autoComplete="tel" {...form.register('client_phone')} />
      </Field>
      <Button type="submit" className="mt-1 w-full" disabled={mutation.isPending}>
        {mutation.isPending ? 'Rezerwowanie…' : 'Zarezerwuj wizytę'}
        <ArrowRight className="size-4" />
      </Button>
    </form>
  )
}
