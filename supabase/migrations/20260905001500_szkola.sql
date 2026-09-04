-- Mokotown Music Academy — school operations (section /szkola/)
-- ActiveNow stays the system of record for students, schedule and payments.
-- These tables cover what ActiveNow does not: lead pipeline, teacher settlement
-- by lesson count, cancellation/make-up log, school calendar.

-- ---------------------------------------------------------------------------
-- teachers — no intranet login; managed by the directors
-- ---------------------------------------------------------------------------
create table public.teachers (
  id             uuid primary key default gen_random_uuid(),
  name           text not null,
  email          text,
  phone          text,
  instruments    text[] not null default '{}',
  rate_30        numeric(8,2) not null default 0,   -- PLN per 30-min lesson
  rate_45        numeric(8,2) not null default 0,
  rate_60        numeric(8,2) not null default 0,
  contract_type  text not null default 'umowa_zlecenie'
                 check (contract_type in ('umowa_zlecenie','umowa_o_dzielo','b2b','inna')),
  is_active      boolean not null default true,
  notes          text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create trigger teachers_updated_at before update on public.teachers
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- teacher_settlements — one row per teacher per month; rates are snapshotted
-- ---------------------------------------------------------------------------
create table public.teacher_settlements (
  id          uuid primary key default gen_random_uuid(),
  teacher_id  uuid not null references public.teachers(id) on delete cascade,
  period      text not null check (period ~ '^\d{4}-\d{2}$'),   -- 'YYYY-MM'
  lessons_30  integer not null default 0 check (lessons_30 >= 0),
  lessons_45  integer not null default 0 check (lessons_45 >= 0),
  lessons_60  integer not null default 0 check (lessons_60 >= 0),
  rate_30     numeric(8,2) not null default 0,
  rate_45     numeric(8,2) not null default 0,
  rate_60     numeric(8,2) not null default 0,
  total       numeric(10,2) generated always as
              (lessons_30 * rate_30 + lessons_45 * rate_45 + lessons_60 * rate_60) stored,
  status      text not null default 'do_wyplaty' check (status in ('do_wyplaty','wyplacone')),
  paid_at     date,
  notes       text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (teacher_id, period)
);
create trigger teacher_settlements_updated_at before update on public.teacher_settlements
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- leads — enquiries before they become ActiveNow students
-- ---------------------------------------------------------------------------
create table public.leads (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  phone           text,
  email           text,
  instrument      text,
  student_age     integer,
  source          text not null default 'inne'
                  check (source in ('formularz','quiz','telefon','polecenie','social','inne')),
  status          text not null default 'nowy'
                  check (status in ('nowy','kontakt','lekcja_probna','zapisany','rezygnacja')),
  preferred_days  text,
  next_action_at  date,
  notes           text,
  converted_at    timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index leads_status_idx on public.leads (status, next_action_at);
create trigger leads_updated_at before update on public.leads
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- lesson_cancellations — cancellation and make-up log
-- ---------------------------------------------------------------------------
create table public.lesson_cancellations (
  id            uuid primary key default gen_random_uuid(),
  lesson_date   date not null,
  lesson_time   time,
  student_name  text not null,
  teacher_id    uuid references public.teachers(id) on delete set null,
  duration_min  integer not null default 45 check (duration_min in (30,45,60)),
  cancelled_by  text not null default 'uczen' check (cancelled_by in ('uczen','nauczyciel','szkola')),
  reason        text,
  status        text not null default 'do_odrobienia'
                check (status in ('do_odrobienia','odrobiona','zwrot','przepada')),
  makeup_date   date,
  notes         text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index lesson_cancellations_status_idx on public.lesson_cancellations (status, lesson_date desc);
create trigger lesson_cancellations_updated_at before update on public.lesson_cancellations
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- calendar_events — holidays, breaks, concerts, open days
-- ---------------------------------------------------------------------------
create table public.calendar_events (
  id                uuid primary key default gen_random_uuid(),
  title             text not null,
  type              text not null default 'inne'
                    check (type in ('wolne','ferie','koncert','przesluchanie','dzien_otwarty','inne')),
  start_date        date not null,
  end_date          date not null,
  description       text,
  affects_schedule  boolean not null default true,   -- no lessons on these days
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  check (end_date >= start_date)
);
create index calendar_events_dates_idx on public.calendar_events (start_date, end_date);
create trigger calendar_events_updated_at before update on public.calendar_events
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- RLS — the directors (admin) and office (staff) manage everything
-- ---------------------------------------------------------------------------
alter table public.teachers             enable row level security;
alter table public.teacher_settlements  enable row level security;
alter table public.leads                enable row level security;
alter table public.lesson_cancellations enable row level security;
alter table public.calendar_events      enable row level security;

create policy teachers_staff on public.teachers for all to authenticated
  using (public.is_staff()) with check (public.is_staff());
create policy settlements_staff on public.teacher_settlements for all to authenticated
  using (public.is_staff()) with check (public.is_staff());
create policy leads_staff on public.leads for all to authenticated
  using (public.is_staff()) with check (public.is_staff());
create policy cancellations_staff on public.lesson_cancellations for all to authenticated
  using (public.is_staff()) with check (public.is_staff());
create policy calendar_staff on public.calendar_events for all to authenticated
  using (public.is_staff()) with check (public.is_staff());

-- Public site may read the calendar (holidays shown on the website later)
create policy calendar_public_read on public.calendar_events for select to anon using (true);

-- ---------------------------------------------------------------------------
-- Housekeeping: the second owner invitation was inserted twice and never
-- marked accepted (the account exists in app_users already).
-- ---------------------------------------------------------------------------
delete from public.user_invitations
where id in (
  select id from (
    select id, row_number() over (partition by lower(email) order by created_at) as rn
    from public.user_invitations where lower(email) = 'bartkondrat.ai@gmail.com'
  ) t where rn > 1
);
update public.user_invitations set status = 'accepted'
where lower(email) = 'bartkondrat.ai@gmail.com' and status = 'pending';
