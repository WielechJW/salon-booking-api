import { z } from 'zod'

export const personName = z
  .string()
  .trim()
  .min(2, 'Wpisz co najmniej 2 znaki.')
  .max(100, 'Maksymalnie 100 znaków.')
export const email = z.string().trim().email('Podaj poprawny adres email.').max(254)
export const phone = z
  .string()
  .trim()
  .transform((value) => value.replace(/[\s()-]/g, ''))
  .pipe(z.string().regex(/^\+?\d{7,15}$/, 'Podaj numer zawierający od 7 do 15 cyfr.'))
export const password = z
  .string()
  .min(8, 'Hasło musi mieć co najmniej 8 znaków.')
  .max(128, 'Maksymalnie 128 znaków.')
export const contactSchema = z.object({
  client_name: personName,
  client_email: email,
  client_phone: phone,
})
export const loginSchema = z.object({ email, password: z.string().min(1, 'Wpisz hasło.').max(128) })
export const registerSchema = z.object({
  email,
  password,
  first_name: personName,
  last_name: personName,
  phone,
})
export const serviceSchema = z.object({
  name: personName,
  description: z.string().trim().min(5, 'Wpisz co najmniej 5 znaków.').max(500),
  duration_minutes: z
    .number()
    .int('Podaj pełne minuty.')
    .positive('Czas musi być większy od zera.'),
  price: z
    .string()
    .regex(/^\d+(?:[.,]\d{1,2})?$/, 'Podaj cenę z maksymalnie 2 miejscami po przecinku.')
    .refine((value) => Number(value.replace(',', '.')) <= 99_999_999.99, 'Cena jest zbyt duża.'),
})
