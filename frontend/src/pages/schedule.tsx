import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { format } from 'date-fns'
import { TZDate } from '@date-fns/tz'
import { z } from 'zod'
import { Clock3, Pencil, Plus, Trash2, X } from 'lucide-react'
import { useAuth } from '@/auth'
import {
  api,
  getSchedule,
  getTimeOffs,
  unwrap,
  type Schedule,
  type TimeOff,
} from '@/lib/api/client'
import { dateTimeLabel, dayInSalon, localDateTimeToUtc, weekdays } from '@/lib/dates'
import { queryClient, useEmployees, useSalon } from '@/lib/query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  ConfirmDialog,
  EmptyState,
  ErrorNotice,
  Field,
  Loading,
  PageHeading,
  QueryError,
} from '@/components/shared'

const scheduleSchema = z
  .object({
    start_time: z.string().regex(/^\d{2}:\d{2}$/, 'Podaj godzinę.'),
    end_time: z.string().regex(/^\d{2}:\d{2}$/, 'Podaj godzinę.'),
  })
  .refine((values) => values.end_time > values.start_time, {
    message: 'Koniec pracy musi być późniejszy od początku.',
    path: ['end_time'],
  })
const timeOffSchema = z
  .object({
    start_at: z.string().min(1, 'Podaj początek blokady.'),
    end_at: z.string().min(1, 'Podaj koniec blokady.'),
    reason: z.string().trim().min(2, 'Wpisz co najmniej 2 znaki.').max(500),
  })
  .refine((values) => values.end_at > values.start_at, {
    message: 'Koniec blokady musi być późniejszy od początku.',
    path: ['end_at'],
  })

export function SchedulePage({ admin = false }: { admin?: boolean }) {
  const { user } = useAuth()
  const employees = useEmployees()
  const salon = useSalon()
  const [search, setSearch] = useSearchParams()
  const requestedId = Number(search.get('employee'))
  const employeeId = admin
    ? (employees.data?.find((item) => item.id === requestedId)?.id ?? employees.data?.[0]?.id)
    : user?.employee_id
  return (
    <>
      <PageHeading
        eyebrow={admin ? 'Zarządzanie salonem' : 'Panel pracownika'}
        title={admin ? 'Każdy dzień ma swój rytm.' : 'Zaplanuj swój czas.'}
        description="Ustaw stałe godziny pracy i dodaj urlopy lub przerwy. Zmiany kolidujące z aktywnymi wizytami zostaną odrzucone."
      />
      {employees.isError ? (
        <QueryError error={employees.error} retry={employees.refetch} />
      ) : salon.isError ? (
        <QueryError error={salon.error} retry={salon.refetch} />
      ) : employees.isPending || salon.isPending ? (
        <Loading />
      ) : !employeeId ? (
        <EmptyState
          title={admin ? 'Dodaj najpierw pracownika' : 'Brak przypisanego kalendarza'}
          description={
            admin
              ? 'Grafik możesz ustawić po dodaniu osoby do zespołu.'
              : 'Poproś administratora o przypisanie Twojego konta do pracownika.'
          }
        />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-white p-5">
            {admin ? (
              <Field label="Wybierz pracownika" id="schedule-employee">
                <select
                  id="schedule-employee"
                  className="native-select min-w-56"
                  value={employeeId}
                  onChange={(event) =>
                    setSearch({ employee: event.target.value }, { replace: true })
                  }
                >
                  {employees.data.map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.name}
                    </option>
                  ))}
                </select>
              </Field>
            ) : (
              <p className="font-medium">
                {employees.data.find((employee) => employee.id === employeeId)?.name}
              </p>
            )}
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock3 className="size-4" />
              Strefa salonu: {salon.data.timezone}
            </span>
          </div>
          <CalendarWorkspace
            key={employeeId}
            employeeId={employeeId}
            timezone={salon.data.timezone}
          />
        </>
      )}
    </>
  )
}

