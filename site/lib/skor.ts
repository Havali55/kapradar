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
 * Kullanıcının GÖRDÜĞÜ büyüklük kademesi — doğrudan ciro oranından, S'den
 * değil (2026-09-24 kararı). S içindeki K çarpanı gizli karşı taraflı ya
 * da güncelleme bildirimlerini aşağı çekiyor; "cirosunun %37'si · Rutin"
 * gibi kendi içinde çelişen bir kart çıkıyordu. K bir güvenilirlik
 * ayarı, büyüklük değil — büyüklük etiketine karışmamalı.
 *
 * Eşikler S kademeleriyle aynı yerde: K = 1'de S = 2,5 tam %5'e, S = 3,5
 * %16,6'ya denk düşüyor; üst eşik okunabilirlik için %15'e yuvarlandı.
 * Skorlu 481 bildirimde: %5+ → 226, %15+ → 88.
 *
 * `kademeBul(skor)` yaşamaya devam ediyor: Modül C'nin akran grubu
 * metodolojide S kademesiyle tanımlı.
 *
 * Kanonik tanım `skor.ONEMLI_ORAN` / `skor.MEGA_ORAN` /
 * `skor.buyukluk_kademesi`; `scripts/skor_yenile.py` değişiklik
 * raporunu onunla veriyor.
 */
export const ONEMLI_ORAN = 0.05;
export const MEGA_ORAN = 0.15;

export function buyuklukBul(oran: number | null): Kademe | null {
  if (oran === null) return null;
  if (oran >= MEGA_ORAN) return "mega";
  if (oran >= ONEMLI_ORAN) return "onemli";
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
 * yazıp "mega" rengiyle çiziliyordu. Aynı ders kademe ciro oranına
 * geçince de geçerli: renk ile etiket tek fonksiyondan (`oranRengi`).
 */
export function kademeRengi(k: Kademe | null): string {
  if (k === "mega") return "var(--mavi-koyu)";
  if (k === "onemli") return "var(--mavi)";
  if (k === "rutin") return "var(--mut-2)";
  return "var(--ken)";
}

/** Görünen renk ciro oranının kademesinden — etiketle aynı kaynak. */
export function oranRengi(oran: number | null): string {
  return kademeRengi(buyuklukBul(oran));
}

/* ---------------------------------------------- bildirim yorgunluğu */

export type SiklikBayragi = "seyrek" | "orta" | "sik";

/**
 * Eşikler `skor.SIKLIK_ORTA_ESIGI` / `skor.SIKLIK_SIK_ESIGI` ile aynı.
 * Arşiv penceresindeki bildirim sayısının üçlük kesimlerinden geliyor:
 * 613 bildirimi %33,9 / %33,1 / %33,0 diye bölüyor.
 */
export const SIKLIK_ORTA_ESIGI = 8;
export const SIKLIK_SIK_ESIGI = 18;

/**
 * Şirketin bildirim sıklığı — **skora girmez**. Adım 16'nın en sağlam
 * bulgusuydu — örneklem dışı yılda TEKRARLANMADI (t = −0,74), yalnız
 * olgu olarak gösteriliyor. İlk ölçüm: ln(sıklık) −0,111, t = −2,48
 * (p = 0,013). Skora katılmamasının sebebi tahta bayrağıyla aynı: bu
 * şirketin özelliği, bildirimin değil.
 */
export function siklikBayragi(adet: number | null): SiklikBayragi | null {
  if (adet === null) return null;
  if (adet >= SIKLIK_SIK_ESIGI) return "sik";
  if (adet >= SIKLIK_ORTA_ESIGI) return "orta";
  return "seyrek";
}

export function siklikRenk(bayrak: SiklikBayragi): string {
  if (bayrak === "seyrek") return "yes";
  if (bayrak === "orta") return "kehribar";
  return "kir";
}

export function tahtaRenk(tahta: string): string {
  if (tahta === "temiz") return "yes";
  if (tahta === "hareketli") return "kehribar";
  return "kir";
}
