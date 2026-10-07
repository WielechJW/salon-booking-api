import { Link } from 'react-router'
import { ArrowUpRight, Clock3, Scissors } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState, Loading, PageHeading, QueryError } from '@/components/shared'
import { useServices } from '@/lib/query'
import { money } from '@/lib/dates'

export function ServicesPage() {
  const services = useServices()
  return (
    <>
      <PageHeading
        eyebrow="Oferta salonu"
        title="Znajdź coś dla siebie."
        description="Poznaj nasze usługi. Wybierz swoją i sprawdź najbliższe wolne terminy."
      />
      {services.isPending ? (
        <Loading />
      ) : services.isError ? (
        <QueryError error={services.error} retry={services.refetch} />
      ) : services.data.length === 0 ? (
        <EmptyState
          title="Oferta jest w przygotowaniu"
          description="Usługi pojawią się tutaj po dodaniu ich przez salon."
        />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {services.data.map((service) => (
            <article key={service.id} className="panel flex flex-col">
              <span className="mb-8 flex size-12 items-center justify-center rounded-2xl bg-accent">
                <Scissors className="size-5" />
              </span>
              <h2 className="text-xl font-semibold">{service.name}</h2>
              <p className="mt-3 flex-1 text-sm leading-6 text-muted-foreground">
                {service.description}
              </p>
              <div className="mb-6 mt-7 flex items-center justify-between border-t pt-5">
                <span className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock3 className="size-3.5" />
                  {service.duration_minutes} min
                </span>
                <span className="text-lg font-semibold">{money(service.price)}</span>
              </div>
              <Button asChild>
                <Link to={`/?service=${service.id}`}>
                  Wybierz termin
                  <ArrowUpRight className="size-4" />
                </Link>
              </Button>
            </article>
          ))}
        </div>
      )}
    </>
  )
}
