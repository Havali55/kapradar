// Hisse sayfasının hikâyesi ve /hisse dizini: tez cümlesinin sayıları,
// kayan 12 ay serisi, grafik başlığı, iş listesi, "kiminle" ve dizin
// satırları. Saf ve içe aktarmasız; `node --test` doğrudan koşar.
//
// "Sayılan iş" (oranı var, `ayni_is` değil) kuralı `anasayfa.sayilanIs`'te.
// Bu modül içe aktaramadığı için süzmeyi çağıran yapar: `sonOnIkiAy`,
// `gunlukSeri` ve `kiminle` sayılan işleri bekler; `dizinSatirlari`
// kuralı parametre olarak alır.

export const GUN_MS = 86_400_000;
const YIL_MS = 365 * GUN_MS;

export type CiroBasamagi = {
  gecerlilik_basi: string;
  hasilat: number | null;
  para_birimi: string | null;
  /** Basamağın 12 ayının bittiği gün (`ciro_seri.donem_sonu`). */
  donem_sonu?: string | null;
};

/** (simdi − 365 gün, simdi] içindekiler. */
export function sonOnIkiAy<T extends { yayin_zamani: string }>(
  isler: readonly T[],
  simdi: number,
): T[] {
  return isler.filter((i) => {
    const z = Date.parse(i.yayin_zamani);
    return z <= simdi && z > simdi - YIL_MS;
  });
}

/**
 * `t` anında bilinen son 12 aylık ciro: o ana kadar yürürlüğe girmiş en
 * yeni basamak. Boşluk basamağı (hasılat yok) ya da TL dışı → null;
 * önceki değer taşınmaz.
 */
export function ciroAn(basamaklar: readonly CiroBasamagi[], t: number): number | null {
  const b = ciroBasamagi(basamaklar, t);
  return b !== null && b.hasilat !== null && b.para_birimi === "TL" ? b.hasilat : null;
}

/** `t` anında yürürlükteki basamak: o ana kadar yayınlanmış en yeni rapor. */
export function ciroBasamagi<B extends CiroBasamagi>(basamaklar: readonly B[], t: number): B | null {
  let enYeni = -Infinity;
  let secilen: B | null = null;
  for (const b of basamaklar) {
    const z = Date.parse(b.gecerlilik_basi);
    if (z <= t && z > enYeni) {
      enYeni = z;
      secilen = b;
    }
  }
  return secilen;
}

const KISA_AY = new Intl.DateTimeFormat("tr-TR", { month: "short", timeZone: "UTC" });

/**
 * Dönem sonunda biten 12 ay, okura: "2026-06-30" → "Tem 2025 – Haz 2026".
 * Kesikli çizginin gerçekleşmiş satış olduğunu, tahmin olmadığını söylemek
 * için.
 */
export function onIkiAyAraligi(donemSonu: string): string {
  const son = new Date(`${donemSonu.slice(0, 10)}T00:00:00Z`);
  const bas = new Date(Date.UTC(son.getUTCFullYear(), son.getUTCMonth() - 11, 1));
  const ay = (d: Date) => `${KISA_AY.format(d)} ${d.getUTCFullYear()}`;
  return `${ay(bas)} – ${ay(son)}`;
}

/**
 * Grafikteki kısa dönem etiketi: "2026-06-30" → "6A26" (altı aylık),
 * yıllık rapor "12A25". Ciro çizgisinin sıçradığı yerde hangi raporun
 * geldiğini söyler.
 */
export function donemEtiketi(donemSonu: string): string {
  return `${Number(donemSonu.slice(5, 7))}A${donemSonu.slice(2, 4)}`;
}

export type SeriNoktasi = { t: number; duyurulan: number; ciro: number | null };

/**
 * Cironun yeni bir değere geçtiği günlerin sırası: bir raporun
 * yayınlandığı gün. İlk gün sıçrama sayılmaz (grafik o seviyeden
 * başlıyor); boşluğa (ciro yok) geçiş de sayılmaz.
 */
export function ciroSicramalari(seri: readonly SeriNoktasi[]): number[] {
  const sonuc: number[] = [];
  for (let i = 1; i < seri.length; i++) {
    const c = seri[i].ciro;
    if (c !== null && c !== seri[i - 1].ciro) sonuc.push(i);
  }
  return sonuc;
}

