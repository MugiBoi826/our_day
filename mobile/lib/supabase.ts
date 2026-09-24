import { createClient } from '@supabase/supabase-js';

// These values identify the public Supabase API and are safe to ship to the browser.
// Environment variables can still override them for another deployment.
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  || 'https://nhgprzjnaunfcdbefbsx.supabase.co';
const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  || 'sb_publishable_r21ppU3g50eYM1lZ1pZaEw_kW9DWj9X';

export const isSupabaseConfigured = Boolean(supabaseUrl && publishableKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl!, publishableKey!, {
      auth: { persistSession: true, autoRefreshToken: true },
    })
  : null;
