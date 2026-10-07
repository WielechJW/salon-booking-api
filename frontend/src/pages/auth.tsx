import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'
import { ArrowRight, LockKeyhole } from 'lucide-react'
import { useAuth, safeReturnTo } from '@/auth'
import { api, unwrap } from '@/lib/api/client'
import { loginSchema, registerSchema } from '@/lib/validation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ErrorNotice, Field, Loading } from '@/components/shared'

type LoginValues = z.infer<typeof loginSchema>
type RegisterValues = z.infer<typeof registerSchema>

export function AuthPage({ register = false }: { register?: boolean }) {
  const { user, loading } = useAuth()
  const [search] = useSearchParams()
  const next = safeReturnTo(search.get('next'))
  if (loading) return <Loading label="Sprawdzanie sesji…" />
  if (user) return <Navigate to={next} replace />
  return (
    <div className="mx-auto grid max-w-4xl overflow-hidden rounded-3xl border bg-white md:grid-cols-[0.85fr_1.15fr]">
      <div className="flex flex-col justify-between bg-primary p-8 text-white sm:p-10">
        <div>
          <p className="text-[10px] tracking-[0.18em] text-white/50">MIŁO CIĘ WIDZIEĆ</p>
          <h1 className="mt-6 text-4xl font-medium leading-tight">
            Dobra wizyta
            <br />
            zaczyna się
            <br />
            <span className="text-[#e1efbb]">tutaj.</span>
          </h1>
          <p className="mt-6 max-w-xs text-sm leading-6 text-white/60">
            Twoje rezerwacje, ulubione chwile i wszystko, czego potrzebujesz przed wizytą.
          </p>
        </div>
        <div className="mt-12 flex items-center gap-3 text-xs text-white/50">
          <LockKeyhole className="size-4" />
          Twoje własne konto w salonie
        </div>
      </div>
      <div className="p-7 sm:p-10">
        <h2 className="text-2xl font-semibold">{register ? 'Stwórz konto' : 'Zaloguj się'}</h2>
        <p className="mb-7 mt-2 text-sm text-muted-foreground">
          {register
            ? 'Wypełnij dane i zarezerwuj swój czas.'
            : 'Witaj ponownie. Twoje terminy już czekają.'}
        </p>
        {register ? <RegisterForm next={next} /> : <LoginForm next={next} />}
        <p className="mt-6 text-center text-xs text-muted-foreground">
          {register ? 'Masz już konto?' : 'Pierwsza wizyta?'}{' '}
          <Link
            className="font-semibold text-primary underline underline-offset-4"
            to={`/${register ? 'login' : 'register'}?next=${encodeURIComponent(next)}`}
          >
            {register ? 'Zaloguj się' : 'Załóż konto'}
          </Link>
        </p>
      </div>
    </div>
  )
}

function LoginForm({ next }: { next: string }) {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>()
  const form = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })
  const submit = form.handleSubmit(async (values) => {
    setError(undefined)
    try {
      await login(values.email, values.password)
      navigate(next, { replace: true })
    } catch (error) {
      setError(error)
    }
  })
  return (
    <form className="grid gap-5" onSubmit={submit} noValidate>
      {!!error && <ErrorNotice error={error} />}
      <Field label="Email" id="email" error={form.formState.errors.email?.message}>
        <Input
          id="email"
          type="email"
          autoComplete="username"
          placeholder="ty@example.com"
          aria-invalid={!!form.formState.errors.email}
          {...form.register('email')}
        />
      </Field>
      <Field label="Hasło" id="password" error={form.formState.errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          aria-invalid={!!form.formState.errors.password}
          {...form.register('password')}
        />
      </Field>
      <Button className="mt-1" type="submit" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? 'Logowanie…' : 'Zaloguj się'}
        <ArrowRight className="size-4" />
      </Button>
    </form>
  )
}

function RegisterForm({ next }: { next: string }) {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>()
  const form = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })
  const submit = form.handleSubmit(async (values) => {
    setError(undefined)
    try {
      unwrap(await api.POST('/auth/register', { body: values }))
      await login(values.email, values.password)
      navigate(next, { replace: true })
    } catch (error) {
      setError(error)
    }
  })
  return (
    <form className="grid gap-4" onSubmit={submit} noValidate>
      {!!error && <ErrorNotice error={error} />}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Imię" id="first_name" error={form.formState.errors.first_name?.message}>
          <Input id="first_name" autoComplete="given-name" {...form.register('first_name')} />
        </Field>
        <Field label="Nazwisko" id="last_name" error={form.formState.errors.last_name?.message}>
          <Input id="last_name" autoComplete="family-name" {...form.register('last_name')} />
        </Field>
      </div>
      <Field label="Email" id="email" error={form.formState.errors.email?.message}>
        <Input id="email" type="email" autoComplete="email" {...form.register('email')} />
      </Field>
      <Field label="Telefon" id="phone" error={form.formState.errors.phone?.message}>
        <Input
          id="phone"
          type="tel"
          autoComplete="tel"
          placeholder="+48 123 456 789"
          {...form.register('phone')}
        />
      </Field>
      <Field
        label="Hasło"
        id="password"
        error={form.formState.errors.password?.message}
        hint="Od 8 do 128 znaków."
      >
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          {...form.register('password')}
        />
      </Field>
      <Button className="mt-2" type="submit" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? 'Tworzenie konta…' : 'Stwórz konto'}
        <ArrowRight className="size-4" />
      </Button>
    </form>
  )
}
