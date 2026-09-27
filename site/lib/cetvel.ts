// Grafik yerleşimi: arı kovanı dizilimi ve çakışmasız etiket. Saf
// geometri; veri, ölçek ve içe aktarma yok, `node --test` doğrudan koşar.

/**
 * Arı kovanı: her nokta değer ekseninde kendi konumunda kalır, çarpışırsa
 * dik eksende 0, −1, +1, −2, +2… adım kayar. Küçük konum önce yerleşir.
 *
 * `sinir` (dar sütun) aşılırsa nokta düşürülmez: sınır içindeki en az
 * çakışan adaya konur. Grafikteki nokta sayısı başlıktaki sayıyla
 * tutmalı; maket yer bulamayan noktayı sessizce atıyordu.
 *
 * Dönen dizi girdi sırasında, dik eksendeki kaymalar.
 */
export function kovanYerlesimi(
  konumlar: readonly number[],
  yaricap: number,
  bosluk = 3,
  sinir = Infinity,
): number[] {
  const adim = 2 * yaricap + bosluk;
  const enAz = 2 * yaricap + bosluk / 2;
  const sira = konumlar.map((_, i) => i).sort((a, b) => konumlar[a] - konumlar[b]);
  const kayma = new Array<number>(konumlar.length).fill(0);
  const yerlesen: { k: number; d: number }[] = [];
  for (const i of sira) {
    const k = konumlar[i];
    let enIyi = { d: 0, mesafe: -1 };
    for (let kat = 0; ; kat++) {
      const d = kat === 0 ? 0 : Math.ceil(kat / 2) * adim * (kat % 2 ? -1 : 1);
      if (Math.abs(d) > sinir) break;
      let mesafe = Infinity;
      for (const p of yerlesen) mesafe = Math.min(mesafe, Math.hypot(p.k - k, p.d - d));
      if (mesafe >= enAz) {
        enIyi = { d, mesafe };
        break;
      }
      if (mesafe > enIyi.mesafe) enIyi = { d, mesafe };
    }
    kayma[i] = enIyi.d;
    yerlesen.push({ k, d: enIyi.d });
  }
  return kayma;
}

/**
 * Eksen etiketlerinden birbirine binmeyenleri seçer. İki uç her zaman
 * kalır (ölçeğin tabanı ve tavanı); aradakiler soldan sağa, yerleşmiş
 * hiçbir etikete `bosluk`tan yakın değilse. Telefonda %50 ile %100
 * üst üste biniyordu. Dönen: kalan indeksler, sıralı.
 */
export function seyrekEtiketler(
  kutular: readonly { x1: number; x2: number }[],
  bosluk = 4,
): number[] {
  const n = kutular.length;
  if (n <= 2) return kutular.map((_, i) => i);
  const kalan = [0, n - 1];
  for (let i = 1; i < n - 1; i++) {
    const k = kutular[i];
    const bos = kalan.every(
      (j) => k.x2 + bosluk <= kutular[j].x1 || kutular[j].x2 + bosluk <= k.x1,
    );
    if (bos) kalan.push(i);
  }
  return kalan.sort((a, b) => a - b);
}

export type Nokta = { x: number; y: number; r: number };
type Kutu = { x1: number; x2: number; y1: number; y2: number };

const cakisir = (a: Kutu, b: Kutu) =>
  a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;

// 11 px JetBrains Mono'nun taban çizgisine göre gerçek sınırları (tarayıcıda
// ölçüldü): 11 px yukarı, 3 px aşağı. İlk sürüm kutuyu −10/+2 sanıyordu,
// alta konan etiket kendi noktasına 2 px biniyordu.
const YAZI_UST = 11;
const YAZI_ALT = 3;
/** Etiketle nokta arasındaki boşluk. */
const ARALIK = 2;

/**
 * Etiketleri istek sırasıyla (önemliden önemsize) noktanın üstüne ya da
 * altına koyar: üst, alt, bir kat daha üst, bir kat daha alt. Başka bir
 * noktaya, yerleşmiş etikete ya da alanın dışına taşan aday atlanır.
 * Dört aday da düşerse etiket konmaz (ipucu hâlâ var). Yatayda etiket
 * alanın içine kaydırılır.
 *
 * Noktanın `r`'si çizilen kenarı da içermeli (kenar kalınlığının yarısı).
 *
 * Dönen: nokta indeksi → etiketin taban çizgisi (ortası x, taban y).
 */
export function etiketYerlestir(
  noktalar: readonly Nokta[],
  istekler: readonly { i: number; genislik: number }[],
  alan: { w: number; h: number },
): Map<number, { x: number; y: number }> {
  const kutular: Kutu[] = [];
  const sonuc = new Map<number, { x: number; y: number }>();
  for (const { i, genislik: w } of istekler) {
    const p = noktalar[i];
    const x = Math.min(Math.max(p.x, w / 2), alan.w - w / 2);
    for (const kat of [-1, 1, -2, 2]) {
      const uzak = (Math.abs(kat) - 1) * (YAZI_UST + YAZI_ALT + ARALIK);
      const taban =
        kat < 0
          ? p.y - p.r - ARALIK - YAZI_ALT - uzak
          : p.y + p.r + ARALIK + YAZI_UST + uzak;
      const kt = { x1: x - w / 2, x2: x + w / 2, y1: taban - YAZI_UST, y2: taban + YAZI_ALT };
      if (kt.y1 < 0 || kt.y2 > alan.h) continue;
      const noktaya = noktalar.some(
        (q, j) =>
          j !== i && cakisir(kt, { x1: q.x - q.r, x2: q.x + q.r, y1: q.y - q.r, y2: q.y + q.r }),
      );
      if (noktaya || kutular.some((k) => cakisir(k, kt))) continue;
      kutular.push(kt);
      sonuc.set(i, { x, y: taban });
      break;
    }
  }
  return sonuc;
}
