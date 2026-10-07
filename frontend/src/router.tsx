import { createBrowserRouter, Link, Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from '@/auth'
import { Layout } from '@/components/layout'
import { EmptyState, Loading, QueryError } from '@/components/shared'
import { Button } from '@/components/ui/button'
import type { User } from '@/lib/api/client'

function ProtectedRoute({ roles }: { roles?: User['role'][] }) {
  const { user, loading, error, retry } = useAuth()
  const location = useLocation()
  if (loading) return <Loading label="Sprawdzanie sesji…" />
  if (error) return <QueryError error={error} retry={retry} />
  if (!user)
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
        replace
      />
    )
  if (roles && !roles.includes(user.role))
    return (
      <EmptyState
        title="Ten widok wymaga innej roli"
        description="Twoje konto nie ma dostępu do tego panelu."
        action={
          <Button asChild>
            <Link to="/account">Przejdź do swoich wizyt</Link>
          </Button>
        }
      />
    )
  return <Outlet />
}

function NotFound() {
  return (
    <EmptyState
      title="Nie znaleźliśmy tej strony"
      description="Wróć do rezerwacji i znajdź swój termin."
      action={
        <Button asChild>
          <Link to="/">Umów wizytę</Link>
        </Button>
      }
    />
  )
}

function RouteError() {
  return (
    <div className="mx-auto max-w-xl p-8">
      <EmptyState
        title="Nie udało się wyświetlić strony"
        description="Odśwież aplikację i spróbuj ponownie."
        action={<Button onClick={() => window.location.reload()}>Odśwież stronę</Button>}
      />
    </div>
  )
}

export const router = createBrowserRouter([
  {
    element: <Layout />,
    hydrateFallbackElement: <Loading label="Uruchamianie aplikacji…" />,
    errorElement: <RouteError />,
    children: [
      {
        index: true,
        lazy: async () => ({ Component: (await import('@/pages/booking')).BookingPage }),
      },
      {
        path: 'services',
        lazy: async () => ({ Component: (await import('@/pages/services')).ServicesPage }),
      },
      { path: 'login', lazy: async () => ({ Component: (await import('@/pages/auth')).AuthPage }) },
      {
        path: 'register',
        lazy: async () => {
          const { AuthPage } = await import('@/pages/auth')
          return { Component: () => <AuthPage register /> }
        },
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: 'account',
            lazy: async () => {
              const { AppointmentsPage } = await import('@/pages/appointments')
              return { Component: () => <AppointmentsPage mode="client" /> }
            },
          },
        ],
      },
      {
        element: <ProtectedRoute roles={['EMPLOYEE']} />,
        children: [
          {
            path: 'staff',
            lazy: async () => {
              const { AppointmentsPage } = await import('@/pages/appointments')
              return { Component: () => <AppointmentsPage mode="staff" /> }
            },
          },
          {
            path: 'staff/schedule',
            lazy: async () => ({ Component: (await import('@/pages/schedule')).SchedulePage }),
          },
        ],
      },
      {
        element: <ProtectedRoute roles={['ADMIN']} />,
        children: [
          {
            path: 'admin',
            lazy: async () => {
              const { AppointmentsPage } = await import('@/pages/appointments')
              return { Component: () => <AppointmentsPage mode="admin" /> }
            },
          },
          {
            path: 'admin/services',
            lazy: async () => ({
              Component: (await import('@/pages/admin-services')).AdminServicesPage,
            }),
          },
          {
            path: 'admin/employees',
            lazy: async () => ({
              Component: (await import('@/pages/admin-employees')).AdminEmployeesPage,
            }),
          },
          {
            path: 'admin/schedule',
            lazy: async () => {
              const { SchedulePage } = await import('@/pages/schedule')
              return { Component: () => <SchedulePage admin /> }
            },
          },
        ],
      },
      { path: '*', Component: NotFound },
    ],
  },
])
