'use client';

import type { User } from '@supabase/supabase-js';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { isSupabaseConfigured, supabase } from '@/lib/supabase';
import { importDesktopDatabase } from '@/lib/importDesktop';
import { TasksPanel } from '@/components/TasksPanel';
import { ServicesPanel } from '@/components/ServicesPanel';

type Tab = 'Kezdőlap' | 'Vendégek' | 'Teendők' | 'Szolgáltatók' | 'Továbbiak';
type Wedding = { id: string; bride_name: string; groom_name: string; wedding_date: string | null; venue_name: string | null; budget_amount: number };

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [wedding, setWedding] = useState<Wedding | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) { setLoading(false); return; }
    supabase.auth.getSession().then(({ data }) => { setUser(data.session?.user ?? null); setLoading(false); });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setUser(session?.user ?? null));
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!supabase || !user) { setWedding(null); return; }
    supabase.from('weddings').select('id,bride_name,groom_name,wedding_date,venue_name,budget_amount').order('created_at').limit(1).maybeSingle()
      .then(({ data }) => setWedding(data as Wedding | null));
  }, [user]);

  if (loading) return <LoadingScreen />;
  if (!isSupabaseConfigured || !supabase) return <MessageScreen title="Helyi mód" message="A felhőkapcsolat még nincs beállítva." />;
  if (!user) return <AuthScreen />;
  if (!wedding) return <WeddingSetup user={user} onCreated={setWedding} />;
  return <Dashboard user={user} wedding={wedding} />;
}

function AuthScreen() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    const result = mode === 'login'
      ? await supabase!.auth.signInWithPassword({ email, password })
      : await supabase!.auth.signUp({ email, password });
    if (result.error) setMessage(result.error.message);
    else if (mode === 'signup' && !result.data.session) setMessage('Megerősítő emailt küldtünk. A belépéshez nyisd meg a benne lévő hivatkozást.');
    setBusy(false);
  }

  return <main className="auth-shell"><section className="auth-card">
    <div className="auth-logo">O</div><p className="eyebrow">OUR DAY MOBIL</p>
    <h1>{mode === 'login' ? 'Üdv újra!' : 'Kezdjük el együtt'}</h1>
    <p className="auth-lead">Az esküvőszervezés minden fontos részlete, mindig kéznél.</p>
    <form onSubmit={submit}>
      <label>Email-cím<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      <label>Jelszó<input type="password" minLength={6} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      {message && <p className="form-message">{message}</p>}
      <button className="primary-action" disabled={busy}>{busy ? 'Egy pillanat…' : mode === 'login' ? 'Belépés' : 'Regisztráció'}</button>
    </form>
    <button className="text-action" onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setMessage(''); }}>{mode === 'login' ? 'Még nincs fiókod? Regisztrálj' : 'Már van fiókod? Lépj be'}</button>
  </section></main>;
}

function WeddingSetup({ user, onCreated }: { user: User; onCreated: (wedding: Wedding) => void }) {
  const [bride, setBride] = useState(''); const [groom, setGroom] = useState(''); const [date, setDate] = useState('');
  const [venue, setVenue] = useState(''); const [budget, setBudget] = useState(''); const [message, setMessage] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault(); setMessage('');
    const { data, error } = await supabase!.from('weddings').insert({ bride_name: bride, groom_name: groom, wedding_date: date || null, venue_name: venue || null, budget_amount: Number(budget) || 0, created_by: user.id }).select().single();
    if (error) setMessage(error.message); else onCreated(data as Wedding);
  }
  return <main className="auth-shell"><section className="auth-card setup-card"><p className="eyebrow">ELSŐ LÉPÉS</p><h1>A ti nagy napotok</h1><p className="auth-lead">Add meg az alapadatokat. Később mindent módosíthatsz.</p>
    <form onSubmit={submit}><div className="form-row"><label>Menyasszony<input value={bride} onChange={(e) => setBride(e.target.value)} required /></label><label>Vőlegény<input value={groom} onChange={(e) => setGroom(e.target.value)} required /></label></div>
      <label>Esküvő dátuma<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label><label>Helyszín<input value={venue} onChange={(e) => setVenue(e.target.value)} /></label><label>Tervezett költségkeret (Ft)<input type="number" min="0" step="10000" value={budget} onChange={(e) => setBudget(e.target.value)} /></label>
      {message && <p className="form-message">{message}</p>}<button className="primary-action">Projekt létrehozása</button>
    </form></section></main>;
}