/**
 * Son `gun` günün her günü, bugün dahil: o güne kadarki 12 ayda duyurulan
 * TL toplamı ve o gün bilinen ciro. Son nokta tez cümlesiyle aynı hesap.
 */
export function gunlukSeri(
  isler: readonly { yayin_zamani: string; net_tutar_tl: number | null }[],
  basamaklar: readonly CiroBasamagi[],
  simdi: number,
  gun = 365,
): SeriNoktasi[] {
  const zaman = isler.map((i) => ({ z: Date.parse(i.yayin_zamani), tl: i.net_tutar_tl ?? 0 }));
  const seri: SeriNoktasi[] = [];
  for (let k = gun; k >= 0; k--) {
    const t = simdi - k * GUN_MS;
    let toplam = 0;
    for (const { z, tl } of zaman) if (z <= t && z > t - YIL_MS) toplam += tl;
    seri.push({ t, duyurulan: toplam, ciro: ciroAn(basamaklar, t) });
  }
  return seri;
}

/**
 * `i`. günde 12 aylık pencereye giren ve pencereden çıkan işler: grafiğin
 * neden yükselip indiğini ipucunda söylemek için. Pencere `gunlukSeri` ile
 * aynı, (t − 365 gün, t]: önceki günden bu yana duyurulan girer, tam 12 ay
 * önceki gün aralığında duyurulan çıkar.
 */
export function gunDegisimi<T extends { t: number }>(
  seri: readonly SeriNoktasi[],
  i: number,
  isler: readonly T[],
): { giren: T[]; cikan: T[] } {
  if (i <= 0) return { giren: [], cikan: [] };
  const a = seri[i - 1].t;
  const b = seri[i].t;
  return {
    giren: isler.filter((x) => x.t > a && x.t <= b),
    cikan: isler.filter((x) => x.t > a - YIL_MS && x.t <= b - YIL_MS),
  };
}

/**
 * Serinin 12 ayı dolup hesaptan çıkan işleri, çıktıkları günün sırasıyla:
 * mavi çizginin her inişinin sebebi. Aynı gün birden çok iş çıkabilir.
 */
export function cikisNoktalari<T extends { t: number }>(
  seri: readonly SeriNoktasi[],
  isler: readonly T[],
): { i: number; cikan: T[] }[] {
  const sonuc: { i: number; cikan: T[] }[] = [];
  for (let i = 1; i < seri.length; i++) {
    const { cikan } = gunDegisimi(seri, i, isler);
    if (cikan.length) sonuc.push({ i, cikan });
  }
  return sonuc;
}

export type SeriIliskisi = "ustte" | "altta" | "karisik" | "ciro-yok";

/**
 * Grafik başlığının dayanağı. "Her gününde" iddiası ancak her gün ciro
 * biliniyorsa kurulur; bir gün bile boşsa karışık sayılır.
 */
export function seriIliskisi(seri: readonly SeriNoktasi[]): SeriIliskisi {
  if (seri.every((n) => n.ciro === null)) return "ciro-yok";
  if (seri.some((n) => n.ciro === null)) return "karisik";
  if (seri.every((n) => n.duyurulan > (n.ciro as number))) return "ustte";
  if (seri.every((n) => n.duyurulan < (n.ciro as number))) return "altta";
  return "karisik";
}

/** Eksen adımı: yaklaşık `hedef` aralık, 1 · 2 · 5 × 10^k. */
export function guzelAdim(maks: number, hedef = 4): number {
  if (maks <= 0) return 1;
  const kaba = maks / hedef;
  const us = 10 ** Math.floor(Math.log10(kaba));
  const oran = kaba / us;
  return (oran <= 1 ? 1 : oran <= 2 ? 2 : oran <= 5 ? 5 : 10) * us;
}

export function birimSec(maks: number): { bolen: number; ad: string; kisa: string } {
  return maks >= 1e9
    ? { bolen: 1e9, ad: "milyar TL", kisa: "Mr" }
    : { bolen: 1e6, ad: "milyon TL", kisa: "Mn" };
}

const DEVLET_ON_EKI = /^(Türkiye Cumhuriyeti|T\.\s?C\.)\s+Cumhurbaşkanlığı\s+/u;

