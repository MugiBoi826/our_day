'use client';

import { FormEvent, useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

export type GuestPreference = { id: string; category: string; name: string };

const DEFAULT_CATEGORIES = ['Étrend', 'Érzékenység', 'Allergia', 'Különleges igény'];

export function PreferencesPanel({ weddingId, onBack }: { weddingId: string; onBack: () => void }) {
  const [items, setItems] = useState<GuestPreference[]>([]);
  const [category, setCategory] = useState(DEFAULT_CATEGORIES[1]);
  const [customCategory, setCustomCategory] = useState('');
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    const { data, error } = await supabase!.from('guest_preferences').select('id,category,name').eq('wedding_id', weddingId).order('category').order('name');
    if (error) setMessage(error.message); else setItems((data ?? []) as GuestPreference[]);
  }

  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer); }, [weddingId]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const finalCategory = (category === 'Egyéb kategória' ? customCategory : category).trim();
    const finalName = name.trim();
    if (!finalCategory || !finalName) return;
    if (items.some((item) => item.category.toLocaleLowerCase('hu') === finalCategory.toLocaleLowerCase('hu') && item.name.toLocaleLowerCase('hu') === finalName.toLocaleLowerCase('hu'))) {
      setMessage('Ez az igény már szerepel a listában.'); return;
    }
    setBusy(true); setMessage('');
    const { error } = await supabase!.from('guest_preferences').insert({ wedding_id: weddingId, category: finalCategory, name: finalName });
    setBusy(false);
    if (error) setMessage(error.message); else { setName(''); setCustomCategory(''); await load(); }
  }

  async function remove(item: GuestPreference) {
    if (!window.confirm(`Biztosan törlöd ezt az elemet: ${item.category} – ${item.name}? A vendégekről is lekerül.`)) return;
    setBusy(true); setMessage('');
    const { error } = await supabase!.from('guest_preferences').delete().eq('id', item.id).eq('wedding_id', weddingId);
    setBusy(false);
    if (error) setMessage(error.message); else await load();
  }

  const grouped = items.reduce<Record<string, GuestPreference[]>>((result, item) => {
    (result[item.category] ??= []).push(item); return result;
  }, {});

  return <section className="settings-page preference-page"><button className="back-link" onClick={onBack}>‹ Továbbiak</button><p className="eyebrow">VENDÉGADATOK</p><h1>Igények és érzékenységek</h1>
    <p className="settings-lead">Itt veheted fel az ételérzékenységeket, allergiákat és egyéb különleges igényeket. Ezeket utána többesével is kiválaszthatod a vendégeknél.</p>
    <form className="settings-form preference-form" onSubmit={create}>
      <label>Kategória<select value={category} onChange={(event) => setCategory(event.target.value)}>{DEFAULT_CATEGORIES.map((value) => <option key={value}>{value}</option>)}<option>Egyéb kategória</option></select></label>
      {category === 'Egyéb kategória' && <label>Kategória neve<input value={customCategory} onChange={(event) => setCustomCategory(event.target.value)} required /></label>}
      <label>Megnevezés<input value={name} onChange={(event) => setName(event.target.value)} placeholder="pl. Akadálymentes megközelítés" required /></label>
      {message && <p className="form-message">{message}</p>}<button className="primary-action" disabled={busy}>{busy ? 'Mentés…' : 'Új elem felvétele'}</button>
    </form>
    <div className="preference-groups">{Object.keys(grouped).length ? Object.entries(grouped).map(([group, values]) => <section key={group}><h2>{group}</h2>{values.map((item) => <div className="preference-row" key={item.id}><span>{item.name}</span><button onClick={() => remove(item)} disabled={busy} aria-label={`${item.name} törlése`}>Törlés</button></div>)}</section>) : <p className="empty-list">Még nincs felvett igény.</p>}</div>
  </section>;
}
