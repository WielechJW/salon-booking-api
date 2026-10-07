import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'
import { Pencil, Plus, Scissors, Trash2 } from 'lucide-react'
import { api, unwrap, type Service } from '@/lib/api/client'
import { money } from '@/lib/dates'
import { queryClient, useServices } from '@/lib/query'
import { serviceSchema } from '@/lib/validation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
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

export function AdminServicesPage() {
  const services = useServices()
  const [editing, setEditing] = useState<Service | null | undefined>()
  const [removing, setRemoving] = useState<Service>()
  const mutation = useMutation({
    mutationFn: async (service: Service) =>
      unwrap(
        await api.DELETE('/services/{service_id}', {
          params: { path: { service_id: service.id } },
        }),
      ),
    onSuccess: async () => {
      setRemoving(undefined)
      await queryClient.invalidateQueries({ queryKey: ['services'] })
      await queryClient.invalidateQueries({ queryKey: ['employee-services'] })
      await queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
  return (
    <>
      <PageHeading
        eyebrow="Zarządzanie salonem"
        title="Oferta, która przyciąga."
        description="Dodawaj usługi, aktualizuj ceny i czas trwania. Istniejące wizyty zachowują cenę i czas z chwili rezerwacji."
        action={
          <Button onClick={() => setEditing(null)}>
            <Plus className="size-4" />
            Dodaj usługę
          </Button>
        }
      />
      {services.isPending ? (
        <Loading />
      ) : services.isError ? (
        <QueryError error={services.error} retry={services.refetch} />
      ) : services.data.length === 0 ? (
        <EmptyState
          title="Dodaj pierwszą usługę"
          description="Po dodaniu i przypisaniu do pracownika klienci będą mogli szukać terminów."
          action={<Button onClick={() => setEditing(null)}>Dodaj usługę</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {services.data.map((service) => (
            <article key={service.id} className="panel">
              <div className="flex items-start justify-between gap-4">
                <span className="flex size-10 items-center justify-center rounded-xl bg-accent">
                  <Scissors className="size-5" />
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Edytuj ${service.name}`}
                    onClick={() => setEditing(service)}
                  >
                    <Pencil className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive"
                    aria-label={`Usuń ${service.name}`}
                    onClick={() => {
                      mutation.reset()
                      setRemoving(service)
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
              <h2 className="mt-5 text-lg font-semibold">{service.name}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{service.description}</p>
              <div className="mt-6 flex justify-between border-t pt-4 text-sm">
                <span className="text-muted-foreground">{service.duration_minutes} min</span>
                <span className="font-semibold">{money(service.price)}</span>
              </div>
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
            <DialogTitle>{editing ? 'Edytuj usługę' : 'Nowa usługa'}</DialogTitle>
            <DialogDescription>
              Ustal nazwę, czas trwania i cenę widoczne dla klientów.
            </DialogDescription>
          </DialogHeader>
          {editing !== undefined && (
            <ServiceForm
              key={editing?.id ?? 'new'}
              service={editing}
              onSaved={() => setEditing(undefined)}
            />
          )}
        </DialogContent>
      </Dialog>
      <ConfirmDialog
        open={!!removing}
        onOpenChange={(open) => {
          if (!open) setRemoving(undefined)
        }}
        title="Usunąć usługę?"
        description={`Usługa „${removing?.name ?? ''}” zniknie z oferty. Usługi powiązanej z wizytami nie można usunąć.`}
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

function ServiceForm({ service, onSaved }: { service: Service | null; onSaved: () => void }) {
  const form = useForm<z.infer<typeof serviceSchema>>({
    resolver: zodResolver(serviceSchema),
    defaultValues: {
      name: service?.name ?? '',
      description: service?.description ?? '',
      duration_minutes: service?.duration_minutes ?? 30,
      price: service?.price.toFixed(2) ?? '',
    },
  })
  const mutation = useMutation({
    mutationFn: async (values: z.infer<typeof serviceSchema>) => {
      const body = { ...values, price: values.price.replace(',', '.') }
      return service
        ? unwrap(
            await api.PUT('/services/{service_id}', {
              params: { path: { service_id: service.id } },
              body,
            }),
          )
        : unwrap(await api.POST('/services', { body }))
    },
    onSuccess: async () => {
      onSaved()
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['services'] }),
        queryClient.invalidateQueries({ queryKey: ['employee-services'] }),
        queryClient.invalidateQueries({ queryKey: ['availability'] }),
      ])
    },
  })
  return (
    <form
      className="grid gap-5"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      {mutation.isError && <ErrorNotice error={mutation.error} />}
      <Field label="Nazwa usługi" id="service-name" error={form.formState.errors.name?.message}>
        <Input id="service-name" {...form.register('name')} />
      </Field>
      <Field
        label="Opis"
        id="service-description"
        error={form.formState.errors.description?.message}
      >
        <Textarea id="service-description" rows={3} {...form.register('description')} />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field
          label="Czas trwania (min)"
          id="service-duration"
          error={form.formState.errors.duration_minutes?.message}
        >
          <Input
            id="service-duration"
            type="number"
            min="1"
            step="1"
            {...form.register('duration_minutes', { valueAsNumber: true })}
          />
        </Field>
        <Field label="Cena (PLN)" id="service-price" error={form.formState.errors.price?.message}>
          <Input
            id="service-price"
            inputMode="decimal"
            placeholder="80,00"
            {...form.register('price')}
          />
        </Field>
      </div>
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Zapisywanie…' : 'Zapisz usługę'}
      </Button>
    </form>
  )
}
