#!/usr/bin/env node
// Runs a SQL file (or inline SQL) against the linked Supabase project through the
// Management API — no psql, no DB password. Uses the Supabase CLI login token.
//
// Usage:
//   node scripts/run-sql.js supabase/migrations/20260904231500_beart_foundation.sql
//   node scripts/run-sql.js supabase/migrations/2026..._name.sql --record   # also mark as applied
//   node scripts/run-sql.js --sql "select count(*) from app_users"
//
// Token resolution order:
//   1. SUPABASE_ACCESS_TOKEN env var
//   2. ~/.supabase/access-token
//   3. macOS Keychain item "Supabase CLI" (what `supabase login` stores)

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_REF = 'gcbdraagnpdpihcucsqq';
const API = `https://api.supabase.com/v1/projects/${PROJECT_REF}/database/query`;

function getToken() {
  if (process.env.SUPABASE_ACCESS_TOKEN) return process.env.SUPABASE_ACCESS_TOKEN;
  const file = path.join(os.homedir(), '.supabase', 'access-token');
  if (fs.existsSync(file)) return fs.readFileSync(file, 'utf8').trim();
  try {
    return execSync('security find-generic-password -s "Supabase CLI" -w', { stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
  } catch {
    throw new Error('No Supabase token found. Run `supabase login` or set SUPABASE_ACCESS_TOKEN.');
  }
}

async function runQuery(token, query) {
  const res = await fetch(API, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function main() {
  const args = process.argv.slice(2);
  const record = args.includes('--record');
  const sqlIdx = args.indexOf('--sql');
  let sql, migrationName = null;

  if (sqlIdx !== -1) {
    sql = args[sqlIdx + 1];
  } else {
    const file = args.find(a => !a.startsWith('--'));
    if (!file) { console.error('Usage: run-sql.js <file.sql> [--record] | --sql "<query>"'); process.exit(1); }
    sql = fs.readFileSync(file, 'utf8');
    migrationName = path.basename(file, '.sql'); // e.g. 20260904231500_beart_foundation
  }

  const token = getToken();
  const result = await runQuery(token, sql);
  console.log(JSON.stringify(result, null, 2));

  if (record) {
    if (!migrationName) throw new Error('--record needs a migration file, not --sql');
    const m = migrationName.match(/^(\d{14})_(.+)$/);
    if (!m) throw new Error(`Migration file name must be <14-digit timestamp>_name.sql, got ${migrationName}`);
    await runQuery(token, `
      create schema if not exists supabase_migrations;
      create table if not exists supabase_migrations.schema_migrations
        (version text primary key, statements text[], name text);
      insert into supabase_migrations.schema_migrations (version, name)
        values ('${m[1]}', '${m[2].replace(/'/g, "''")}') on conflict do nothing;
    `);
    console.log(`Recorded migration ${m[1]} (${m[2]}) in supabase_migrations.schema_migrations`);
  }
}

main().catch(err => { console.error(err.message); process.exit(1); });
