create extension if not exists "pgcrypto";

create table public.weddings (
  id uuid primary key default gen_random_uuid(),
  bride_name text not null,
  groom_name text not null,
  wedding_date date,
  venue_name text,
  venue_address text,
  budget_amount numeric(12, 2) not null default 0,
  notes text,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.wedding_members (
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'editor' check (role in ('owner', 'editor', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (wedding_id, user_id)
);

create table public.guest_tables (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  name text not null,
  capacity integer not null default 8 check (capacity > 0),
  shape text not null default 'round',
  position_x numeric not null default 0,
  position_y numeric not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.guests (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  table_id uuid references public.guest_tables(id) on delete set null,
  name text not null,
  email text,
  phone text,
  guest_type text not null default 'Felnőtt',
  invitation_status text not null default 'Nincs elküldve',
  attendance_status text not null default 'Válaszra vár',
  attends_dinner boolean not null default true,
  dietary_notes text,
  seating_notes text,
  accessibility_required boolean not null default false,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  title text not null,
  description text,
  due_date date,
  priority text not null default 'Közepes',
  status text not null default 'Teendő',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.entries (
  id uuid primary key default gen_random_uuid(),
  wedding_id uuid not null references public.weddings(id) on delete cascade,
  entry_type text not null default 'Szolgáltatás',
  title text not null,
  description text,
  contact_name text,
  phone text,
  email text,
  deposit_amount numeric(12, 2) not null default 0,
  total_amount numeric(12, 2) not null default 0,
  status text not null default 'Ötlet',
  deposit_due_date date,
  deposit_paid_date date,
  payment_due_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index guests_wedding_id_idx on public.guests(wedding_id);
create index tasks_wedding_id_due_date_idx on public.tasks(wedding_id, due_date);
create index entries_wedding_id_idx on public.entries(wedding_id);
create index guest_tables_wedding_id_idx on public.guest_tables(wedding_id);

alter table public.weddings enable row level security;
alter table public.wedding_members enable row level security;
alter table public.guest_tables enable row level security;
alter table public.guests enable row level security;
alter table public.tasks enable row level security;
alter table public.entries enable row level security;

create or replace function public.is_wedding_member(target_wedding_id uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.wedding_members
    where wedding_id = target_wedding_id and user_id = auth.uid()
  );
$$;

create policy "members can view weddings" on public.weddings
  for select using (public.is_wedding_member(id) or created_by = auth.uid());
create policy "users can create weddings" on public.weddings
  for insert with check (created_by = auth.uid());
create policy "members can update weddings" on public.weddings
  for update using (public.is_wedding_member(id));

create policy "members can view memberships" on public.wedding_members
  for select using (public.is_wedding_member(wedding_id) or user_id = auth.uid());

create policy "members manage guest tables" on public.guest_tables
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));
create policy "members manage guests" on public.guests
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));
create policy "members manage tasks" on public.tasks
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));
create policy "members manage entries" on public.entries
  for all using (public.is_wedding_member(wedding_id)) with check (public.is_wedding_member(wedding_id));

create or replace function public.add_creator_as_owner()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.wedding_members (wedding_id, user_id, role)
  values (new.id, new.created_by, 'owner');
  return new;
end;
$$;

create trigger wedding_creator_membership
after insert on public.weddings
for each row execute function public.add_creator_as_owner();
