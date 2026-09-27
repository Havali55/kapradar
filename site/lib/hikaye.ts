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
  let enYeni = -Infinity;
  let deger: number | null = null;
  for (const b of basamaklar) {
    const z = Date.parse(b.gecerlilik_basi);
    if (z <= t && z > enYeni) {
      enYeni = z;
      deger = b.hasilat !== null && b.para_birimi === "TL" ? b.hasilat : null;
    }
  }
  return deger;
}

export type SeriNoktasi = { t: number; duyurulan: number; ciro: number | null };

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

export type DizinAnahtari = "ticker" | "adet12" | "sonIs" | "kat" | "buyume";

type Siralanabilir = Pick<DizinSatiri, "ticker" | "adet12" | "sonIs" | "kat" | "buyume">;

/** Boş değerler her iki yönde sonda; eşitlikte ticker. */
export function dizinSirala<T extends Siralanabilir>(
  satirlar: readonly T[],
  anahtar: DizinAnahtari,
  azalan: boolean,
): T[] {
  const deger = (s: T): number | string | null =>
    anahtar === "sonIs" ? Date.parse(s.sonIs) : s[anahtar];
  const tk = (a: T, b: T) => (a.ticker < b.ticker ? -1 : a.ticker > b.ticker ? 1 : 0);
  return [...satirlar].sort((a, b) => {
    const x = deger(a);
    const y = deger(b);
    if (x === null || y === null) return x === y ? tk(a, b) : x === null ? 1 : -1;
    const fark = typeof x === "string" ? (x < y ? -1 : x > y ? 1 : 0) : x - (y as number);
    return (azalan ? -fark : fark) || tk(a, b);
  });
}
