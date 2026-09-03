import { supabase } from './supabase';

type Row = Record<string, unknown>;
type ExportPayload = { format: string; version: number; tables: Record<string, Row[]> };

function requiredTables(payload: ExportPayload) {
  return ['weddings', 'entries', 'tasks', 'guest_tables', 'invitation_groups', 'guests'].every((name) => Array.isArray(payload.tables?.[name]));
}

function clean(row: Row, fields: string[]) {
  return Object.fromEntries(fields.filter((field) => row[field] !== undefined).map((field) => [field, row[field]]));
}

function asBoolean(value: unknown) { return value === true || value === 1; }
function idMap(rows: Row[] | null) { return new Map((rows ?? []).map((row) => [Number(row.legacy_id), String(row.id)])); }
function fail(error: { message: string } | null) { if (error) throw new Error(error.message); }

export async function importDesktopDatabase(file: File, weddingId: string, progress: (text: string) => void) {
  if (!supabase) throw new Error('A Supabase nincs beállítva.');
  const payload = JSON.parse(await file.text()) as ExportPayload;
  if (payload.format !== 'our-day-sqlite-export' || payload.version !== 1 || !requiredTables(payload)) throw new Error('Ez nem érvényes Our Day importfájl.');
  const tables = payload.tables;

  progress('Esküvői alapadatok…');
  const sourceWedding = tables.weddings[0];
  if (sourceWedding) {
    const { error } = await supabase.from('weddings').update(clean(sourceWedding, ['bride_name', 'groom_name', 'wedding_date', 'venue_name', 'venue_address', 'budget_amount', 'notes'])).eq('id', weddingId);
    fail(error);
  }

  progress('Asztalok és meghívási csoportok…');
  const cloudTables = tables.guest_tables.map((row) => ({ ...clean(row, ['name', 'capacity', 'notes', 'position_x', 'position_y', 'shape']), wedding_id: weddingId, legacy_id: row.id }));
  const tableResult = await supabase.from('guest_tables').upsert(cloudTables, { onConflict: 'wedding_id,legacy_id' }).select('id,legacy_id'); fail(tableResult.error);
  const tableIds = idMap(tableResult.data as Row[] | null);

  const cloudGroups = tables.invitation_groups.map((row) => ({ ...clean(row, ['name', 'group_type', 'contact_name', 'email', 'phone', 'invitation_sent_date', 'rsvp_due_date', 'notes']), wedding_id: weddingId, legacy_id: row.id }));
  const groupResult = await supabase.from('invitation_groups').upsert(cloudGroups, { onConflict: 'wedding_id,legacy_id' }).select('id,legacy_id'); fail(groupResult.error);
  const groupIds = idMap(groupResult.data as Row[] | null);

  progress('Étkezési preferenciák…');
  const cloudPreferences = (tables.guest_preferences ?? []).map((row) => ({ ...clean(row, ['category', 'name']), wedding_id: weddingId, legacy_id: row.id }));
  const preferenceResult = await supabase.from('guest_preferences').upsert(cloudPreferences, { onConflict: 'wedding_id,legacy_id' }).select('id,legacy_id'); fail(preferenceResult.error);
  const preferenceIds = idMap(preferenceResult.data as Row[] | null);

  progress(`Vendégek feltöltése (0/${tables.guests.length})…`);
  const guestFields = ['name', 'email', 'phone', 'guest_type', 'invitation_status', 'attendance_status', 'plus_one_name', 'dietary_notes', 'family_name', 'notes', 'response_date', 'seating_notes'];
  const cloudGuests = tables.guests.map((row) => ({ ...clean(row, guestFields), wedding_id: weddingId, legacy_id: row.id, table_id: row.table_id ? tableIds.get(Number(row.table_id)) ?? null : null, invitation_group_id: row.invitation_group_id ? groupIds.get(Number(row.invitation_group_id)) ?? null : null, has_plus_one: asBoolean(row.has_plus_one), attends_dinner: asBoolean(row.attends_dinner), is_contact_person: asBoolean(row.is_contact_person), accessibility_required: asBoolean(row.accessibility_required) }));
  const guestResult = await supabase.from('guests').upsert(cloudGuests, { onConflict: 'wedding_id,legacy_id' }).select('id,legacy_id'); fail(guestResult.error);
  const guestIds = idMap(guestResult.data as Row[] | null);

  progress('Családi és kapcsolattartói kapcsolatok…');
  for (const row of tables.guests) {
    if (!row.parent_guest_id) continue;
    const { error } = await supabase.from('guests').update({ parent_guest_id: guestIds.get(Number(row.parent_guest_id)) ?? null }).eq('id', guestIds.get(Number(row.id))!); fail(error);
  }
  for (const row of tables.invitation_groups) {
    if (!row.contact_guest_id) continue;
    const { error } = await supabase.from('invitation_groups').update({ contact_guest_id: guestIds.get(Number(row.contact_guest_id)) ?? null }).eq('id', groupIds.get(Number(row.id))!); fail(error);
  }

  progress('Feladatok és szolgáltatások…');
  const taskRows = tables.tasks.map((row) => ({ ...clean(row, ['title', 'description', 'due_date', 'priority', 'status']), wedding_id: weddingId, legacy_id: row.id }));
  const entryRows = tables.entries.map((row) => ({ ...clean(row, ['entry_type', 'title', 'description', 'contact_name', 'phone', 'email', 'deposit_amount', 'total_amount', 'status', 'deposit_due_date', 'deposit_paid_date', 'payment_due_date']), wedding_id: weddingId, legacy_id: row.id }));
  if (taskRows.length) { const { error } = await supabase.from('tasks').upsert(taskRows, { onConflict: 'wedding_id,legacy_id' }); fail(error); }
  if (entryRows.length) { const { error } = await supabase.from('entries').upsert(entryRows, { onConflict: 'wedding_id,legacy_id' }); fail(error); }

  progress('Preferencia- és ültetési kapcsolatok…');
  const preferenceLinks = (tables.guest_preference_rel ?? []).map((row) => ({ guest_id: guestIds.get(Number(row.guest_id)), preference_id: preferenceIds.get(Number(row.preference_id)) })).filter((row) => row.guest_id && row.preference_id);
  if (preferenceLinks.length) { const { error } = await supabase.from('guest_preference_rel').upsert(preferenceLinks, { onConflict: 'guest_id,preference_id', ignoreDuplicates: true }); fail(error); }
  const seatingLinks = (tables.guest_seating_preferences ?? []).map((row) => ({ guest_id: guestIds.get(Number(row.guest_id)), related_guest_id: guestIds.get(Number(row.related_guest_id)), relation_type: row.relation_type })).filter((row) => row.guest_id && row.related_guest_id);
  if (seatingLinks.length) { const { error } = await supabase.from('guest_seating_preferences').upsert(seatingLinks, { onConflict: 'guest_id,related_guest_id,relation_type', ignoreDuplicates: true }); fail(error); }

  return { guests: tables.guests.length, groups: tables.invitation_groups.length, tasks: tables.tasks.length, entries: tables.entries.length, tables: tables.guest_tables.length };
}