function Dashboard({ user, wedding }: { user: User; wedding: Wedding }) {
  const [activeTab, setActiveTab] = useState<Tab>('Kezdőlap');
  const [cloudTasks, setCloudTasks] = useState<Array<{ id: string; title: string; due_date: string | null; priority: string; status: string }>>([]);
  const [cloudGuests, setCloudGuests] = useState<Array<{ id: string; name: string; attendance_status: string; table_id: string | null }>>([]);
  const [summary, setSummary] = useState({ guests: 0, confirmed: 0, assigned: 0, planned: 0 });
  const daysLeft = useMemo(() => wedding.wedding_date ? Math.max(0, Math.ceil((new Date(`${wedding.wedding_date}T12:00:00`).getTime() - Date.now()) / 86_400_000)) : 0, [wedding.wedding_date]);
  const dateLabel = wedding.wedding_date ? new Intl.DateTimeFormat('hu-HU', { dateStyle: 'long' }).format(new Date(`${wedding.wedding_date}T12:00:00`)) : 'A dátum még nincs megadva';
  const initials = `${wedding.bride_name[0] ?? ''}${wedding.groom_name[0] ?? ''}`.toUpperCase();

  useEffect(() => {
    async function loadDashboard() {
      const [guestsResult, confirmedResult, assignedResult, tasksResult, entriesResult] = await Promise.all([
        supabase!.from('guests').select('id,name,attendance_status,table_id', { count: 'exact' }).eq('wedding_id', wedding.id).order('name').limit(3),
        supabase!.from('guests').select('id', { count: 'exact', head: true }).eq('wedding_id', wedding.id).eq('attendance_status', 'Részt vesz'),
        supabase!.from('guests').select('id', { count: 'exact', head: true }).eq('wedding_id', wedding.id).not('table_id', 'is', null),
        supabase!.from('tasks').select('id,title,due_date,priority,status').eq('wedding_id', wedding.id).neq('status', 'Elkészült').order('due_date', { ascending: true, nullsFirst: false }).limit(3),
        supabase!.from('entries').select('total_amount,status').eq('wedding_id', wedding.id),
      ]);
      setCloudGuests((guestsResult.data ?? []) as typeof cloudGuests);
      setCloudTasks((tasksResult.data ?? []) as typeof cloudTasks);
      const planned = (entriesResult.data ?? []).filter((entry) => !['Ötlet', 'Ajánlatkérés', 'Lemondva'].includes(entry.status)).reduce((sum, entry) => sum + Number(entry.total_amount || 0), 0);
      setSummary({ guests: guestsResult.count ?? 0, confirmed: confirmedResult.count ?? 0, assigned: assignedResult.count ?? 0, planned });
    }
    loadDashboard();
  }, [wedding.id]);

  async function completeTask(taskId: string) {
    const { error } = await supabase!.from('tasks').update({ status: 'Elkészült' }).eq('id', taskId);
    if (!error) setCloudTasks((current) => current.filter((task) => task.id !== taskId));
  }

  const seatingPercent = summary.guests ? Math.round(summary.assigned / summary.guests * 100) : 0;
  return <main className="app-shell">
    <header className="topbar"><div className="brand-mark">O</div><div><p className="eyebrow">OUR DAY</p><p className="welcome">{wedding.bride_name} &amp; {wedding.groom_name}</p></div><span className="cloud-state online">● Online</span><button className="avatar" onClick={() => supabase!.auth.signOut()} title={user.email ?? 'Kijelentkezés'}>{initials}</button></header>
    <div className="content">{activeTab === 'Kezdőlap' ? <>
      <section className="hero"><div className="hero-copy"><span className="hero-label">A nagy napig</span><strong>{daysLeft}</strong><span className="days">nap van hátra</span><h1>{wedding.bride_name} &amp; {wedding.groom_name}</h1><p>{dateLabel}{wedding.venue_name ? ` · ${wedding.venue_name}` : ''}</p></div><div className="rings"><i /><i /></div></section>
      <section className="stats"><article><span>Vendégek</span><strong>{summary.guests}</strong><small>{summary.confirmed} visszajelzett</small></article><article><span>Ültetés</span><strong>{seatingPercent}%</strong><small>{summary.assigned} fő elhelyezve</small></article><article><span>Keret</span><strong>{formatBudget(wedding.budget_amount)}</strong><small>{formatMoney(summary.planned)} tervezve</small></article></section>
      <section className="section-block"><div className="section-heading"><div><span className="kicker">Következő lépések</span><h2>Teendők</h2></div><button onClick={() => setActiveTab('Teendők')}>Összes</button></div><div className="task-list">{cloudTasks.length ? cloudTasks.map((task) => <button className="task" key={task.id} onClick={() => completeTask(task.id)}><span className="check" /><span className="task-copy"><strong>{task.title}</strong><small>{formatDate(task.due_date)} · {task.priority} prioritás</small></span><span className="chevron">›</span></button>) : <p className="empty-list">Nincs nyitott teendő.</p>}</div></section>
      <section className="section-block"><div className="section-heading"><div><span className="kicker">Felhőből betöltve</span><h2>Vendégek</h2></div><button onClick={() => setActiveTab('Vendégek')}>Megnyitás</button></div><div className="guest-list">{cloudGuests.length ? cloudGuests.map((guest) => <article className="guest" key={guest.id}><span className="guest-avatar">{guest.name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()}</span><span><strong>{guest.name}</strong><small>{guest.table_id ? 'Asztalhoz rendelve' : 'Nincs asztal'}</small></span><em className={guest.attendance_status === 'Részt vesz' ? 'yes' : 'waiting'}>{guest.attendance_status}</em></article>) : <p className="empty-list">Még nincs vendég.</p>}</div></section>
    </> : activeTab === 'Vendégek' ? <GuestsPanel weddingId={wedding.id} /> : activeTab === 'Teendők' ? <TasksPanel weddingId={wedding.id} /> : activeTab === 'Szolgáltatók' ? <ServicesPanel weddingId={wedding.id} /> : <ImportPanel weddingId={wedding.id} />}</div>
    <nav className="bottom-nav five-tabs">{(['Kezdőlap','Vendégek','Teendők','Szolgáltatók','Továbbiak'] as Tab[]).map(tab=><button key={tab} className={activeTab===tab?'active':''} onClick={()=>setActiveTab(tab)}><span>{tab==='Kezdőlap'?'⌂':tab==='Vendégek'?'♧':tab==='Teendők'?'✓':tab==='Szolgáltatók'?'₣':'•••'}</span>{tab}</button>)}</nav>
  </main>;
}