function CalendarWorkspace({ employeeId, timezone }: { employeeId: number; timezone: string }) {
  const schedule = useQuery({
    queryKey: ['schedules', employeeId],
    queryFn: ({ signal }) => getSchedule(employeeId, signal),
  })
  const timeOffs = useQuery({
    queryKey: ['time-offs', employeeId],
    queryFn: ({ signal }) => getTimeOffs(employeeId, signal),
  })
  const [editing, setEditing] = useState<TimeOff>()
  const [removing, setRemoving] = useState<TimeOff>()
  const remove = useMutation({
    mutationFn: async (timeOff: TimeOff) =>
      unwrap(
        await api.DELETE('/employees/{employee_id}/time-off/{time_off_id}', {
          params: { path: { employee_id: employeeId, time_off_id: timeOff.id } },
        }),
      ),
    onSuccess: async () => {
      setRemoving(undefined)
      if (editing?.id === removing?.id) setEditing(undefined)
      await queryClient.invalidateQueries({ queryKey: ['time-offs', employeeId] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <div className="grid items-start gap-6 xl:grid-cols-2">
      <section className="panel">
        <h2 className="text-lg font-semibold">Tygodniowy grafik</h2>
        <p className="mb-6 mt-2 text-xs leading-5 text-muted-foreground">
          Stałe godziny powtarzają się co tydzień. Zapisz każdy wybrany dzień osobno.
        </p>
        {schedule.isPending ? (
          <Loading />
        ) : schedule.isError ? (
          <QueryError error={schedule.error} retry={schedule.refetch} />
        ) : (
          <div className="grid gap-4">
            {weekdays.map((name, day) => {
              const current = schedule.data.find((item) => item.day_of_week === day)
              return (
                <ScheduleRow
                  key={`${day}-${current?.start_time}-${current?.end_time}`}
                  employeeId={employeeId}
                  day={day}
                  name={name}
                  current={current}
                />
              )
            })}
          </div>
        )}
      </section>
      <section className="panel">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {editing ? 'Edytuj blokadę' : 'Urlopy i przerwy'}
          </h2>
          {editing && (
            <Button
              size="icon"
              variant="ghost"
              aria-label="Anuluj edycję blokady"
              onClick={() => setEditing(undefined)}
            >
              <X className="size-4" />
            </Button>
          )}
        </div>
        <p className="mb-6 mt-2 text-xs leading-5 text-muted-foreground">
          Zablokuj czas, w którym pracownik nie przyjmuje klientów.
        </p>
        <TimeOffForm
          key={editing?.id ?? 'new'}
          employeeId={employeeId}
          timezone={timezone}
          timeOff={editing}
          onSaved={() => setEditing(undefined)}
        />
        <h3 className="mb-4 mt-8 border-t pt-6 text-sm font-semibold">Zapisane blokady</h3>
        {timeOffs.isPending ? (
          <Loading />
        ) : timeOffs.isError ? (
          <QueryError error={timeOffs.error} retry={timeOffs.refetch} />
        ) : timeOffs.data.length === 0 ? (
          <p className="rounded-xl bg-secondary p-4 text-xs text-muted-foreground">
            Nie ma jeszcze urlopów ani przerw.
          </p>
        ) : (
          <div className="grid max-h-96 gap-3 overflow-y-auto">
            {timeOffs.data.map((item) => (
              <article
                key={item.id}
                className="flex items-start justify-between gap-3 rounded-xl border p-4"
              >
                <div>
                  <h4 className="text-sm font-medium">{item.reason}</h4>
                  <p className="mt-2 text-[11px] leading-5 text-muted-foreground">
                    {dateTimeLabel(item.start_at, timezone)}
                    <br />
                    do {dateTimeLabel(item.end_at, timezone)}
                  </p>
                </div>
                <div className="flex">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Edytuj blokadę ${item.reason}`}
                    onClick={() => setEditing(item)}
                  >
                    <Pencil className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive"
                    aria-label={`Usuń blokadę ${item.reason}`}
                    onClick={() => {
                      remove.reset()
                      setRemoving(item)
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      <ConfirmDialog
        open={!!removing}
        onOpenChange={(open) => {
          if (!open) setRemoving(undefined)
        }}
        title="Usunąć blokadę czasu?"
        description={`Blokada „${removing?.reason ?? ''}” zostanie usunięta. Ten czas ponownie będzie brany pod uwagę przy rezerwacji.`}
        destructive
        pending={remove.isPending}
        error={remove.error}
        onConfirm={() => {
          if (removing) remove.mutate(removing)
        }}
      />
    </div>
  )
}

function ScheduleRow({
  employeeId,
  day,
  name,
  current,
}: {
  employeeId: number
  day: number
  name: string
  current?: Schedule
}) {
  const form = useForm<z.infer<typeof scheduleSchema>>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      start_time: current?.start_time.slice(0, 5) ?? '09:00',
      end_time: current?.end_time.slice(0, 5) ?? '17:00',
    },
  })
  const mutation = useMutation({
    mutationFn: async (values: z.infer<typeof scheduleSchema>) => {
      const body = {
        day_of_week: day,
        start_time: `${values.start_time}:00`,
        end_time: `${values.end_time}:00`,
      }
      const params = { path: { employee_id: employeeId } }
      return current
        ? unwrap(await api.PUT('/employees/{employee_id}/schedule', { params, body }))
        : unwrap(await api.POST('/employees/{employee_id}/schedule', { params, body }))
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['schedules', employeeId] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <form
      className="rounded-xl border p-4"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{name}</h3>
        <span className="text-[10px] text-muted-foreground">
          {current ? 'Godziny ustawione' : 'Brak grafiku'}
        </span>
      </div>
      <div className="grid grid-cols-[1fr_1fr_auto] items-start gap-2">
        <div>
          <label className="sr-only" htmlFor={`start-${day}`}>
            Początek pracy — {name}
          </label>
          <Input id={`start-${day}`} type="time" {...form.register('start_time')} />
        </div>
        <div>
          <label className="sr-only" htmlFor={`end-${day}`}>
            Koniec pracy — {name}
          </label>
          <Input id={`end-${day}`} type="time" {...form.register('end_time')} />
        </div>
        <Button
          type="submit"
          variant={current ? 'outline' : 'default'}
          disabled={mutation.isPending || (!!current && !form.formState.isDirty)}
        >
          {mutation.isPending ? '…' : current ? 'Zapisz' : 'Dodaj'}
        </Button>
      </div>
      {form.formState.errors.end_time && (
        <p role="alert" className="mt-2 text-xs text-destructive">
          {form.formState.errors.end_time.message}
        </p>
      )}
      {mutation.isError && (
        <div className="mt-3">
          <ErrorNotice error={mutation.error} />
        </div>
      )}
    </form>
  )
}

function TimeOffForm({
  employeeId,
  timezone,
  timeOff,
  onSaved,
}: {
  employeeId: number
  timezone: string
  timeOff?: TimeOff
  onSaved: () => void
}) {
  const [localError, setLocalError] = useState('')
  const [saved, setSaved] = useState(false)
  const today = dayInSalon(timezone)
  const localValue = (value: string) => format(new TZDate(value, timezone), "yyyy-MM-dd'T'HH:mm")
  const form = useForm<z.infer<typeof timeOffSchema>>({
    resolver: zodResolver(timeOffSchema),
    defaultValues: {
      start_at: timeOff ? localValue(timeOff.start_at) : `${today}T12:00`,
      end_at: timeOff ? localValue(timeOff.end_at) : `${today}T13:00`,
      reason: timeOff?.reason ?? '',
    },
  })
  const mutation = useMutation({
    mutationFn: async (body: { start_at: string; end_at: string; reason: string }) =>
      timeOff
        ? unwrap(
            await api.PUT('/employees/{employee_id}/time-off/{time_off_id}', {
              params: { path: { employee_id: employeeId, time_off_id: timeOff.id } },
              body,
            }),
          )
        : unwrap(
            await api.POST('/employees/{employee_id}/time-off', {
              params: { path: { employee_id: employeeId } },
              body,
            }),
          ),
    onSuccess: async () => {
      setSaved(true)
      if (timeOff) onSaved()
      else form.reset()
      await queryClient.invalidateQueries({ queryKey: ['time-offs', employeeId] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <form
      className="grid gap-4"
      onSubmit={form.handleSubmit((values) => {
        setSaved(false)
        setLocalError('')
        try {
          mutation.mutate({
            ...values,
            start_at: localDateTimeToUtc(values.start_at, timezone),
            end_at: localDateTimeToUtc(values.end_at, timezone),
          })
        } catch (error) {
          setLocalError(error instanceof Error ? error.message : 'Sprawdź datę i godzinę.')
        }
      })}
      noValidate
    >
      {localError && <ErrorNotice message={localError} />}
      {mutation.isError && <ErrorNotice error={mutation.error} />}
      {saved && (
        <p role="status" className="text-sm text-emerald-700">
          Blokada czasu została zapisana.
        </p>
      )}
      <Field
        label="Początek blokady"
        id="off-start"
        error={form.formState.errors.start_at?.message}
      >
        <Input id="off-start" type="datetime-local" {...form.register('start_at')} />
      </Field>
      <Field label="Koniec blokady" id="off-end" error={form.formState.errors.end_at?.message}>
        <Input id="off-end" type="datetime-local" {...form.register('end_at')} />
      </Field>
      <Field label="Powód" id="off-reason" error={form.formState.errors.reason?.message}>
        <Input
          id="off-reason"
          placeholder="Np. urlop lub przerwa obiadowa"
          {...form.register('reason')}
        />
      </Field>
      <Button type="submit" disabled={mutation.isPending}>
        <Plus className="size-4" />
        {mutation.isPending ? 'Zapisywanie…' : timeOff ? 'Zapisz blokadę' : 'Dodaj blokadę'}
      </Button>
    </form>
  )
}
