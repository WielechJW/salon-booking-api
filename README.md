# Salon Booking API

Backend systemu do rezerwacji wizyt w salonie fryzjerskim, inspirowany rozwiązaniami typu Booksy.

Celem projektu jest stworzenie kompletnego REST API umożliwiającego zarządzanie pracownikami, usługami, grafikami oraz rezerwacjami klientów.

Projekt powstaje przede wszystkim jako projekt edukacyjny do nauki:

- Python
- FastAPI
- REST API
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT Authentication
- Pytest
- Docker

---

## Główne założenia

Salon posiada wielu pracowników.

Każdy pracownik:

- może wykonywać różne usługi,
- posiada własny grafik pracy,
- może mieć przerwy i dni wolne,
- może posiadać własne rezerwacje.

Każda usługa posiada:

- nazwę,
- opis,
- cenę,
- czas trwania.

Klient będzie mógł:

1. wybrać usługę,
2. wybrać pracownika,
3. wybrać dzień,
4. zobaczyć dostępne godziny,
5. zarezerwować wizytę,
6. anulować wizytę,
7. przeglądać swoje rezerwacje.

---

# Plan rozwoju

## Etap 1 — Podstawy FastAPI

Pierwszym celem jest stworzenie prostej aplikacji FastAPI bez bazy danych.

### Funkcjonalności

- uruchomienie serwera FastAPI,
- utworzenie pierwszych endpointów,
- obsługa requestów i response,
- testowanie API przez Swagger UI,
- przechowywanie danych tymczasowo w pamięci.

### Endpointy

```text
GET    /employees
POST   /employees

GET    /services
POST   /services

GET    /appointments
POST   /appointments
```

### Cel edukacyjny

Poznanie:

- `GET`
- `POST`
- `PUT`
- `DELETE`
- path parameters
- query parameters
- status codes
- podstaw FastAPI

---

## Etap 2 — Pydantic i walidacja danych

Dodanie modeli danych oraz walidacji requestów.

Przykładowe modele:

```text
Employee
Service
Appointment
```

Przykładowa usługa:

```json
{
  "name": "Strzyżenie męskie",
  "duration_minutes": 45,
  "price": 80
}
```

### Cel edukacyjny

Poznanie:

- Pydantic
- BaseModel
- walidacji danych
- request models
- response models
- typowania w Pythonie

---

## Etap 3 — PostgreSQL

Dane przestają być przechowywane w pamięci aplikacji.

Do projektu zostanie dodana baza:

```text
PostgreSQL
```

### Główne tabele

```text
employees
services
appointments
```

### Technologie

```text
SQLAlchemy
PostgreSQL
```

### Cel edukacyjny

Poznanie:

- relacyjnych baz danych,
- SQL,
- ORM,
- modeli SQLAlchemy,
- zapisywania danych,
- pobierania danych,
- aktualizowania danych,
- usuwania danych.

---

## Etap 4 — Migracje bazy danych

Do projektu zostanie dodany:

```text
Alembic
```

Pozwoli to kontrolować zmiany struktury bazy danych.

Przykład:

```text
dodanie kolumny
↓
utworzenie migracji
↓
uruchomienie migracji
↓
aktualizacja bazy
```

### Cel edukacyjny

Poznanie zarządzania zmianami schematu bazy danych.

---

## Etap 5 — Pracownicy i usługi

Nie każdy pracownik wykonuje wszystkie usługi.

Powstanie relacja:

```text
Employee
   ↕
EmployeeService
   ↕
Service
```

Przykład:

```text
Bartek
├── Strzyżenie męskie
├── Broda
└── Strzyżenie + broda

Anna
├── Strzyżenie damskie
├── Koloryzacja
└── Modelowanie
```

### Endpointy

```text
GET /employees/{employee_id}/services

POST /employees/{employee_id}/services/{service_id}

DELETE /employees/{employee_id}/services/{service_id}
```

### Cel edukacyjny

Poznanie:

- relacji many-to-many,
- foreign keys,
- join tables,
- bardziej złożonych zapytań SQL.

---

# Etap 6 — Grafik pracowników

Każdy pracownik będzie posiadał własne godziny pracy.

Przykład:

```text
Poniedziałek
09:00 - 17:00

Wtorek
10:00 - 18:00

Środa
09:00 - 17:00
```