function GuestsPanel({ weddingId }: { weddingId: string }) {
  type GuestRecord = { id: string; name: string; email: string | null; phone: string | null; guest_type: string; attendance_status: string; invitation_status: string; table_id: string | null; attends_dinner: boolean; dietary_notes: string | null; notes: string | null };
  const [guests, setGuests] = useState<GuestRecord[]>([]); const [editing, setEditing] = useState<GuestRecord | 'new' | null>(null);
  const [query, setQuery] = useState(''); const [filter, setFilter] = useState('Mind'); const [loading, setLoading] = useState(true);
  async function loadGuests() { setLoading(true); const { data } = await supabase!.from('guests').select('id,name,email,phone,guest_type,attendance_status,invitation_status,table_id,attends_dinner,dietary_notes,notes').eq('wedding_id', weddingId).order('name'); setGuests((data ?? []) as GuestRecord[]); setLoading(false); }
  useEffect(() => { loadGuests(); }, [weddingId]);
  const visible = guests.filter((guest) => guest.name.toLocaleLowerCase('hu').includes(query.toLocaleLowerCase('hu')) && (filter === 'Mind' || guest.attendance_status === filter));
  return <section className="list-page"><div className="list-title"><div><p className="eyebrow">MEGHÍVOTTAK</p><h1>Vendégek</h1></div><div className="list-actions"><strong>{guests.length} fő</strong><button onClick={() => setEditing('new')} aria-label="Új vendég">＋</button></div></div>
    <input className="search-input" type="search" placeholder="Keresés név alapján…" value={query} onChange={(event) => setQuery(event.target.value)} />
    <div className="filter-row">{['Mind', 'Részt vesz', 'Válaszra vár', 'Nem vesz részt'].map((item) => <button key={item} className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}</div>
    <div className="guest-list full-list">{loading ? <p className="empty-list">Vendégek betöltése…</p> : visible.length ? visible.map((guest) => <button className="guest guest-button" key={guest.id} onClick={() => setEditing(guest)}><span className="guest-avatar">{guest.name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()}</span><span><strong>{guest.name}</strong><small>{guest.email || guest.invitation_status}</small></span><em className={guest.attendance_status === 'Részt vesz' ? 'yes' : 'waiting'}>{guest.attendance_status}</em></button>) : <p className="empty-list">Nincs találat.</p>}</div>
    {editing && <GuestEditor weddingId={weddingId} guest={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); loadGuests(); }} />}
  </section>;
}

