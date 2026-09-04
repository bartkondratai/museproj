-- BeArt&Music — foundation schema
-- Own, minimal schema replacing the alpacapps template one. Covers exactly what
-- shared/auth.js, login/, shared/admin-shell.js, shared/config-loader.js and
-- shared/brand-config.js need to work. Domain data (students, lessons, schedule)
-- lives in ActiveNow; `people` is only a light contact table.
--
-- Roles are kept as the template names because shared/auth.js hard-codes them:
--   oracle/admin = owner, staff = teachers & office, resident/associate = unused for now,
--   demo/public/prospect = no intranet access.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- ---------------------------------------------------------------------------
-- people — contacts (students, parents, teachers, leads). System of record for
-- school data is ActiveNow; activenow_id links a row to it when synced.
-- ---------------------------------------------------------------------------
create table public.people (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  first_name    text,
  last_name     text,
  email         text unique,
  phone         text,
  type          text not null default 'contact'
                check (type in ('student','parent','teacher','staff','lead','contact')),
  activenow_id  text,
  notes         text,
  is_archived   boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index people_email_idx on public.people (lower(email));
create trigger people_updated_at before update on public.people
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- app_users — one row per signed-in account (shared/auth.js, directory/)
-- ---------------------------------------------------------------------------
create table public.app_users (
  id                  uuid primary key default gen_random_uuid(),
  auth_user_id        uuid unique references auth.users(id) on delete cascade,
  email               text not null unique,
  role                text not null default 'public'
                      check (role in ('oracle','admin','staff','resident','associate','demo','public','prospect')),
  display_name        text,
  first_name          text,
  last_name           text,
  phone               text,
  phone2              text,
  whatsapp            text,
  avatar_url          text,
  bio                 text,
  gender              text,
  pronouns            text,
  birthday            date,
  instagram           text,
  links               jsonb not null default '[]'::jsonb,
  nationality         text,
  location_base       text,
  privacy_settings    jsonb not null default '{}'::jsonb,
  slug                text unique,
  person_id           uuid references public.people(id) on delete set null,
  is_current_resident boolean not null default false,
  invited_by          uuid references public.app_users(id) on delete set null,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  last_sign_in_at     timestamptz
);
create index app_users_role_idx on public.app_users (role);
create trigger app_users_updated_at before update on public.app_users
  for each row execute function public.set_updated_at();

-- Role of the calling user (security definer so RLS policies can use it
-- without recursing into app_users policies).
create or replace function public.current_app_role()
returns text language sql stable security definer set search_path = public as $$
  select role from public.app_users where auth_user_id = auth.uid();
$$;

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce(public.current_app_role() in ('admin','oracle'), false);
$$;

create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce(public.current_app_role() in ('admin','oracle','staff'), false);
$$;

-- Non-admins may edit their own profile but never their own role.
create or replace function public.protect_app_user_role()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.role is distinct from old.role and not public.is_admin() then
    raise exception 'Only admins can change roles';
  end if;
  return new;
end $$;
create trigger app_users_protect_role before update on public.app_users
  for each row execute function public.protect_app_user_role();

-- ---------------------------------------------------------------------------
-- user_invitations — sign-in is invite-only (shared/auth.js creates the
-- app_users row from a pending invitation on first login)
-- ---------------------------------------------------------------------------
create table public.user_invitations (
  id          uuid primary key default gen_random_uuid(),
  email       text not null,
  role        text not null
              check (role in ('oracle','admin','staff','resident','associate','demo','public','prospect')),
  invited_by  uuid references public.app_users(id) on delete set null,
  status      text not null default 'pending'
              check (status in ('pending','accepted','expired','revoked')),
  expires_at  timestamptz not null default now() + interval '30 days',
  created_at  timestamptz not null default now()
);
create index user_invitations_email_idx on public.user_invitations (lower(email), status);

-- ---------------------------------------------------------------------------
-- Permissions — role defaults ± per-user overrides (shared/admin-shell.js)
-- ---------------------------------------------------------------------------
create table public.permissions (
  key         text primary key,
  label       text not null,
  description text,
  category    text not null default 'staff',
  sort_order  integer not null default 100
);

create table public.role_permissions (
  role            text not null,
  permission_key  text not null references public.permissions(key) on delete cascade,
  primary key (role, permission_key)
);

create table public.user_permission_overrides (
  app_user_id     uuid not null references public.app_users(id) on delete cascade,
  permission_key  text not null references public.permissions(key) on delete cascade,
  granted         boolean not null,
  primary key (app_user_id, permission_key)
);

create or replace function public.get_effective_permissions(p_app_user_id uuid)
returns setof text language sql stable security definer set search_path = public as $$
  (
    select rp.permission_key
    from public.role_permissions rp
    join public.app_users u on u.id = p_app_user_id and u.role = rp.role
    union
    select o.permission_key
    from public.user_permission_overrides o
    where o.app_user_id = p_app_user_id and o.granted
  )
  except
  select o.permission_key
  from public.user_permission_overrides o
  where o.app_user_id = p_app_user_id and not o.granted;
$$;

-- ---------------------------------------------------------------------------
-- Config singletons (shared/config-loader.js, shared/brand-config.js)
-- ---------------------------------------------------------------------------
create table public.property_config (
  id          integer primary key check (id = 1),
  config      jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now(),
  updated_by  uuid references public.app_users(id) on delete set null
);

create table public.brand_config (
  id          integer primary key check (id = 1),
  config      jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now(),
  updated_by  uuid references public.app_users(id) on delete set null
);

insert into public.property_config (id, config) values (1, '{
  "property": {
    "name": "BeArt&Music",
    "short_name": "BeArt&Music",
    "tagline": "Fundacja BeArt & Music — Mokotown Music Academy",
    "city": "Warszawa",
    "country": "PL",
    "timezone": "Europe/Warsaw"
  },
  "domain": { "primary": "beartandmusic.pl" },
  "email": {
    "team": "kontakt@beartandmusic.pl",
    "notifications_from": "notifications@beartandmusic.pl",
    "noreply_from": "noreply@beartandmusic.pl"
  },
  "features": {}
}'::jsonb);

insert into public.brand_config (id, config) values (1, '{
  "brand": {
    "primary_name": "BeArt&Music",
    "full_name": "Fundacja BeArt & Music",
    "platform_name": "BeArt&Music Intranet",
    "website": "https://beartandmusic.pl"
  }
}'::jsonb);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.people                   enable row level security;
alter table public.app_users                enable row level security;
alter table public.user_invitations         enable row level security;
alter table public.permissions              enable row level security;
alter table public.role_permissions         enable row level security;
alter table public.user_permission_overrides enable row level security;
alter table public.property_config          enable row level security;
alter table public.brand_config             enable row level security;

-- people: staff read, admin write
create policy people_select on public.people for select to authenticated using (public.is_staff());
create policy people_write  on public.people for all    to authenticated using (public.is_admin()) with check (public.is_admin());

-- app_users: own row always; staff see everyone (directory); admin writes all;
-- a user may create their own row only from a pending invitation with that role
create policy app_users_select on public.app_users for select to authenticated
  using (auth_user_id = auth.uid() or public.is_staff());
create policy app_users_update_self on public.app_users for update to authenticated
  using (auth_user_id = auth.uid()) with check (auth_user_id = auth.uid());
create policy app_users_admin_write on public.app_users for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy app_users_insert_from_invite on public.app_users for insert to authenticated
  with check (
    auth_user_id = auth.uid()
    and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
    and exists (
      select 1 from public.user_invitations i
      where lower(i.email) = lower(app_users.email)
        and i.status = 'pending'
        and i.expires_at > now()
        and i.role = app_users.role
    )
  );

-- user_invitations: invitee sees & accepts their own; admin manages all
create policy invitations_select on public.user_invitations for select to authenticated
  using (public.is_admin() or lower(email) = lower(coalesce(auth.jwt() ->> 'email', '')));
create policy invitations_accept on public.user_invitations for update to authenticated
  using (lower(email) = lower(coalesce(auth.jwt() ->> 'email', '')))
  with check (status = 'accepted');
create policy invitations_admin on public.user_invitations for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- permissions tables: everyone signed in can read; admin writes
create policy permissions_select on public.permissions for select to authenticated using (true);
create policy permissions_admin  on public.permissions for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy role_permissions_select on public.role_permissions for select to authenticated using (true);
create policy role_permissions_admin  on public.role_permissions for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy overrides_select on public.user_permission_overrides for select to authenticated
  using (public.is_admin() or app_user_id in (select id from public.app_users where auth_user_id = auth.uid()));
create policy overrides_admin on public.user_permission_overrides for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- config: public read (the public site reads brand/property config), admin write
create policy property_config_select on public.property_config for select to anon, authenticated using (true);
create policy property_config_admin  on public.property_config for all to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy brand_config_select on public.brand_config for select to anon, authenticated using (true);
create policy brand_config_admin  on public.brand_config for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------------------
-- Bootstrap: first admin. Signing in with this Google account creates the
-- admin app_users row automatically (shared/auth.js invitation flow).
-- ---------------------------------------------------------------------------
insert into public.user_invitations (email, role, expires_at)
values ('bart.kondrat@gmail.com', 'admin', now() + interval '1 year');

-- Base permission that every staff/admin gets; admin-shell.js adds the rest on first load.
insert into public.permissions (key, label, description, category, sort_order)
values ('manage_permissions', 'Manage Permissions', 'Edit roles and permission overrides', 'admin', 1);
insert into public.role_permissions (role, permission_key)
values ('admin', 'manage_permissions'), ('oracle', 'manage_permissions');