/** Listede gösterilen karşı taraf: devlet ön eki kısalır, gerisi olduğu gibi. */
export function karsiGorunen(ad: string): string {
  return ad.replace(DEVLET_ON_EKI, "").trim();
}

const KISALTMA: [RegExp, string][] = [[/Savunma Sanayii Başkanlığı/u, "SSB"]];

/** Grafik etiketi için tek sözcük: bilinen kısaltma, parantez içi, ilk sözcük. */
export function kisaAd(ad: string | null): string | null {
  if (!ad) return null;
  for (const [desen, kisa] of KISALTMA) if (desen.test(ad)) return kisa;
  const parantez = ad.match(/\(([A-ZÇĞİÖŞÜ]{2,8})\)/u);
  if (parantez) return parantez[1];
  return ad.trim().split(/[\s-]+/u)[0];
}

export type KiminleSatiri = { ad: string | null; tl: number; adet: number };

/** Karşı taraf başına TL; adı verilenler büyükten küçüğe, adsızlar tek satırda sonda. */
export function kiminle(
  isler: readonly { net_tutar_tl: number | null; karsi: string | null }[],
): KiminleSatiri[] {
  const m = new Map<string | null, KiminleSatiri>();
  for (const i of isler) {
    const e = m.get(i.karsi) ?? { ad: i.karsi, tl: 0, adet: 0 };
    e.tl += i.net_tutar_tl ?? 0;
    e.adet += 1;
    m.set(i.karsi, e);
  }
  return [...m.values()].sort(
    (a, b) => Number(a.ad === null) - Number(b.ad === null) || b.tl - a.tl,
  );
}

/** Satırda gösterilecek kalemler: toplam sözleşme bedeli skora girmiyor. */
export function gosterilenKalemler<T extends { tip: string }>(tutarlar: readonly T[] | null): T[] {
  return (tutarlar ?? []).filter((t) => t.tip !== "toplam_sozlesme");
}

export type Suzgec = "tum" | "onemli" | "acik";

export function isleriSuz<T extends { oran: number | null; tekrar: boolean; karsi: string | null }>(
  isler: readonly T[],
  suzgec: Suzgec,
  onemliEsik: number,
): T[] {
  if (suzgec === "onemli") {
    return isler.filter((i) => i.oran !== null && i.oran >= onemliEsik && !i.tekrar);
  }
  if (suzgec === "acik") return isler.filter((i) => i.karsi !== null);
  return [...isler];
}

const AY_YIL = new Intl.DateTimeFormat("tr-TR", {
  timeZone: "Europe/Istanbul",
  month: "long",
  year: "numeric",
});

/**
 * Görünen satırları aylara böler (İstanbul takvimi, girdi sırasıyla). Ay
 * başlığındaki sayı `tumu`'ndan: "Daha eski" düğmesine basılmadan da ayın
 * gerçek iş sayısı görünür.
 */
export function aylaraBol<T extends { zaman: string }>(
  tumu: readonly T[],
  gorunen: readonly T[],
): { ay: string; adet: number; isler: T[] }[] {
  const say = new Map<string, number>();
  for (const i of tumu) {
    const a = AY_YIL.format(new Date(i.zaman));
    say.set(a, (say.get(a) ?? 0) + 1);
  }
  const gruplar: { ay: string; adet: number; isler: T[] }[] = [];
  for (const i of gorunen) {
    const a = AY_YIL.format(new Date(i.zaman));
    const son = gruplar.at(-1);
    if (son?.ay === a) son.isler.push(i);
    else gruplar.push({ ay: a, adet: say.get(a) ?? 0, isler: [i] });
  }
  return gruplar;
}

/** Tablo alternatifi: son noktadan geriye her `aralik` günde bir, eskiden yeniye. */
export function tabloSatirlari<T>(seri: readonly T[], aralik = 30): T[] {
  return seri.filter((_, i) => (seri.length - 1 - i) % aralik === 0);
}

// ------------------------------------------------ son 20 seansın hareketi

