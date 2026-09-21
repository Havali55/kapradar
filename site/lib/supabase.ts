import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anahtar = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!url || !anahtar) {
  throw new Error(
    "NEXT_PUBLIC_SUPABASE_URL ve NEXT_PUBLIC_SUPABASE_ANON_KEY tanımlı değil. " +
      ".env.local.example dosyasını kopyalayıp doldurun.",
  );
}

/**
 * Yayınlanabilir anahtarla bağlanır. Gizli anahtar siteye hiç girmiyor —
 * okunabilen tek şey `public.akis` view'ı, o da yalnızca kapıdan geçmiş
 * bildirimleri gösteriyor.
 */
export const supabase = createClient(url, anahtar, {
  auth: { persistSession: false },
});
