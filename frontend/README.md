# Studio — Salon Booking frontend

Polski, responsywny frontend do istniejącego FastAPI. Wszystkie dane pochodzą z API;
aplikacja nie dodaje przykładowych pracowników ani usług do bazy salonu.

## Uruchomienie lokalne

W katalogu głównym uruchom backend zgodnie z głównym README, np.
`docker compose up --build api db`. Następnie w drugim terminalu:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Otwórz http://localhost:5173. Proxy `/api` domyślnie wskazuje
`http://127.0.0.1:18000`, zgodnie z backendowym `.env.example`.
Jeżeli API działa na porcie 8000, ustaw `API_PROXY_TARGET=http://127.0.0.1:8000`
w `frontend/.env`. Po zmianie uruchom ponownie Vite.

Cały stack można również uruchomić z katalogu głównego:

```bash
docker compose up --build
```

Frontend będzie dostępny na http://localhost:3000 (`FRONTEND_PORT`). Nginx serwuje
statyczny build, obsługuje bezpośrednie wejścia na podstrony i przekazuje `/api/`
do FastAPI. Dzięki wspólnemu originowi nie trzeba dodawać CORS do backendu.

## Widoki

| Adres                 | Dostęp     | Funkcje                                                             |
| --------------------- | ---------- | ------------------------------------------------------------------- |
| `/`                   | Publiczny  | Wybór usługi, dnia, pracownika i terminu; rezerwacja po zalogowaniu |
| `/services`           | Publiczny  | Oferta salonu z cenami i czasem trwania                             |
| `/login`, `/register` | Publiczny  | Logowanie i rejestracja                                             |
| `/account`            | Zalogowani | Własne wizyty, filtry, paginacja, anulowanie                        |
| `/staff`              | EMPLOYEE   | Wizyty własnego kalendarza i dozwolone zmiany statusów              |
| `/staff/schedule`     | EMPLOYEE   | Własny grafik, tworzenie/edycja/usuwanie blokad czasu               |
| `/admin`              | ADMIN      | Rezerwacje salonu, filtry i zmiany statusów                         |
| `/admin/services`     | ADMIN      | Dodawanie, edycja i usuwanie usług                                  |
| `/admin/employees`    | ADMIN      | Pracownicy, przypisania usług oraz kont                             |
| `/admin/schedule`     | ADMIN      | Grafiki i blokady czasu wszystkich pracowników                      |

Pierwszego administratora utwórz przez istniejące `python -m app.cli create-admin`.
Konto pracownika powstaje przez rejestrację klienta, a następnie przypisanie jego ID
w panelu zespołu. Użytkownik widzi ID swojego konta w „Moich wizytach”.

## Stack i struktura

React, TypeScript, Vite, React Router w Data Mode, TanStack Query, Tailwind CSS,
komponenty shadcn/ui oparte na Radix, React Hook Form, Zod, openapi-typescript,
openapi-fetch oraz date-fns z `@date-fns/tz`.

```text
src/
├── auth.tsx              # Sesja i profil użytkownika
├── router.tsx            # Trasy, role, lazy loading
├── components/
│   ├── ui/               # Komponenty shadcn/ui
│   ├── layout.tsx        # Nawigacja i responsywny układ
│   └── shared.tsx        # Formularze, stany ładowania, błędy, dialogi
├── lib/
│   ├── api/              # Typowany klient i wygenerowany kontrakt
│   ├── dates.ts          # Strefa salonu i konwersje dat
│   ├── query.ts          # Cache i odświeżanie danych
│   └── validation.ts     # Walidacja formularzy
└── pages/                # Rezerwacje, logowanie i zarządzanie salonem
```

Po zmianie backendowych schematów lub endpointów zregeneruj kontrakt:

```bash
npm run api:generate
```

Polecenie korzysta z `../.venv/bin/python`, ewentualnie `python3`; własny interpreter
można wskazać zmienną `PYTHON`. Eksport nie uruchamia serwera ani migracji.
`openapi.json` i wygenerowane typy są zapisane w repo, więc build frontu nie wymaga
działającego backendu ani Pythona.

## Sesja, daty i zakres MVP

- Access token jest przechowywany w pamięci oraz `sessionStorage` bieżącej karty.
  Wylogowanie, wygaśnięcie tokenu lub `401` usuwają sesję i cache danych użytkownika.
  API nie ma refresh tokenów; po wygaśnięciu sesji potrzebne jest ponowne logowanie.
  `sessionStorage` nie chroni tokenu przed XSS; przy rozbudowie produkcyjnego
  uwierzytelniania warto dodać sesję opartą na HttpOnly cookies po stronie serwera.
- Role frontendowe sterują widocznością widoków. Faktyczne uprawnienia nadal
  sprawdza backend przy każdym żądaniu.
- Strefa jest odczytywana z publicznego `GET /salon`; profil `GET /users/me`
  udostępnia własny `employee_id`. Te dodatki nie wymagają migracji.
- Kreator używa dokładnych `start_at` z `GET /availability`. Zajęcie terminu przez
  inną osobę powoduje komunikat `409`, odświeżenie dostępności i ponowny wybór godziny.
- Ceny usług są wysyłane jako ciągi dziesiętne, żeby zachować dokładność walidacji
  Decimal. Formularze blokad czasu interpretują daty w strefie salonu i odrzucają
  nieistniejące lub niejednoznaczne godziny przy zmianie czasu.
- MVP używa list wizyt z filtrami i paginacją. Pełny kalendarz, zarządzanie
  katalogiem klientów, przenoszenie wizyt i usuwanie dnia grafiku to dalsze etapy.

## Weryfikacja

```bash
npm run build
npm run lint
npm test
npm run test:e2e
```

Testy jednostkowe sprawdzają granice dat i zmianę czasu. Testy Playwright używają
zainstalowanego Google Chrome oraz backendowych zależności Pythona. Uruchamiają
oddzielne API na porcie 18100 i Vite na 5180, z nową tymczasową bazą SQLite w `/tmp`;
nie korzystają z bazy salonu. Sprawdzają rezerwację przez logowanie, anulowanie,
rejestrację, konflikt terminu, role, sesję, operacje administratora i widok mobilny.
