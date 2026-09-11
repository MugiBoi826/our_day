'use client';

import { FormEvent, useState } from 'react';
import { supabase } from '@/lib/supabase';

export type WeddingSettings = { id: string; bride_name: string; groom_name: string; wedding_date: string | null; venue_name: string | null; venue_address: string | null; budget_amount: number; notes: string | null };

export function WeddingSettingsPanel({ wedding, onBack, onSaved }: { wedding: WeddingSettings; onBack: () => void; onSaved: (value: WeddingSettings) => void }) {
  const [form, setForm] = useState({ bride_name: wedding.bride_name, groom_name: wedding.groom_name, wedding_date: wedding.wedding_date ?? '', venue_name: wedding.venue_name ?? '', venue_address: wedding.venue_address ?? '', budget_amount: String(wedding.budget_amount ?? 0), notes: wedding.notes ?? '' });
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    const payload = { ...form, wedding_date: form.wedding_date || null, venue_name: form.venue_name || null, venue_address: form.venue_address || null, budget_amount: Number(form.budget_amount) || 0, notes: form.notes || null, updated_at: new Date().toISOString() };
    const { data, error } = await supabase!.from('weddings').update(payload).eq('id', wedding.id).select('id,bride_name,groom_name,wedding_date,venue_name,venue_address,budget_amount,notes').single();
    setBusy(false); if (error) setMessage(error.message); else { setMessage('Az alapadatok elmentve.'); onSaved(data as WeddingSettings); }
  }
  return <section className="settings-page"><button className="back-link" onClick={onBack}>‹ Továbbiak</button><p className="eyebrow">ALAPBEÁLLÍTÁSOK</p><h1>A nagy nap</h1><form className="settings-form" onSubmit={save}>
    <div className="form-row"><label>Menyasszony<input value={form.bride_name} onChange={(e) => setForm({ ...form, bride_name: e.target.value })} required /></label><label>Vőlegény<input value={form.groom_name} onChange={(e) => setForm({ ...form, groom_name: e.target.value })} required /></label></div>
    <label>Dátum<input type="date" value={form.wedding_date} onChange={(e) => setForm({ ...form, wedding_date: e.target.value })} /></label>
    <label>Helyszín<input value={form.venue_name} onChange={(e) => setForm({ ...form, venue_name: e.target.value })} /></label>
    <label>Helyszín címe<input value={form.venue_address} onChange={(e) => setForm({ ...form, venue_address: e.target.value })} /></label>
    <label>Költségkeret (Ft)<input type="number" min="0" step="10000" value={form.budget_amount} onChange={(e) => setForm({ ...form, budget_amount: e.target.value })} /></label>
    <label>Megjegyzés<textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
    {message && <p className="form-message success-message">{message}</p>}<button className="primary-action" disabled={busy}>{busy ? 'Mentés…' : 'Alapadatok mentése'}</button>
  </form></section>;
}