/** `hisse_limit_gunleri` görünümünün satırı (son 20 seans, günlük kapanış). */
export type LimitGunleri = {
  son_tarih: string;
  seans: number;
  taban_gun: number;
  tavan_gun: number;
  son_taban_serisi: number;
  son_tavan_serisi: number;
  /** Ortalama |günlük getiri|; sermaye işlemi günleri hariç. */
  ort_hareket: number | null;
  /** %10,5'i aşan, normal işlemle oluşamayan gün (bedelsiz, veri hatası). */
  gecersiz_gun: number;
};

export type SeansRengi = "yes" | "notr" | "kehribar" | "kir";

/**
 * Ortalama hareketin, listedeki hisselerin ortasına oranına göre kademe.
 * Göreli: piyasanın tamamı sarsıldığında da hangi tahtanın ayrıştığını
 * söylesin diye. Eylül 2026'da 144 hissenin dağılımıyla (orta %2,9)
 * yaklaşık dörtte biri sakin, sekizde biri çok oynak düşüyor.
 */
export const HAREKET_KADEMELERI: readonly { ust: number; ad: string; renk: SeansRengi }[] = [
  { ust: 0.75, ad: "Sakin", renk: "yes" },
  { ust: 4 / 3, ad: "Olağan", renk: "notr" },
  { ust: 2, ad: "Oynak", renk: "kehribar" },
  { ust: Infinity, ad: "Çok oynak", renk: "kir" },
];

/** Listedeki hisselerin ortalama hareketlerinin ortancası. */
export function hareketMedyani(satirlar: readonly { ort_hareket: number | null }[]): number | null {
  const d = satirlar
    .map((s) => s.ort_hareket)
    .filter((v): v is number => v !== null && Number.isFinite(v))
    .sort((a, b) => a - b);
  if (d.length === 0) return null;
  const m = Math.floor(d.length / 2);
  return d.length % 2 ? d[m] : (d[m - 1] + d[m]) / 2;
}

const ondalik = (v: number) => v.toFixed(1).replace(".", ",");

/**
 * Son 20 seans, okura. Tahta etiketi bildirim gününün devre kesici
 * ölçüsü; tabanda kilitli, işlem görmeyen hisse devre kesiciyi
 * tetiklemiyor (TEHOL, Eylül 2026). Süren taban/tavan serisi (en az iki
 * seans) önce söylenir; yoksa ortalama hareketin kademesi. `kisa` dizin
 * hücresi için, `aciklama` ipucu ve hisse sayfası için.
 */
export function seansDurumu(
  l: LimitGunleri | null,
  medyan: number | null,
): {
  kisa: string;
  metin: string;
  aciklama: string;
  renk: SeansRengi;
  hareket: number | null;
} | null {
  if (!l) return null;
  const oran = l.ort_hareket !== null && medyan ? l.ort_hareket / medyan : null;
  const kademe = oran === null ? null : HAREKET_KADEMELERI.find((k) => oran < k.ust)!;
  const limitler = [
    l.taban_gun > 0 ? `${l.taban_gun} taban` : null,
    l.tavan_gun > 0 ? `${l.tavan_gun} tavan` : null,
  ].filter(Boolean);
  const cumleler = [
    l.ort_hareket !== null
      ? `Günde ortalama %${ondalik(l.ort_hareket * 100)} hareket` +
        (oran !== null && medyan
          ? `; listedeki hisselerin ortası %${ondalik(medyan * 100)}, bu onun ${ondalik(oran)} katı`
          : "")
      : null,
    `Son ${l.seans} seansta ${limitler.length ? `${limitler.join(", ")} günü` : "taban ya da tavan yok"}`,
    l.gecersiz_gun > 0
      ? `${l.gecersiz_gun} gün, fiyat marjını aşan bir sıçrama (bedelsiz ya da veri hatası) olduğu için sayılmadı`
      : null,
  ].filter(Boolean);
  const aciklama = cumleler.join(". ") + ".";

  if (l.son_taban_serisi >= 2) {
    const kisa = `${l.son_taban_serisi} seanstır tabanda`;
    return { kisa, metin: `Son ${kisa}`, aciklama, renk: "kir", hareket: l.ort_hareket };
  }
  if (l.son_tavan_serisi >= 2) {
    const kisa = `${l.son_tavan_serisi} seanstır tavanda`;
    return { kisa, metin: `Son ${kisa}`, aciklama, renk: "kehribar", hareket: l.ort_hareket };
  }
  if (!kademe) return null;
  return { kisa: kademe.ad, metin: kademe.ad, aciklama, renk: kademe.renk, hareket: l.ort_hareket };
}