function GuestEditor({ weddingId, guest, onClose, onSaved }: { weddingId: string; guest: { id: string; name: string; email: string | null; phone: string | null; guest_type: string; attendance_status: string; invitation_status: string; attends_dinner: boolean; dietary_notes: string | null; notes: string | null } | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: guest?.name ?? '', email: guest?.email ?? '', phone: guest?.phone ?? '', guest_type: guest?.guest_type ?? 'Felnőtt', attendance_status: guest?.attendance_status ?? 'Válaszra vár', invitation_status: guest?.invitation_status ?? 'Tervezett', attends_dinner: guest?.attends_dinner ?? true, dietary_notes: guest?.dietary_notes ?? '', notes: guest?.notes ?? '' });
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  function field(name: keyof typeof form, value: string | boolean) { setForm((current) => ({ ...current, [name]: value })); }
  async function save(event: FormEvent) { event.preventDefault(); setBusy(true); setMessage(''); const payload = { ...form, email: form.email || null, phone: form.phone || null, dietary_notes: form.dietary_notes || null, notes: form.notes || null }; const result = guest ? await supabase!.from('guests').update(payload).eq('id', guest.id) : await supabase!.from('guests').insert({ ...payload, wedding_id: weddingId }); setBusy(false); if (result.error) setMessage(result.error.message); else onSaved(); }
  return <div className="modal-backdrop" role="dialog" aria-modal="true"><section className="editor-card"><div className="editor-heading"><div><p className="eyebrow">{guest ? 'SZERKESZTÉS' : 'ÚJ MEGHÍVOTT'}</p><h2>{guest ? guest.name : 'Vendég felvétele'}</h2></div><button onClick={onClose} aria-label="Bezárás">×</button></div><form onSubmit={save}>
    <label>Név<input value={form.name} onChange={(e) => field('name', e.target.value)} required /></label><div className="form-row"><label>Email<input type="email" value={form.email} onChange={(e) => field('email', e.target.value)} /></label><label>Telefon<input value={form.phone} onChange={(e) => field('phone', e.target.value)} /></label></div>
    <div className="form-row"><label>Vendégtípus<select value={form.guest_type} onChange={(e) => field('guest_type', e.target.value)}><option>Felnőtt</option><option>Gyermek</option></select></label><label>Részvétel<select value={form.attendance_status} onChange={(e) => field('attendance_status', e.target.value)}><option>Válaszra vár</option><option>Részt vesz</option><option>Nem vesz részt</option></select></label></div>
    <label>Meghívás állapota<select value={form.invitation_status} onChange={(e) => field('invitation_status', e.target.value)}><option>Tervezett</option><option>Meghívó elküldve</option><option>Visszajelzett</option></select></label><label className="toggle-label"><input type="checkbox" checked={form.attends_dinner} onChange={(e) => field('attends_dinner', e.target.checked)} /> Részt vesz a vacsorán</label>
    <label>Étrendi igény<textarea value={form.dietary_notes} onChange={(e) => field('dietary_notes', e.target.value)} /></label><label>Megjegyzés<textarea value={form.notes} onChange={(e) => field('notes', e.target.value)} /></label>{message && <p className="form-message">{message}</p>}<button className="primary-action" disabled={busy}>{busy ? 'Mentés…' : 'Mentés'}</button>
  </form></section></div>;
}

function ImportPanel({ weddingId }: { weddingId: string }) {
  const [file, setFile] = useState<File | null>(null); const [status, setStatus] = useState(''); const [busy, setBusy] = useState(false); const [done, setDone] = useState(false);
  async function startImport() {
    if (!file) return; setBusy(true); setDone(false);
    try { const result = await importDesktopDatabase(file, weddingId, setStatus); setStatus(`Kész: ${result.guests} vendég, ${result.groups} csoport, ${result.tables} asztal, ${result.tasks} feladat és ${result.entries} szolgáltatás.`); setDone(true); window.setTimeout(() => window.location.reload(), 1200); }
    catch (error) { setStatus(error instanceof Error ? error.message : 'Az import nem sikerült.'); }
    finally { setBusy(false); }
  }
  return <section className="import-page"><p className="eyebrow">ADATÁTVITEL</p><h1>Asztali adatbázis</h1><p className="auth-lead">Válaszd ki az előkészített importfájlt. Az eredeti asztali adatbázis változatlan marad.</p><label className="file-picker"><span>{file ? file.name : 'Importfájl kiválasztása'}</span><input type="file" accept="application/json,.json" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>{status && <p className={`import-status ${done ? 'success' : ''}`}>{status}</p>}<button className="primary-action import-button" disabled={!file || busy} onClick={startImport}>{busy ? 'Importálás folyamatban…' : 'Adatok importálása'}</button><p className="privacy-note">A fájl tartalma közvetlenül ebből az eszközből kerül a saját Supabase projektedbe.</p></section>;
}

function LoadingScreen() { return <main className="auth-shell"><div className="auth-logo pulse">O</div></main>; }
function MessageScreen({ title, message }: { title: string; message: string }) { return <main className="auth-shell"><section className="auth-card"><div className="auth-logo">O</div><h1>{title}</h1><p className="auth-lead">{message}</p></section></main>; }
function formatBudget(value: number) { return value >= 1_000_000 ? `${(value / 1_000_000).toLocaleString('hu-HU', { maximumFractionDigits: 1 })} M` : `${Math.round(value / 1000)} e`; }
function formatMoney(value: number) { return `${Math.round(value).toLocaleString('hu-HU')} Ft`; }
function formatDate(value: string | null) { return value ? new Intl.DateTimeFormat('hu-HU', { month: 'short', day: 'numeric' }).format(new Date(`${value}T12:00:00`)) : 'Nincs határidő'; }
