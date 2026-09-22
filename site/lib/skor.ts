/**
 * Skor ölçeğinin site tarafındaki aynası — saf fonksiyonlar, veri
 * erişimi yok.
 *
 * Neden `veri.ts`'ten ayrı: bu fonksiyonları istemci bileşenleri de
 * kullanıyor (kartın rengi, panelin formül satırı). `veri.ts` Supabase
 * istemcisini içe aktarıyor; oradan bir fonksiyon almak tüm veri
 * katmanını tarayıcı paketine sürüklerdi.
 *
 * KANONİK TANIM `src/kap_radar/skor.py`. Buradaki her sabit onun
 * kopyası; biri değişirse diğeri de değişmeli.
 */

/** Ölçeğin çapaları — `skor.Agirliklar` ile birebir aynı. */
export const TABAN_ORAN = 0.0025;
export const TAVAN_ORAN = 1.0;

/** Kademe eşikleri — `skor.MEGA_ESIGI` / `skor.ONEMLI_ESIGI`. */
export const MEGA_ESIGI = 3.5;
export const ONEMLI_ESIGI = 2.5;

export type Kademe = "rutin" | "onemli" | "mega";

/**
 * Eşikler 2026-09-22'de 3/2'den 3,5/2,5'e çıkarıldı — skor enflasyonu
 * DEĞİL, telafisi. Aynı gün formülün tabanı %1'den %0,25'e indi; taban
 * eksenin sıfır noktası olduğu için altındaki her şey yukarı kaydı
 * (medyan 1,39 → 2,02). Eşikler yerinde bıraksaydık "Mega iş" 60
 * bildirimden 94'e çıkardı, yani etiketin anlamı kullanıcıya haber
 * verilmeden değişirdi.
 *
 * Yeni eşikler kademelerin nüfus içindeki payını koruyor: 3,5 → 55
 * bildirim (eskiden 60), 2,5 → 164 (eskiden 153).
 */
export function kademeBul(skor: number | null): Kademe | null {
  if (skor === null) return null;
  if (skor >= MEGA_ESIGI) return "mega";
  if (skor >= ONEMLI_ESIGI) return "onemli";
  return "rutin";
}

/**
 * f(r) — skoru YENİDEN HESAPLAMAK için değil, veritabanındaki sayının
 * nasıl çıktığını göstermek için. Kullanıcı 5·f(r)·K çarpımını kendi
 * yapıp `etki_skoru` ile karşılaştırabilsin diye duruyor.
 *
 * Bu fonksiyonun bir kopyası 2026-09-22'ye kadar DetayPanel içinde eski
 * tabanla duruyordu; taban değişince panel uyuşmayan bir çarpım
 * gösterir hâle gelmişti. Ölçeğin bütün aynaları artık bu dosyada.
 */
export function fOran(r: number): number {
  if (r <= TABAN_ORAN) return 0;
  if (r >= TAVAN_ORAN) return 1;
  const taban = Math.log10(TABAN_ORAN);
  return (Math.log10(r) - taban) / (Math.log10(TAVAN_ORAN) - taban);
}

/** Panelde formülün okunabilir hâli; eşik değişirse metin de değişsin. */
export const F_ORAN_METNI = "f(r) = (log₁₀ r + 2,602) / 2,602";

/**
 * K — skorun içindeki güvenilirlik çarpanı. Burada YENİDEN HESAPLANMIYOR,
 * yalnızca gösterim için aynı tablodan okunuyor; skorun kendisi
 * veritabanından geliyor (`etki_skoru`).
 */
export function guvenilirlik(ktAcik: boolean, guncelleme: boolean): number {
  if (ktAcik) return guncelleme ? 0.85 : 1.0;
  return guncelleme ? 0.7 : 0.5;
}

/**
 * En yakın sıra istatistiği; ara değer üretmiyor. Python tarafındaki
 * `skor._yuzdelik` ile birebir aynı: gerçekten gözlenmiş bir getiriyi
 * göstermek, iki gözlem arasında hiç yaşanmamış bir sayı uydurmaktan
 * dürüst.
 */
export function yuzdelik(sirali: number[], oran: number): number {
  return sirali[Math.floor(oran * (sirali.length - 1))];
}

/**
 * Renk kademeden türetiliyor, kendi eşiğini taşımıyor. Eskiden burada
 * 3/2 sabitleri vardı ve eşikler 3,5/2,5'e taşınınca kartın rengiyle
 * üstündeki etiket ayrışıyordu: 3,2 alan bir bildirim "Önemli iş"
 * yazıp "mega" rengiyle çiziliyordu.
 */
export function skorRengi(skor: number | null): string {
  const k = kademeBul(skor);
  if (k === "mega") return "var(--mavi-koyu)";
  if (k === "onemli") return "var(--mavi)";
  if (k === "rutin") return "var(--mut-2)";
  return "var(--ken)";
}

export function tahtaRenk(tahta: string): string {
  if (tahta === "temiz") return "yes";
  if (tahta === "hareketli") return "kehribar";
  return "kir";
}
