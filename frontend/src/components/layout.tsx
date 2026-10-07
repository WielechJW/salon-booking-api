import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router'
import {
  ArrowUpRight,
  CalendarDays,
  CalendarPlus,
  Clock3,
  LayoutDashboard,
  LogOut,
  Menu,
  Scissors,
  Users,
  X,
} from 'lucide-react'
import { useAuth } from '@/auth'
import { Button } from '@/components/ui/button'
import { useSalon } from '@/lib/query'
import { cn } from '@/lib/utils'

const roleLabels = { CLIENT: 'Konto klienta', EMPLOYEE: 'Konto pracownika', ADMIN: 'Administrator' }

export function Layout() {
  const { user, logout, expired, loading } = useAuth()
  const salon = useSalon()
  const location = useLocation()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const links = [
    { path: '/', label: 'Umów wizytę', icon: CalendarPlus },
    { path: '/services', label: 'Nasze usługi', icon: Scissors },
    { path: '/account', label: 'Moje wizyty', icon: CalendarDays },
    ...(user?.role === 'EMPLOYEE'
      ? [
          { path: '/staff', label: 'Wizyty klientów', icon: LayoutDashboard },
          { path: '/staff/schedule', label: 'Mój grafik', icon: Clock3 },
        ]
      : []),
    ...(user?.role === 'ADMIN'
      ? [
          { path: '/admin', label: 'Rezerwacje salonu', icon: LayoutDashboard },
          { path: '/admin/services', label: 'Zarządzaj usługami', icon: Scissors },
          { path: '/admin/employees', label: 'Zespół', icon: Users },
          { path: '/admin/schedule', label: 'Grafiki i urlopy', icon: Clock3 },
        ]
      : []),
  ]
  const navigation = (
    <nav aria-label="Nawigacja główna" className="grid gap-1.5">
      {links.map(({ path, label, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
          end
          onClick={() => setMenuOpen(false)}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition-colors',
              isActive
                ? 'bg-[#e1efbb] font-medium text-[#203c36]'
                : 'text-white/70 hover:bg-white/8 hover:text-white',
            )
          }
        >
          <Icon className="size-[18px]" />
          {label}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[244px_minmax(0,1fr)]">
      <aside className="sticky top-0 hidden h-screen flex-col bg-primary px-5 py-8 text-white lg:flex">
        <Link to="/" className="px-4">
          <span className="flex items-center gap-2 text-3xl font-semibold tracking-tight">
            studio<span className="text-[#e1efbb]">.</span>
          </span>
          <span className="mt-2 block text-[9px] tracking-[0.22em] text-white/45">
            TWÓJ CZAS. TWOJE MIEJSCE.
          </span>
        </Link>
        <p className="mb-4 mt-12 px-4 text-[10px] font-medium tracking-[0.18em] text-white/35">
          REZERWACJE
        </p>
        {navigation}
        <div className="mt-auto px-4 pt-8">
          <div className="mb-7 rounded-xl border border-white/10 p-4">
            <Scissors className="mb-3 size-5 text-[#e1efbb]" />
            <p className="text-sm font-medium">
              Mała zmiana.
              <br />
              Dobry dzień.
            </p>
            <p className="mt-2 text-xs leading-5 text-white/45">Znajdź chwilę dla siebie.</p>
          </div>
          <p className="flex items-center gap-2 text-[10px] text-white/45">
            <Clock3 className="size-3" />
            {salon.data?.timezone ?? 'Strefa czasowa salonu'}
          </p>
        </div>
      </aside>
      <div className="min-w-0">
        <div className="sticky top-0 z-30 bg-primary px-5 py-4 text-white lg:hidden">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-semibold tracking-tight">
              studio<span className="text-[#e1efbb]">.</span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10 hover:text-white"
              aria-label={menuOpen ? 'Zamknij menu' : 'Otwórz menu'}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? <X /> : <Menu />}
            </Button>
          </div>
          {menuOpen && <div className="pt-5">{navigation}</div>}
        </div>
        <header className="flex min-h-20 items-center justify-between gap-3 border-b px-5 sm:px-8 xl:px-12">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span
              className={cn(
                'size-1.5 rounded-full',
                salon.isError ? 'bg-red-500' : salon.data ? 'bg-emerald-600' : 'bg-amber-500',
              )}
            />
            <span>{salon.isError ? 'API niedostępne' : 'Rezerwacje online'}</span>
            <span className="hidden text-border sm:inline">/</span>
            <span className="hidden sm:inline">{salon.data?.timezone.replace('_', ' ')}</span>
          </div>
          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-[10px] text-muted-foreground">{roleLabels[user.role]}</p>
              </div>
              <span
                className="flex size-9 items-center justify-center rounded-full bg-accent text-xs font-semibold"
                aria-hidden="true"
              >
                {user.first_name[0]}
                {user.last_name[0]}
              </span>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Wyloguj się"
                onClick={() => {
                  logout()
                  navigate('/', { replace: true })
                }}
              >
                <LogOut className="size-4" />
              </Button>
            </div>
          ) : (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}>
                {loading ? 'Sprawdzanie konta…' : 'Zaloguj się'}
                <ArrowUpRight className="size-3.5" />
              </Link>
            </Button>
          )}
        </header>
        <main id="main" className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 sm:py-10 xl:px-12">
          {expired && !user && (
            <div
              role="status"
              className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              Sesja wygasła. Zaloguj się ponownie, aby kontynuować.
            </div>
          )}
          <div className="page-enter" key={location.pathname}>
            <Outlet />
          </div>
        </main>
        <footer className="flex flex-wrap justify-between gap-2 px-5 pb-6 text-[10px] text-muted-foreground sm:px-8 xl:px-12">
          <span>studio. / Salon Booking</span>
          <span>Wszystkie godziny podajemy w strefie salonu.</span>
        </footer>
      </div>
    </div>
  )
}