// -------------------------------------------------------------- dizin

export type DizinSatiri = {
  ticker: string;
  sirket: string;
  adet12: number;
  /** Arşivdeki en yeni bildirim (sayılan olmasa da). */
  sonIs: string;
  /** Son 12 ayda duyurulan TL ÷ bugünkü son 12 aylık ciro. */
  kat: number | null;
  /** Son dönemin reel büyümesi; rapor nominalse null. */
  buyume: number | null;
  buyumeDonemi: string | null;
  nominal: boolean;
};

type DizinGirdi = {
  ticker: string;
  sirket: string;
  yayin_zamani: string;
  net_tutar_tl: number | null;
};

type DizinBuyumesi = {
  ticker: string;
  donem_sonu: string;
  ay_sayisi: number;
  buyume: number | null;
  reel: boolean;
};

/**
 * Şirket başına dizin satırı. `satirlar` yeniden eskiye sıralı olmalı
 * (ilk görülen en yeni). Son dönem: en yeni dönem sonu, onun en uzun
 * kümülatif raporu.
 */
export function dizinSatirlari<T extends DizinGirdi>(
  satirlar: readonly T[],
  seri: readonly (CiroBasamagi & { ticker: string })[],
  buyumeler: readonly DizinBuyumesi[],
  simdi: number,
  sayilanMi: (s: T) => boolean,
): DizinSatiri[] {
  const gruplar = new Map<string, T[]>();
  for (const s of satirlar) {
    const g = gruplar.get(s.ticker) ?? [];
    g.push(s);
    gruplar.set(s.ticker, g);
  }
  return [...gruplar].map(([ticker, g]) => {
    const son12 = sonOnIkiAy(g.filter(sayilanMi), simdi);
    const tl = son12.reduce((t, s) => t + (s.net_tutar_tl ?? 0), 0);
    const ciro = ciroAn(
      seri.filter((b) => b.ticker === ticker),
      simdi,
    );
    let enSon: DizinBuyumesi | null = null;
    for (const b of buyumeler) {
      if (b.ticker !== ticker || b.buyume === null) continue;
      if (
        !enSon ||
        b.donem_sonu > enSon.donem_sonu ||
        (b.donem_sonu === enSon.donem_sonu && b.ay_sayisi > enSon.ay_sayisi)
      ) {
        enSon = b;
      }
    }
    return {
      ticker,
      sirket: g[0].sirket,
      adet12: son12.length,
      sonIs: g[0].yayin_zamani,
      kat: ciro ? tl / ciro : null,
      buyume: enSon && enSon.reel ? enSon.buyume : null,
      buyumeDonemi: enSon ? enSon.donem_sonu : null,
      nominal: enSon !== null && !enSon.reel,
    };
  });
}

export type DizinAnahtari = "ticker" | "adet12" | "sonIs" | "kat" | "buyume" | "hareket";

type Siralanabilir = Pick<DizinSatiri, "ticker" | "adet12" | "sonIs" | "kat" | "buyume"> & {
  /** Son 20 seansın ortalama hareketi; dizin sayfası ekler. */
  hareket?: number | null;
};

/** Boş değerler her iki yönde sonda; eşitlikte ticker. */
export function dizinSirala<T extends Siralanabilir>(
  satirlar: readonly T[],
  anahtar: DizinAnahtari,
  azalan: boolean,
): T[] {
  const deger = (s: T): number | string | null =>
    anahtar === "sonIs"
      ? Date.parse(s.sonIs)
      : anahtar === "hareket"
        ? (s.hareket ?? null)
        : s[anahtar];
  const tk = (a: T, b: T) => (a.ticker < b.ticker ? -1 : a.ticker > b.ticker ? 1 : 0);
  return [...satirlar].sort((a, b) => {
    const x = deger(a);
    const y = deger(b);
    if (x === null || y === null) return x === y ? tk(a, b) : x === null ? 1 : -1;
    const fark = typeof x === "string" ? (x < y ? -1 : x > y ? 1 : 0) : x - (y as number);
    return (azalan ? -fark : fark) || tk(a, b);
  });
}
