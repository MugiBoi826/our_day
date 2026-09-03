alter table public.guest_tables add column if not exists legacy_id bigint;
alter table public.guest_tables add column if not exists notes text;
create unique index if not exists guest_tables_legacy_idx on public.guest_tables(wedding_id, legacy_id);

alter table public.guests add column if not exists legacy_id bigint;
alter table public.guests add column if not exists has_plus_one boolean not null default false;
alter table public.guests add column if not exists plus_one_name text;
alter table public.guests add column if not exists parent_guest_id uuid references public.guests(id) on delete set null;
alter table public.guests add column if not exists family_name text;
alter table public.guests add column if not exists response_date date;
alter table public.guests add column if not exists is_contact_person boolean not null default false;
create unique index if not exists guests_legacy_idx on public.guests(wedding_id, legacy_id);

alter table public.tasks add column if not exists legacy_id bigint;
alter table public.entries add column if not exists legacy_id bigint;
create unique index if not exists tasks_legacy_idx on public.tasks(wedding_id, legacy_id);
create unique index if not exists entries_legacy_idx on public.entries(wedding_id, legacy_id);

create table if not exists public.invitation_groups (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  legacy_id bigint,
  name text not null,
  group_type text,
  contact_name text,
  email text,
  phone text,
  invitation_sent_date date,
  rsvp_due_date date,
  notes text,
  contact_guest_id uuid references public.guests(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(wedding_id, legacy_id)
);

alter table public.guests add column if not exists invitation_group_id uuid references public.invitation_groups(id) on delete set null;

create table if not exists public.guest_preferences (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  legacy_id bigint,
  category text not null,
  name text not null,
  unique(wedding_id, legacy_id)
);

create table if not exists public.guest_preference_rel (
  guest_id uuid not null references public.guests(id) on delete cascade,
  preference_id uuid not null references public.guest_preferences(id) on delete cascade,
  primary key(guest_id, preference_id)
);

create table if not exists public.guest_seating_preferences (
  guest_id uuid not null references public.guests(id) on delete cascade,
  related_guest_id uuid not null references public.guests(id) on delete cascade,
  relation_type text not null,
  primary key(guest_id, related_guest_id, relation_type)
);

alter table public.invitation_groups enable row level security;
alter table public.guest_preferences enable row level security;
alter table public.guest_preference_rel enable row level security;
alter table public.guest_seating_preferences enable row level security;

create policy "members manage invitation groups" on public.invitation_groups
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));
create policy "members manage guest preferences" on public.guest_preferences
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));
create policy "members manage guest preference links" on public.guest_preference_rel
  for all using (exists(select 1 from public.guests g where g.id = guest_id and public.is_wedding_member(g.wedding_id)))
  with check (exists(select 1 from public.guests g where g.id = guest_id and public.is_wedding_member(g.wedding_id)));
create policy "members manage seating preferences" on public.guest_seating_preferences
  for all using (exists(select 1 from public.guests g where g.id = guest_id and public.is_wedding_member(g.wedding_id)))
  with check (exists(select 1 from public.guests g where g.id = guest_id and public.is_wedding_member(g.wedding_id)));

grant select, insert, update, delete on public.invitation_groups to authenticated;
grant select, insert, update, delete on public.guest_preferences to authenticated;
grant select, insert, update, delete on public.guest_preference_rel to authenticated;
grant select, insert, update, delete on public.guest_seating_preferences to authenticated;

notify pgrst, 'reload schema';
