-- Columns the template front-end (shared/auth.js, spaces/admin user management)
-- expects on user_invitations and app_users but the foundation migration lacked.
-- Without invited_at the invitation lookup fails and every login ends as "unauthorized".

alter table public.user_invitations
  add column if not exists invited_at        timestamptz not null default now(),
  add column if not exists email_sent_at     timestamptz,
  add column if not exists email_send_count  integer not null default 0,
  add column if not exists subject           text,
  add column if not exists message           text,
  add column if not exists message_text      text;

update public.user_invitations set invited_at = created_at where invited_at is distinct from created_at;

alter table public.app_users
  add column if not exists last_login_at                 timestamptz,
  add column if not exists is_current_resident_override  boolean;