Model:

```text
Schedule

id
employee_id
day_of_week
start_time
end_time
```

### Endpointy

```text
GET  /employees/{id}/schedule

POST /employees/{id}/schedule

PUT  /employees/{id}/schedule
```

### Cel edukacyjny

Praca z:

- datami,
- godzinami,
- biblioteką `datetime`,
- logiką biznesową.

---

# Etap 7 — System dostępności

Jedna z najważniejszych funkcjonalności projektu.

System będzie obliczał dostępne godziny wizyt.

Przykład:

Pracownik pracuje:

```text
09:00 - 17:00
```

Usługa trwa:

```text
45 minut
```

Istniejące rezerwacje:

```text
10:30 - 11:15
13:00 - 13:45
```

API powinno zwrócić tylko dostępne terminy.

### Endpoint

```text
GET /employees/{id}/availability
```

Przykład:

```text
GET /employees/2/availability?date=2026-09-20&service_id=3
```

Response:

```json
{
  "employee_id": 2,
  "date": "2026-09-20",
  "available_slots": [
    "09:00",
    "09:45",
    "11:15",
    "12:00",
    "14:30",
    "15:15"
  ]
}
```

### Backend musi uwzględniać

- godziny pracy pracownika,
- długość usługi,
- istniejące rezerwacje,
- przerwy,
- dni wolne,
- kolizje terminów.

### Cel edukacyjny

Tworzenie prawdziwej logiki biznesowej zamiast prostego CRUD.

---

# Etap 8 — System rezerwacji

Klient będzie mógł utworzyć rezerwację.

### Endpoint

```text
POST /appointments
```

Przykład:

```json
{
  "employee_id": 2,
  "service_id": 3,
  "start_at": "2026-09-20T10:30:00",
  "client_name": "Jan Kowalski",
  "client_email": "jan@example.com",
  "client_phone": "123456789"
}
```

Backend musi sprawdzić:

- czy pracownik istnieje,
- czy usługa istnieje,
- czy pracownik wykonuje tę usługę,
- czy pracownik pracuje w tym czasie,
- czy termin jest wolny,
- czy usługa zmieści się przed końcem pracy.

Status rezerwacji:

```text
pending
confirmed
cancelled
completed
```

---

# Etap 9 — Urlopy, przerwy i wyjątki

Dodanie możliwości blokowania czasu pracownika.

Przykłady:

```text
urlop
choroba
przerwa obiadowa
szkolenie
prywatna blokada czasu
```

Model:

```text
EmployeeTimeOff

id
employee_id
start_at
end_at
reason
```

System dostępności musi automatycznie uwzględniać takie blokady.

---

# Etap 10 — Użytkownicy

Dodanie kont klientów.

Model:

```text
User

id
email
password_hash
first_name
last_name
phone
```

Klient będzie mógł:

```text
GET /users/me

GET /users/me/appointments
```

---

# Etap 11 — Authentication

Dodanie:

```text
JWT Authentication
```

Endpointy:

```text
POST /auth/register
POST /auth/login

GET /users/me
```

Role użytkowników:

```text
CLIENT

EMPLOYEE

ADMIN
```

### Uprawnienia

CLIENT:

```text
rezerwowanie wizyt
anulowanie własnych wizyt
historia wizyt
```

EMPLOYEE:

```text
własny grafik
własne wizyty
zmiana statusu wizyty
```

ADMIN:

```text
pracownicy
usługi
grafiki
wszystkie rezerwacje
zarządzanie salonem
```

---

# Etap 12 — Zaawansowane wyszukiwanie terminów

Klient nie musi wybierać konkretnego pracownika.

Przykład:

```text
GET /availability?service_id=3&date=2026-09-20
```

API może zwrócić:

```json
[
  {
    "employee": "Bartek",
    "time": "10:00"
  },
  {
    "employee": "Kamil",
    "time": "10:15"
  },
  {
    "employee": "Bartek",
    "time": "11:30"
  }
]
```

System wyszukuje wszystkich pracowników, którzy:

- wykonują daną usługę,
- pracują danego dnia,
- posiadają wolny termin.

---

# Etap 13 — Testy

Do projektu zostanie dodany:

```text
Pytest
```

Testowane będą między innymi:

- tworzenie pracowników,
- tworzenie usług,
- tworzenie rezerwacji,
- walidacja danych,
- generowanie dostępnych terminów,
- wykrywanie konfliktów rezerwacji,
- autoryzacja użytkowników.

---

# Etap 14 — Docker

Backend oraz baza danych zostaną uruchomione przy pomocy Dockera.

Docelowa architektura:

```text
Docker Compose

├── FastAPI
└── PostgreSQL
```

Uruchomienie całego projektu:

```bash
docker compose up
```

---

# Etap 15 — Frontend

Po ukończeniu głównej części backendu możliwe będzie stworzenie osobnego frontendu.

Planowany stack:

```text
React
TypeScript
```

Frontend klienta:

```text
wybór usługi
↓
wybór pracownika
↓
wybór dnia
↓
wybór godziny
↓
rezerwacja
```

Frontend administratora:

```text
dashboard
pracownicy
usługi
grafiki
rezerwacje
klienci
```

---

# Docelowa architektura

```text
React
   ↓
REST API
   ↓
FastAPI
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

---

# Aktualna struktura backendu

```text
app/
├── __init__.py
├── main.py
├── database.py
├── models/
│   ├── __init__.py
│   ├── service.py
│   ├── employee.py
│   └── appointment.py
├── routers/
│   ├── __init__.py
│   ├── services.py
│   ├── employees.py
│   └── appointments.py
└── schemas/
    ├── __init__.py
    ├── service.py
    ├── employee.py
    └── appointment.py

tests/
├── conftest.py
├── test_services.py
├── test_employees.py
└── test_appointments.py
```

- `app/main.py` — tworzy aplikację, tabele i dołącza routery.
- `app/database.py` — konfiguruje SQLite, silnik i sesje SQLAlchemy.
- `app/models/` — opisuje tabele SQLAlchemy.
- `app/schemas/` — waliduje requesty i formatuje odpowiedzi Pydantic.
- `app/routers/` — zawiera endpointy usług, pracowników i rezerwacji.
- `tests/` — używa osobnej, tymczasowej bazy SQLite.
- `salon.db` — lokalna baza deweloperska; plik jest ignorowany przez Git.

Wszystkie dane aplikacji są przechowywane w SQLite. `Base.metadata.create_all()` tymczasowo tworzy brakujące tabele przy starcie. W kolejnym etapie zastąpi go Alembic, a później SQLite zostanie zamienione na PostgreSQL.

Uruchomienie z katalogu projektu:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Testy:

```bash
python -m pytest -v
```

Dokumentacja API: `http://127.0.0.1:8000/docs`.

---

# Przykładowa struktura docelowa backendu

```text
app/
│
├── main.py
│
├── database.py
│
├── config.py
│
├── dependencies.py
│
├── models/
│   ├── user.py
│   ├── employee.py
│   ├── service.py
│   ├── appointment.py
│   └── schedule.py
│
├── schemas/
│   ├── user.py
│   ├── employee.py
│   ├── service.py
│   ├── appointment.py
│   └── schedule.py
│
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── employees.py
│   ├── services.py
│   ├── appointments.py
│   └── availability.py
│
├── services/
│   ├── booking_service.py
│   └── availability_service.py
│
└── tests/
```

Struktura projektu będzie rozwijana stopniowo wraz z nauką kolejnych elementów FastAPI.

---

# Status projektu

```text
[x] FastAPI setup
[x] Employees CRUD
[x] Services CRUD
[x] Appointments CRUD
[ ] PostgreSQL
[x] SQLAlchemy
[ ] Alembic
[ ] Employee ↔ Service
[ ] Employee schedules
[ ] Availability system
[ ] Booking validation
[ ] Time off / breaks
[ ] Users
[ ] JWT authentication
[ ] Roles and permissions
[x] Automated tests
[ ] Docker
[ ] React frontend
[ ] Deployment
```

---

# Główny cel projektu

Projekt ma być praktycznym sposobem nauki backend developmentu w Pythonie.

Najważniejszym celem nie jest jak najszybsze ukończenie aplikacji, ale zrozumienie:

- jak projektować REST API,
- jak działa FastAPI,
- jak projektować bazę danych,
- jak tworzyć relacje między tabelami,
- jak implementować logikę biznesową,
- jak zabezpieczać API,
- jak testować backend,
- jak tworzyć aplikację gotową do dalszego rozwoju.
