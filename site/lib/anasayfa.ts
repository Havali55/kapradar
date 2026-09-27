// Ana sayfanın seçimleri: cetvel plakasının penceresi, en büyük işler,
// satır metinleri. Saf ve içe aktarmasız; `node --test` doğrudan koşar.

const GUN_MS = 86_400_000;
export const KISA_PENCERE = 14;
export const UZUN_PENCERE = 30;
/** Kısa pencerede bundan az iş varsa plaka boş görünür; pencere uzar. */
export const ASGARI_IS = 8;

export type PencereGirdi = {
  yayin_zamani: string;
  ciro_orani: number | null;
  onceki_tur?: string | null;
};

/**
 * Büyüklük olarak sayılan iş: oranı var ve daha önce aynı tutarla
 * duyurulmamış (`ayni_is`). Akışın "en büyük iş" kuralıyla aynı.
 */
export function sayilanIs(s: PencereGirdi): boolean {
  return s.ciro_orani !== null && s.onceki_tur !== "ayni_is";
}

/** Son 14 günün sayılan işleri; 8'den azsa son 30 gün. */
export function cetvelPenceresi<T extends PencereGirdi>(
  satirlar: readonly T[],
  simdi: number,
): { gun: number; isler: T[] } {
  const aday = satirlar.filter(sayilanIs);
  const icinde = (gun: number) =>
    aday.filter((s) => {
      const z = Date.parse(s.yayin_zamani);
      return z <= simdi && z > simdi - gun * GUN_MS;
    });
  const kisa = icinde(KISA_PENCERE);
  if (kisa.length >= ASGARI_IS) return { gun: KISA_PENCERE, isler: kisa };
  return { gun: UZUN_PENCERE, isler: icinde(UZUN_PENCERE) };
}

/** Ciro oranına göre en büyükler; eşitlikte yeni olan önce. */
export function enBuyukler<T extends PencereGirdi>(isler: readonly T[], adet = 3): T[] {
  return [...isler]
    .sort(
      (a, b) =>
        (b.ciro_orani ?? 0) - (a.ciro_orani ?? 0) ||
        Date.parse(b.yayin_zamani) - Date.parse(a.yayin_zamani),
    )
    .slice(0, adet);
}

/** Satırda gösterilen özet: hap özetin ilk maddesi, yoksa iş tanımı. */
export function ozetMetni(s: { hap_ozet: string[] | null; is_tanimi: string | null }): string {
  return s.hap_ozet?.[0] ?? s.is_tanimi ?? "Özet yok";
}

/**
 * Karşı tarafın adı, isimle açıklanmışsa. Alan dolu olabilir ama isim
 * olmayabilir ("Uluslararası Müşteri"): sınıflandırıcı (`karsi_taraf_acik`)
 * karar verir. Sınıflandırılmamış eski satırda alan doluysa açık sayılır
 * (`veri.ts` `zenginlestir` ile aynı kural).
 */
export function karsiTarafMetni(s: {
  karsi_taraf: string | null;
  karsi_taraf_acik?: boolean | null;
}): string | null {
  const acik = s.karsi_taraf_acik != null ? s.karsi_taraf_acik : s.karsi_taraf !== null;
  return acik ? s.karsi_taraf : null;
}
