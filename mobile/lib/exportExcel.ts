import ExcelJS from 'exceljs';
import { supabase } from '@/lib/supabase';

type Preference = { id: string; category: string; name: string };
type Link = { guest_id: string; preference_id: string };

export async function exportWeddingToExcel(weddingId: string, weddingLabel: string) {
  const [guestResult, groupResult, tableResult, preferenceResult, linkResult] = await Promise.all([
    supabase!.from('guests').select('id,name,email,phone,guest_type,invitation_status,attendance_status,attends_dinner,dietary_notes,notes,invitation_group_id,table_id').eq('wedding_id', weddingId).order('name'),
    supabase!.from('invitation_groups').select('id,name,group_type,contact_name,email,phone,rsvp_due_date,notes').eq('wedding_id', weddingId).order('name'),
    supabase!.from('guest_tables').select('id,name,capacity').eq('wedding_id', weddingId).order('name'),
    supabase!.from('guest_preferences').select('id,category,name').eq('wedding_id', weddingId).order('category').order('name'),
    supabase!.from('guest_preference_rel').select('guest_id,preference_id'),
  ]);
  const error = guestResult.error ?? groupResult.error ?? tableResult.error ?? preferenceResult.error ?? linkResult.error;
  if (error) throw error;

  const guests = guestResult.data ?? []; const groups = groupResult.data ?? []; const tables = tableResult.data ?? [];
  const preferences = (preferenceResult.data ?? []) as Preference[]; const links = (linkResult.data ?? []) as Link[];
  const groupNames = new Map(groups.map((item) => [item.id, item.name]));
  const tableNames = new Map(tables.map((item) => [item.id, item.name]));
  const preferenceById = new Map(preferences.map((item) => [item.id, item]));
  const preferenceIdsByGuest = new Map<string, string[]>();
  for (const link of links) (preferenceIdsByGuest.get(link.guest_id) ?? (preferenceIdsByGuest.set(link.guest_id, []), preferenceIdsByGuest.get(link.guest_id)!)).push(link.preference_id);
  const labelsFor = (guestId: string, predicate?: (item: Preference) => boolean) => (preferenceIdsByGuest.get(guestId) ?? []).map((id) => preferenceById.get(id)).filter((item): item is Preference => Boolean(item) && (!predicate || predicate(item))).map((item) => item.name).join(', ');

  const workbook = new ExcelJS.Workbook(); workbook.creator = 'Our Day Mobil'; workbook.created = new Date();
  addSummarySheet(workbook, weddingLabel, guests, groups.length, preferenceIdsByGuest);
  const guestSheet = workbook.addWorksheet('Vendégek', { views: [{ state: 'frozen', ySplit: 1 }] });
  guestSheet.columns = [
    ['Meghívási csoport', 24], ['Név', 25], ['Felnőtt / gyermek', 18], ['Meghívás állapota', 20], ['RSVP', 18], ['Vacsora', 12], ['Asztal', 18], ['Telefon', 20], ['E-mail', 28], ['Ételérzékenység / allergia', 34], ['Különleges igények', 34], ['Étrendi megjegyzés', 32], ['Megjegyzés', 32],
  ].map(([header, width]) => ({ header: String(header), key: String(header), width: Number(width) }));
  const specialCategory = (item: Preference) => item.category.toLocaleLowerCase('hu').includes('különleges');
  guests.forEach((guest) => guestSheet.addRow({
    'Meghívási csoport': groupNames.get(guest.invitation_group_id ?? '') ?? 'Csoport nélkül', Név: guest.name, 'Felnőtt / gyermek': guest.guest_type, 'Meghívás állapota': guest.invitation_status, RSVP: guest.attendance_status, Vacsora: guest.attends_dinner ? 'Igen' : 'Nem', Asztal: tableNames.get(guest.table_id ?? '') ?? '', Telefon: guest.phone ?? '', 'E-mail': guest.email ?? '', 'Ételérzékenység / allergia': labelsFor(guest.id, (item) => !specialCategory(item)), 'Különleges igények': labelsFor(guest.id, specialCategory), 'Étrendi megjegyzés': guest.dietary_notes ?? '', Megjegyzés: guest.notes ?? '',
  }));
  styleSheet(guestSheet);

  const groupSheet = workbook.addWorksheet('Csoportok', { views: [{ state: 'frozen', ySplit: 1 }] });
  groupSheet.columns = [['Csoport', 25], ['Típus', 18], ['Kapcsolattartó', 25], ['Telefon', 20], ['E-mail', 28], ['RSVP-határidő', 18], ['Vendégek', 12], ['Megjegyzés', 35]].map(([header, width]) => ({ header: String(header), key: String(header), width: Number(width) }));
  groups.forEach((group) => groupSheet.addRow({ Csoport: group.name, Típus: group.group_type ?? '', Kapcsolattartó: group.contact_name ?? '', Telefon: group.phone ?? '', 'E-mail': group.email ?? '', 'RSVP-határidő': group.rsvp_due_date ?? '', Vendégek: guests.filter((guest) => guest.invitation_group_id === group.id).length, Megjegyzés: group.notes ?? '' })); styleSheet(groupSheet);

  const prefSheet = workbook.addWorksheet('Igények összesítése', { views: [{ state: 'frozen', ySplit: 1 }] });
  prefSheet.columns = [['Kategória', 22], ['Megnevezés', 28], ['Érintett vendégek', 20], ['Vendégek', 55]].map(([header, width]) => ({ header: String(header), key: String(header), width: Number(width) }));
  preferences.forEach((preference) => { const people = links.filter((link) => link.preference_id === preference.id).map((link) => guests.find((guest) => guest.id === link.guest_id)?.name).filter(Boolean); prefSheet.addRow({ Kategória: preference.category, Megnevezés: preference.name, 'Érintett vendégek': people.length, Vendégek: people.join(', ') }); }); styleSheet(prefSheet);

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
  anchor.href = url; anchor.download = `our-day-${slug(weddingLabel)}-${new Date().toISOString().slice(0, 10)}.xlsx`; anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  return guests.length;
}

