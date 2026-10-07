import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Pencil, Plus, Settings2, Trash2, UserRound } from 'lucide-react'
import { api, getEmployeeServices, unwrap, type Employee } from '@/lib/api/client'
import { money } from '@/lib/dates'
import { queryClient, useEmployees, useServices } from '@/lib/query'
import { personName } from '@/lib/validation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ConfirmDialog,
  EmptyState,
  ErrorNotice,
  Field,
  Loading,
  PageHeading,
  QueryError,
} from '@/components/shared'

const employeeSchema = z.object({ name: personName })
const accountSchema = z.object({
  user_id: z.number().int().positive('Podaj poprawne ID konta.').max(2147483647),
})

export function AdminEmployeesPage() {
  const employees = useEmployees()
  const [editing, setEditing] = useState<Employee | null | undefined>()
  const [managing, setManaging] = useState<Employee>()
  const [removing, setRemoving] = useState<Employee>()
  const mutation = useMutation({
    mutationFn: async (employee: Employee) =>
      unwrap(
        await api.DELETE('/employees/{employee_id}', {
          params: { path: { employee_id: employee.id } },
        }),
      ),
    onSuccess: async () => {
      setRemoving(undefined)
      await queryClient.invalidateQueries({ queryKey: ['employees'] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <>
      <PageHeading
        eyebrow="Zarządzanie salonem"
        title="Ludzie, którzy tworzą miejsce."
        description="Zarządzaj zespołem, przypisuj usługi i łącz pracowników z ich kontami."
        action={
          <Button onClick={() => setEditing(null)}>
            <Plus className="size-4" />
            Dodaj pracownika
          </Button>
        }
      />
      {employees.isPending ? (
        <Loading />
      ) : employees.isError ? (
        <QueryError error={employees.error} retry={employees.refetch} />
      ) : employees.data.length === 0 ? (
        <EmptyState
          title="Zbuduj swój zespół"
          description="Dodaj pracownika, przypisz mu usługi i ustaw godziny pracy."
          action={<Button onClick={() => setEditing(null)}>Dodaj pracownika</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {employees.data.map((employee) => (
            <article key={employee.id} className="panel">
              <div className="flex items-start justify-between">
                <span className="flex size-12 items-center justify-center rounded-full bg-accent">
                  <UserRound className="size-5" />
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Edytuj ${employee.name}`}
                    onClick={() => setEditing(employee)}
                  >
                    <Pencil className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive"
                    aria-label={`Usuń ${employee.name}`}
                    onClick={() => {
                      mutation.reset()
                      setRemoving(employee)
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
              <h2 className="mt-5 text-lg font-semibold">{employee.name}</h2>
              <p className="mt-2 text-xs text-muted-foreground">Pracownik #{employee.id}</p>
              <Button
                className="mt-6 w-full"
                variant="outline"
                onClick={() => setManaging(employee)}
              >
                <Settings2 className="size-4" />
                Usługi i konto
              </Button>
            </article>
          ))}
        </div>
      )}
      <Dialog
        open={editing !== undefined}
        onOpenChange={(open) => {
          if (!open) setEditing(undefined)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edytuj pracownika' : 'Nowy pracownik'}</DialogTitle>
            <DialogDescription>
              Nazwa pracownika będzie widoczna podczas wyboru terminu.
            </DialogDescription>
          </DialogHeader>
          {editing !== undefined && (
            <EmployeeForm
              key={editing?.id ?? 'new'}
              employee={editing}
              onSaved={() => setEditing(undefined)}
            />
          )}
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!managing}
        onOpenChange={(open) => {
          if (!open) setManaging(undefined)
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{managing?.name}</DialogTitle>
            <DialogDescription>Przypisz usługi oraz konto pracownika.</DialogDescription>
          </DialogHeader>
          {managing && <EmployeeSettings key={managing.id} employee={managing} />}
        </DialogContent>
      </Dialog>
      <ConfirmDialog
        open={!!removing}
        onOpenChange={(open) => {
          if (!open) setRemoving(undefined)
        }}
        title="Usunąć pracownika?"
        description={`„${removing?.name ?? ''}” zostanie usunięty z zespołu. Pracownika z przypisanymi wizytami nie można usunąć.`}
        destructive
        pending={mutation.isPending}
        error={mutation.error}
        onConfirm={() => {
          if (removing) mutation.mutate(removing)
        }}
      />
    </>
  )
}

function EmployeeForm({ employee, onSaved }: { employee: Employee | null; onSaved: () => void }) {
  const form = useForm<z.infer<typeof employeeSchema>>({
    resolver: zodResolver(employeeSchema),
    defaultValues: { name: employee?.name ?? '' },
  })
  const mutation = useMutation({
    mutationFn: async (body: z.infer<typeof employeeSchema>) =>
      employee
        ? unwrap(
            await api.PUT('/employees/{employee_id}', {
              params: { path: { employee_id: employee.id } },
              body,
            }),
          )
        : unwrap(await api.POST('/employees', { body })),
    onSuccess: async () => {
      onSaved()
      await queryClient.invalidateQueries({ queryKey: ['employees'] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <form
      className="grid gap-5"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      {mutation.isError && <ErrorNotice error={mutation.error} />}
      <Field
        label="Imię i nazwisko / nazwa"
        id="employee-name"
        error={form.formState.errors.name?.message}
      >
        <Input id="employee-name" {...form.register('name')} />
      </Field>
      <Button disabled={mutation.isPending} type="submit">
        {mutation.isPending ? 'Zapisywanie…' : 'Zapisz pracownika'}
      </Button>
    </form>
  )
}

function EmployeeSettings({ employee }: { employee: Employee }) {
  const services = useServices()
  const assignments = useQuery({
    queryKey: ['employee-services', employee.id],
    queryFn: ({ signal }) => getEmployeeServices(employee.id, signal),
  })
  const mutation = useMutation({
    mutationFn: async ({ serviceId, remove }: { serviceId: number; remove: boolean }) => {
      const params = { path: { employee_id: employee.id, service_id: serviceId } }
      return remove
        ? unwrap(await api.DELETE('/employees/{employee_id}/services/{service_id}', { params }))
        : unwrap(await api.POST('/employees/{employee_id}/services/{service_id}', { params }))
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['employee-services', employee.id] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <div className="grid gap-6">
      <section>
        <h3 className="mb-3 text-sm font-semibold">Wykonywane usługi</h3>
        {mutation.isError && (
          <div className="mb-3">
            <ErrorNotice error={mutation.error} />
          </div>
        )}
        {services.isPending || assignments.isPending ? (
          <Loading />
        ) : services.isError ? (
          <QueryError error={services.error} retry={services.refetch} />
        ) : assignments.isError ? (
          <QueryError error={assignments.error} retry={assignments.refetch} />
        ) : services.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">Dodaj najpierw usługi do oferty salonu.</p>
        ) : (
          <div className="grid gap-2">
            {services.data.map((service) => {
              const checked = assignments.data.some((item) => item.id === service.id)
              return (
                <label
                  key={service.id}
                  className="flex cursor-pointer items-center gap-3 rounded-xl border p-3"
                >
                  <input
                    type="checkbox"
                    className="size-4 accent-primary"
                    checked={checked}
                    disabled={mutation.isPending}
                    onChange={() => mutation.mutate({ serviceId: service.id, remove: checked })}
                  />
                  <span className="flex-1 text-sm">{service.name}</span>
                  <span className="text-xs text-muted-foreground">{money(service.price)}</span>
                </label>
              )
            })}
          </div>
        )}
      </section>
      <section className="border-t pt-5">
        <h3 className="mb-2 text-sm font-semibold">Konto pracownika</h3>
        <p className="mb-4 text-xs leading-5 text-muted-foreground">
          Przypisz istniejące konto klienta. Jego właściciel znajdzie ID konta w widoku „Moje
          wizyty”. Po przypisaniu otrzyma dostęp do panelu pracownika.
        </p>
        <AccountForm employeeId={employee.id} />
      </section>
    </div>
  )
}

function AccountForm({ employeeId }: { employeeId: number }) {
  const form = useForm<z.infer<typeof accountSchema>>({ resolver: zodResolver(accountSchema) })
  const mutation = useMutation({
    mutationFn: async (body: z.infer<typeof accountSchema>) =>
      unwrap(
        await api.PUT('/employees/{employee_id}/account', {
          params: { path: { employee_id: employeeId } },
          body,
        }),
      ),
  })
  return (
    <form
      className="grid gap-3"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      {mutation.isError && <ErrorNotice error={mutation.error} />}
      {mutation.isSuccess && (
        <p role="status" className="text-sm text-emerald-700">
          Konto zostało przypisane do pracownika.
        </p>
      )}
      <Field
        label="ID konta użytkownika"
        id="account-id"
        error={form.formState.errors.user_id?.message}
      >
        <Input
          id="account-id"
          type="number"
          min="1"
          step="1"
          {...form.register('user_id', { valueAsNumber: true })}
        />
      </Field>
      <Button type="submit" variant="outline" disabled={mutation.isPending}>
        {mutation.isPending ? 'Przypisywanie…' : 'Przypisz konto'}
      </Button>
    </form>
  )
}
