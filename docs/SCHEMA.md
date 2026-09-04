# Database Schema Reference — BeArt&Music

Supabase project: `beartdata` (`gcbdraagnpdpihcucsqq`, eu-west-1).

This project uses its **own, minimal schema**, not the alpacapps template one.
Source of truth: `supabase/migrations/20260904231500_beart_foundation.sql`.
The template's 68 migrations are kept for reference only in
`supabase/migrations-template-archive/` and must never be pushed.

School data (students, lessons, schedule, payments) lives in **ActiveNow**
(https://app.activenow.io). Supabase only holds accounts, permissions, config and a
light contact table. Add domain tables here only when a feature actually needs them.

## Tables

```
people                   - Light contact list (students, parents, teachers, leads)
                           (name, first_name, last_name, email [unique], phone,
                            type [student/parent/teacher/staff/lead/contact],
                            activenow_id, notes, is_archived)
                           RLS: staff read, admin write

app_users                - One row per signed-in account; drives roles in shared/auth.js
                           (auth_user_id [FK→auth.users], email [unique],
                            role [oracle/admin/staff/resident/associate/demo/public/prospect],
                            display_name, first_name, last_name, phone, phone2, whatsapp,
                            avatar_url, bio, gender, pronouns, birthday, instagram, links [jsonb],
                            nationality, location_base, privacy_settings [jsonb], slug,
                            person_id [FK→people], is_current_resident, invited_by,
                            last_sign_in_at)
                           RLS: own row + staff see all; users may edit own row but a trigger
                           blocks changing own role; insert only from a pending invitation
                           Role mapping for the school: admin/oracle = owner,
                           staff = teachers & office. Other roles unused for now.

user_invitations         - Invite-only sign-up (email, role, invited_by,
                            status [pending/accepted/expired/revoked], expires_at)
                           RLS: invitee reads/accepts own; admin manages all

permissions              - Permission keys (key [PK], label, description, category, sort_order)
role_permissions         - Defaults per role (role, permission_key)
user_permission_overrides- Per-user grant/revoke (app_user_id, permission_key, granted)
                           shared/admin-shell.js auto-inserts missing tab keys on load

property_config          - Singleton (id=1) JSONB: property name, domain, emails, timezone,
                           features flags. Public read, admin write. shared/config-loader.js
brand_config             - Singleton (id=1) JSONB: brand names, colors. Public read,
                           admin write. shared/brand-config.js
```

## Functions

```
get_effective_permissions(p_app_user_id uuid) → setof text
    role defaults ∪ granted overrides − revoked overrides. Used by shared/auth.js.
current_app_role() → text        role of the calling user (security definer, for RLS)
is_admin() / is_staff() → bool   helpers used in every RLS policy
set_updated_at()                 trigger: bumps updated_at on people, app_users
protect_app_user_role()          trigger: non-admins cannot change role
```

## First login

`user_invitations` is seeded with `bart.kondrat@gmail.com` as `admin`. Signing in with
that Google account creates the admin `app_users` row automatically. To add a teacher:

```sql
insert into user_invitations (email, role) values ('teacher@example.com', 'staff');
```

## Running SQL

Use the Supabase Management API (CLI token), never psql:

```bash
curl -s -X POST "https://api.supabase.com/v1/projects/gcbdraagnpdpihcucsqq/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"select 1"}'
```

## Template pages that still expect template tables

`directory/`, `residents/`, `associates/`, `spaces/admin/*` query tables that do not
exist here (`assignments`, `vehicles`, `time_entries`, `media`, …). They load but their
data panels fail. Either build BeArt-specific replacements or remove those pages.
