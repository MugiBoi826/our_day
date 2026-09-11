'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { supabase } from '@/lib/supabase';

export type InvitationGroup = {
  id: string;
  name: string;
  group_type: string | null;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  rsvp_due_date: string | null;
  notes: string | null;
};

export function GroupsPanel({ weddingId, onBack }: { weddingId: string; onBack?: () => void }) {
  const [groups, setGroups] = useState<InvitationGroup[]>([]);
  const [guestCounts, setGuestCounts] = useState<Record<string, number>>({});
  const [editing, setEditing] = useState<InvitationGroup | 'new' | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const [groupsResult, guestsResult] = await Promise.all([
      supabase!.from('invitation_groups').select('id,name,group_type,contact_name,email,phone,rsvp_due_date,notes').eq('wedding_id', weddingId).order('name'),
      supabase!.from('guests').select('invitation_group_id').eq('wedding_id', weddingId).not('invitation_group_id', 'is', null),
    ]);
    setGroups((groupsResult.data ?? []) as InvitationGroup[]);
    const counts: Record<string, number> = {};
    for (const guest of guestsResult.data ?? []) {
      if (guest.invitation_group_id) counts[guest.invitation_group_id] = (counts[guest.invitation_group_id] ?? 0) + 1;
    }
    setGuestCounts(counts);
    setLoading(false);
  }

  useEffect(() => { load(); const timer = window.setInterval(load, 30_000); return () => window.clearInterval(timer); }, [weddingId]);
  const totalAssigned = useMemo(() => Object.values(guestCounts).reduce((sum, count) => sum + count, 0), [guestCounts]);

  return <section className="list-page">
    <div className="list-title"><div>{onBack && <button className="back-link" onClick={onBack}>‹ Továbbiak</button>}<p className="eyebrow">MEGHÍVOTTAK</p><h1>Csoportok</h1></div><div className="list-actions"><strong>{groups.length} csoport · {totalAssigned} fő</strong><button onClick={() => setEditing('new')} aria-label="Új csoport">＋</button></div></div>
    <div className="group-list">{loading ? <p className="empty-list">Csoportok betöltése…</p> : groups.length ? groups.map((group) => <button className="group-row" key={group.id} onClick={() => setEditing(group)}><span className="group-monogram">{group.name.slice(0, 1).toUpperCase()}</span><span><strong>{group.name}</strong><small>{group.group_type || 'Egyéb'}{group.contact_name ? ` · ${group.contact_name}` : ''}</small></span><b>{guestCounts[group.id] ?? 0} fő</b></button>) : <p className="empty-list">Még nincs meghívási csoport.</p>}</div>
    {editing && <GroupEditor weddingId={weddingId} group={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
  </section>;
}

function GroupEditor({ weddingId, group, onClose, onSaved }: { weddingId: string; group: InvitationGroup | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: group?.name ?? '', group_type: group?.group_type ?? 'Család', contact_name: group?.contact_name ?? '', email: group?.email ?? '', phone: group?.phone ?? '', rsvp_due_date: group?.rsvp_due_date ?? '', notes: group?.notes ?? '' });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    const payload = { ...form, contact_name: form.contact_name || null, email: form.email || null, phone: form.phone || null, rsvp_due_date: form.rsvp_due_date || null, notes: form.notes || null, updated_at: new Date().toISOString() };
    const result = group ? await supabase!.from('invitation_groups').update(payload).eq('id', group.id) : await supabase!.from('invitation_groups').insert({ ...payload, wedding_id: weddingId });
    setBusy(false); if (result.error) setMessage(result.error.message); else onSaved();
  }
  return <div className="modal-backdrop" role="dialog" aria-modal="true"><section className="editor-card"><div className="editor-heading"><div><p className="eyebrow">MEGHÍVÁSI CSOPORT</p><h2>{group ? group.name : 'Új csoport'}</h2></div><button onClick={onClose} aria-label="Bezárás">×</button></div><form onSubmit={save}>
    <label>Csoport neve<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
    <label>Típus<select value={form.group_type} onChange={(e) => setForm({ ...form, group_type: e.target.value })}>{['Család','Barátok','Rokonság','Munkahely','Egyéb'].map((value) => <option key={value}>{value}</option>)}</select></label>
    <label>Kapcsolattartó<input value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} /></label>
    <div className="form-row"><label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label><label>Telefon<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label></div>
    <label>Visszajelzési határidő<input type="date" value={form.rsvp_due_date} onChange={(e) => setForm({ ...form, rsvp_due_date: e.target.value })} /></label>
    <label>Megjegyzés<textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
    {message && <p className="form-message">{message}</p>}<button className="primary-action" disabled={busy}>{busy ? 'Mentés…' : 'Mentés'}</button>
  </form></section></div>;
}
