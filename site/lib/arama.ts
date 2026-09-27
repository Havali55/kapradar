// Başlıktaki hisse arama: saf eşleştirme. İstemci bileşeninden ayrı ki
// `node --test` ile tarayıcısız sınansın.

export type HisseSecenek = {
  /** Borsa kodu. */
  t: string;
  /** KAP'taki unvan, büyük harf. */
  s: string;
  /** Arşivdeki yeni iş bildirimi sayısı. */
  n: number;
};

export const ARAMA_SINIRI = 6;

const buyut = (s: string) => s.toLocaleUpperCase("tr");

/**
 * Önce ticker öneki, sonra unvan içinde geçenler; her grup kendi içinde
 * bildirim sayısına göre. Sorgu Türkçe kurallarla büyütülüyor: "i" → "İ",
 * yoksa "elektronik" KAP'ın "ELEKTRONİK" unvanını bulamaz.
 */
export function hisseEsle(
  liste: readonly HisseSecenek[],
  sorgu: string,
  sinir = ARAMA_SINIRI,
): HisseSecenek[] {
  const q = buyut(sorgu.trim());
  if (!q) return [];
  const onek: HisseSecenek[] = [];
  const icinde: HisseSecenek[] = [];
  for (const h of liste) {
    if (h.t.startsWith(q)) onek.push(h);
    else if (buyut(h.s).includes(q)) icinde.push(h);
  }
  const sira = (a: HisseSecenek, b: HisseSecenek) =>
    b.n - a.n || a.t.localeCompare(b.t, "tr");
  return [...onek.sort(sira), ...icinde.sort(sira)].slice(0, sinir);
}