function addSummarySheet(
  workbook: ExcelJS.Workbook,
  weddingLabel: string,
  guests: Array<{ id: string; guest_type: string; attendance_status: string; attends_dinner: boolean; table_id: string | null }>,
  groupCount: number,
  preferenceIdsByGuest: Map<string, string[]>,
) {
  const sheet = workbook.addWorksheet('Összesítő', { views: [{ state: 'frozen', ySplit: 3 }] });
  sheet.columns = [{ width: 24 }, { width: 18 }, { width: 4 }, { width: 24 }, { width: 18 }];
  sheet.mergeCells('A1:E1'); sheet.getCell('A1').value = 'Our Day – vendégösszesítő';
  sheet.mergeCells('A2:E2'); sheet.getCell('A2').value = weddingLabel.replaceAll('-', ' ');
  sheet.getRow(1).height = 34; sheet.getRow(2).height = 24;
  sheet.getCell('A1').font = { bold: true, size: 22, color: { argb: 'FFFFFFFF' } };
  sheet.getCell('A2').font = { italic: true, size: 12, color: { argb: 'FFF1EAF8' } };
  for (const cell of ['A1', 'A2']) { sheet.getCell(cell).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF6B4EA0' } }; sheet.getCell(cell).alignment = { vertical: 'middle', horizontal: 'left' }; }

  const total = guests.length;
  const metrics: Array<[string, number]> = [
    ['Összes vendég', total],
    ['Felnőtt', guests.filter((guest) => guest.guest_type === 'Felnőtt').length],
    ['Gyermek', guests.filter((guest) => guest.guest_type === 'Gyermek').length],
    ['Részt vesz', guests.filter((guest) => guest.attendance_status === 'Részt vesz').length],
    ['Válaszra vár', guests.filter((guest) => guest.attendance_status === 'Válaszra vár').length],
    ['Nem vesz részt', guests.filter((guest) => guest.attendance_status === 'Nem vesz részt').length],
    ['Vacsorán részt vesz', guests.filter((guest) => guest.attends_dinner).length],
    ['Speciális igénnyel', guests.filter((guest) => (preferenceIdsByGuest.get(guest.id)?.length ?? 0) > 0).length],
    ['Asztalhoz rendelve', guests.filter((guest) => Boolean(guest.table_id)).length],
    ['Meghívási csoportok', groupCount],
  ];
  metrics.forEach(([label, value], index) => {
    const row = 4 + Math.floor(index / 2) * 3; const column = index % 2 === 0 ? 1 : 4;
    const labelCell = sheet.getCell(row, column); const valueCell = sheet.getCell(row + 1, column);
    sheet.mergeCells(row, column, row, column + 1); sheet.mergeCells(row + 1, column, row + 1, column + 1);
    labelCell.value = label; valueCell.value = value;
    labelCell.font = { bold: true, size: 11, color: { argb: 'FF6B4EA0' } }; valueCell.font = { bold: true, size: 22, color: { argb: 'FF2E2530' } };
    labelCell.fill = valueCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF4EEF8' } };
    labelCell.alignment = valueCell.alignment = { vertical: 'middle', horizontal: 'center' };
    labelCell.border = { top: { style: 'thin', color: { argb: 'FFE1D7E8' } }, left: { style: 'thin', color: { argb: 'FFE1D7E8' } }, right: { style: 'thin', color: { argb: 'FFE1D7E8' } } };
    valueCell.border = { bottom: { style: 'thin', color: { argb: 'FFE1D7E8' } }, left: { style: 'thin', color: { argb: 'FFE1D7E8' } }, right: { style: 'thin', color: { argb: 'FFE1D7E8' } } };
    sheet.getRow(row).height = 24; sheet.getRow(row + 1).height = 34;
  });

  const responseRate = total ? Math.round((guests.filter((guest) => guest.attendance_status !== 'Válaszra vár').length / total) * 100) : 0;
  sheet.mergeCells('A20:E20'); sheet.getCell('A20').value = `RSVP válaszadási arány: ${responseRate}%`;
  sheet.getCell('A20').font = { bold: true, size: 13, color: { argb: 'FFFFFFFF' } }; sheet.getCell('A20').fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF6B4EA0' } }; sheet.getCell('A20').alignment = { horizontal: 'center', vertical: 'middle' }; sheet.getRow(20).height = 30;
  sheet.mergeCells('A22:E22'); sheet.getCell('A22').value = `Exportálva: ${new Intl.DateTimeFormat('hu-HU', { dateStyle: 'long' }).format(new Date())}`; sheet.getCell('A22').font = { size: 10, color: { argb: 'FF766B74' } }; sheet.getCell('A22').alignment = { horizontal: 'right' };
}

function styleSheet(sheet: ExcelJS.Worksheet) {
  const header = sheet.getRow(1); header.height = 28; header.font = { bold: true, color: { argb: 'FFFFFFFF' } }; header.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF6B4EA0' } }; header.alignment = { vertical: 'middle' };
  sheet.autoFilter = { from: { row: 1, column: 1 }, to: { row: Math.max(1, sheet.rowCount), column: sheet.columnCount } };
  sheet.eachRow((row, index) => { if (index > 1) { row.alignment = { vertical: 'top', wrapText: true }; if (index % 2 === 1) row.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF7F3F8' } }; } });
}

function slug(value: string) { return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'eskuvo'; }
