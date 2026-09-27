// Söz ve gerçek: duyuru yoğunluğu ile gerçekleşen reel büyüme.
//
// `src/kap_radar/soz_gercek.py`'nin birebir karşılığı. İki uygulama tek
// fikstürle sınanıyor (`tests/fixtures/soz_gercek.json`); biri değişip
// öteki unutulursa testlerden biri kırılır. `sozSatirlariKur`,
// `scripts/analiz_soz_gercek.py`'nin D varyantı (TL ÷ FY ciro, yalnız
// reel). Tanım: tasarım §5.2. Saf ve içe aktarmasız: `node --test`
// doğrudan koşar.

/** Raporlama sezonu: kapsam önceki çeyreğin bu oranına ulaşmadıysa dönem erken. */
export const KAPSAM_ORANI = 0.9;

/** "Belirgin önde": üst grup medyanı diğer ikisinin büyüğünü 10 puandan fazla aşmalı. */
export const ONDE_ESIGI = 0.1;

export const GRUP_ADLARI = ["Az duyuran", "Orta", "Çok duyuran"] as const;

const CEYREK_SONU: Record<number, number> = { 3: 31, 6: 30, 9: 30, 12: 31 };

export type SozSatiri = {
  ticker: string;
  /** Söz yılında duyurulan TL toplamı / o yılın cirosu. */
  yogunluk: number;
  /** Büyüme dönemindeki reel ciro büyümesi (0,20 = %20). */
  buyume: number;
};

export type Grup<T extends SozSatiri = SozSatiri> = {
  ad: string;
  satirlar: T[];
  medyanBuyume: number;
  medyanYogunluk: number;
};

export type SozOzeti<T extends SozSatiri = SozSatiri> = {
  n: number;
  gruplar: [Grup<T>, Grup<T>, Grup<T>];
  rho: number;
  t: number;
  ustGrupOnde: boolean;
};

const iki = (n: number) => String(n).padStart(2, "0");

/** Bir çeyrek sonundan önceki çeyrek sonu ("2026-03-31" → "2025-12-31"). */
export function oncekiCeyrek(iso: string): string {
  let yil = Number(iso.slice(0, 4));
  let ay = Number(iso.slice(5, 7)) - 3;
  if (ay <= 0) {
    ay += 12;
    yil -= 1;
  }
  return `${yil}-${iki(ay)}-${iki(CEYREK_SONU[ay])}`;
}

function ceyrekSonuMu(iso: string): boolean {
  return CEYREK_SONU[Number(iso.slice(5, 7))] === Number(iso.slice(8, 10));
}

/**
 * Kapsamı bir önceki çeyreğinkinin en az %90'ı olan en yeni çeyrek sonu.
 * `kapsam`: dönem sonu → o dönem için büyümesi olan şirket sayısı.
 * Çeyrek sonu olmayan dönemler (özel hesap yılı) aday değil.
 */
export function buyumeDonemiSec(kapsam: ReadonlyMap<string, number>): string | null {
  const ceyrekler = [...kapsam.keys()].filter(ceyrekSonuMu).sort().reverse();
  for (const d of ceyrekler) {
    if ((kapsam.get(d) ?? 0) >= KAPSAM_ORANI * (kapsam.get(oncekiCeyrek(d)) ?? 0)) {
      return d;
    }
  }
  return null;
}

function medyan(degerler: number[]): number {
  const s = [...degerler].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** 1'den başlayan sıralar; eşit değerler sıralarının ortalamasını alır. */
function siralar(degerler: readonly number[]): number[] {
  const sira = degerler.map((_, i) => i).sort((a, b) => degerler[a] - degerler[b]);
  const sonuc = new Array<number>(degerler.length);
  for (let i = 0; i < sira.length; ) {
    let j = i;
    while (j + 1 < sira.length && degerler[sira[j + 1]] === degerler[sira[i]]) j++;
    for (let m = i; m <= j; m++) sonuc[sira[m]] = (i + j) / 2 + 1;
    i = j + 1;
  }
  return sonuc;
}

/** Sıralar üzerinden Pearson korelasyonu (eşitlikte ortalama sıra). */
export function spearman(x: readonly number[], y: readonly number[]): number {
  const rx = siralar(x);
  const ry = siralar(y);
  const n = rx.length;
  const ox = rx.reduce((a, b) => a + b, 0) / n;
  const oy = ry.reduce((a, b) => a + b, 0) / n;
  let pay = 0;
  let sx = 0;
  let sy = 0;
  for (let i = 0; i < n; i++) {
    pay += (rx[i] - ox) * (ry[i] - oy);
    sx += (rx[i] - ox) ** 2;
    sy += (ry[i] - oy) ** 2;
  }
  return pay / Math.sqrt(sx * sy);
}

/** H0: ρ = 0 için yaklaşık t, n − 2 serbestlik derecesi. */
export function tIstatistigi(rho: number, n: number): number {
  if (rho * rho >= 1) return rho > 0 ? Infinity : -Infinity;
  return rho * Math.sqrt((n - 2) / (1 - rho * rho));
}

// İki yönlü %5 kritik t değerleri (serbestlik derecesi, değer). Ara
// değerde bir alttaki satır kullanılır: eşik yukarı yuvarlanır, "anlamlı"
// demek zorlaşır.
const T_KRITIK: [number, number][] = [
  [1, 12.706], [2, 4.303], [3, 3.182], [4, 2.776], [5, 2.571],
  [6, 2.447], [7, 2.365], [8, 2.306], [9, 2.262], [10, 2.228],
  [15, 2.131], [20, 2.086], [25, 2.06], [30, 2.042], [40, 2.021],
  [60, 2.0], [120, 1.98],
];

export function anlamliMi(t: number, n: number): boolean {
  const sd = n - 2;
  if (sd < 1) return false;
  let kritik = T_KRITIK[0][1];
  for (const [d, v] of T_KRITIK) if (d <= sd) kritik = v;
  return Math.abs(t) >= kritik;
}

/**
 * Üç eşit grup, grup medyanları ve Spearman sıra korelasyonu. Sıralama
 * yoğunluğa göre, eşitlikte ticker'a göre (kod noktası sırası, Python'la
 * aynı). n üçe bölünmüyorsa artan satırlar son gruba gider.
 */
export function ozetle<T extends SozSatiri>(satirlar: readonly T[]): SozOzeti<T> | null {
  if (satirlar.length < 3) return null;
  const sirali = [...satirlar].sort(
    (a, b) =>
      a.yogunluk - b.yogunluk || (a.ticker < b.ticker ? -1 : a.ticker > b.ticker ? 1 : 0),
  );
  const n = sirali.length;
  const k = Math.floor(n / 3);
  const dilimler = [sirali.slice(0, k), sirali.slice(k, 2 * k), sirali.slice(2 * k)];
  const gruplar = dilimler.map((d, i) => ({
    ad: GRUP_ADLARI[i],
    satirlar: d,
    medyanBuyume: medyan(d.map((s) => s.buyume)),
    medyanYogunluk: medyan(d.map((s) => s.yogunluk)),
  })) as SozOzeti<T>["gruplar"];
  const rho = spearman(
    sirali.map((s) => s.yogunluk),
    sirali.map((s) => s.buyume),
  );
  const altEnIyi = Math.max(gruplar[0].medyanBuyume, gruplar[1].medyanBuyume);
  return {
    n,
    gruplar,
    rho,
    t: tIstatistigi(rho, n),
    ustGrupOnde: gruplar[2].medyanBuyume - altEnIyi > ONDE_ESIGI,
  };
}

export type OkumaTuru = "onde-anlamli" | "onde" | "ayrismiyor";

/** Dürüst okuma cümlesinin kalıbı: sonuç değişirse cümle de değişir. */
export function okumaTuru(o: SozOzeti): OkumaTuru {
  if (!o.ustGrupOnde) return "ayrismiyor";
  return anlamliMi(o.t, o.n) ? "onde-anlamli" : "onde";
}

const DONEM_ADI: Record<string, string> = {
  "03": "ilk çeyrek",
  "06": "ilk yarı",
  "09": "ilk dokuz ay",
  "12": "yılı",
};

/** "2026-06-30" → "2026 ilk yarı". Büyüme en uzun kümülatif dönemden. */
export function donemAdi(iso: string): string {
  return `${iso.slice(0, 4)} ${DONEM_ADI[iso.slice(5, 7)]}`;
}

// ---------------------------------------------------- satır kurma

/** `akis` satırının gereken kısmı. */
export type DuyuruGirdi = {
  ticker: string;
  yayin_zamani: string;
  net_tutar_tl: number | null;
  ciro_orani: number | null;
  onceki_tur?: string | null;
};

/** `reel_buyume` görünümünün satırı. */
export type BuyumeGirdi = {
  ticker: string;
  donem_sonu: string;
  ay_sayisi: number;
  hasilat: number;
  para_birimi: string | null;
  buyume: number | null;
  reel: boolean;
  /** Dönemin son yayınının KAP bildirim numarası (kaynak rapor bağlantısı). */
  kap_index?: number | null;
};

/** Bir şirketin söz yılındaki sözü ve büyüme dönemindeki gerçeği (hisse kartı). */
export type SirketSozu = {
  adet: number;
  tl: number;
  /** Söz yılının FY cirosu (TL); rapor yoksa ya da TL değilse null. */
  fyCiro: number | null;
  yogunluk: number | null;
  /** Büyüme dönemindeki en uzun kümülatif rapor; yoksa null. */
  buyume: number | null;
  reel: boolean | null;
  kaynakIndex: number | null;
};

export type SozSatiriAyrintili = SozSatiri & { adet: number; tl: number; fyCiro: number };

export type SozVerisi = {
  /** Büyüme dönemi sonu, ISO gün. */
  donem: string;
  sozYili: number;
  satirlar: SozSatiriAyrintili[];
  /** Söz yılında işi ve büyümesi olan ama raporu yeniden ifade edilmemiş şirketler. */
  nominal: string[];
  /** Söz yılında sayılan işi olan her şirket; nominal ve FY'siz olanlar dahil. */
  sirketler: Map<string, SirketSozu>;
};

// Yıl sınırı İstanbul saatiyle: 1 Ocak 00:30'daki bildirim UTC'de önceki yıla düşerdi.
const ISTANBUL_YILI = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Europe/Istanbul",
  year: "numeric",
});

/**
 * `analiz_soz_gercek.py` D varyantı. Söz: söz yılında skorlu ve `ayni_is`
 * olmayan bildirimlerin TL toplamı ÷ o yılın FY cirosu (TL). Gerçek:
 * büyüme dönemindeki en uzun kümülatif raporun büyümesi, yalnız reel.
 */
export function sozSatirlariKur(
  duyurular: readonly DuyuruGirdi[],
  buyumeler: readonly BuyumeGirdi[],
): SozVerisi | null {
  const kapsamKume = new Map<string, Set<string>>();
  for (const b of buyumeler) {
    if (b.buyume === null) continue;
    const kume = kapsamKume.get(b.donem_sonu) ?? new Set<string>();
    kume.add(b.ticker);
    kapsamKume.set(b.donem_sonu, kume);
  }
  const donem = buyumeDonemiSec(
    new Map([...kapsamKume].map(([d, kume]) => [d, kume.size])),
  );
  if (donem === null) return null;
  const sozYili = Number(donem.slice(0, 4)) - 1;

  const buyume = new Map<
    string,
    { g: number; reel: boolean; ay: number; kaynak: number | null }
  >();
  const fyCiro = new Map<string, number>();
  for (const b of buyumeler) {
    if (
      b.donem_sonu === donem &&
      b.buyume !== null &&
      b.ay_sayisi > (buyume.get(b.ticker)?.ay ?? 0)
    ) {
      buyume.set(b.ticker, {
        g: b.buyume,
        reel: b.reel,
        ay: b.ay_sayisi,
        kaynak: b.kap_index ?? null,
      });
    }
    if (
      b.donem_sonu === `${sozYili}-12-31` &&
      b.ay_sayisi === 12 &&
      b.para_birimi === "TL" &&
      b.hasilat > 0
    ) {
      fyCiro.set(b.ticker, b.hasilat);
    }
  }

  const duyuru = new Map<string, { tl: number; adet: number }>();
  for (const d of duyurular) {
    if (d.ciro_orani === null || d.onceki_tur === "ayni_is") continue;
    if (Number(ISTANBUL_YILI.format(new Date(d.yayin_zamani))) !== sozYili) continue;
    const toplam = duyuru.get(d.ticker) ?? { tl: 0, adet: 0 };
    toplam.tl += d.net_tutar_tl ?? 0;
    toplam.adet += 1;
    duyuru.set(d.ticker, toplam);
  }

  const satirlar: SozSatiriAyrintili[] = [];
  const nominal: string[] = [];
  const sirketler = new Map<string, SirketSozu>();
  for (const [ticker, { tl, adet }] of duyuru) {
    const g = buyume.get(ticker);
    const ciro = fyCiro.get(ticker) ?? null;
    sirketler.set(ticker, {
      adet,
      tl,
      fyCiro: ciro,
      yogunluk: ciro === null ? null : tl / ciro,
      buyume: g?.g ?? null,
      reel: g ? g.reel : null,
      kaynakIndex: g?.kaynak ?? null,
    });
    if (!g) continue;
    if (!g.reel) {
      nominal.push(ticker);
      continue;
    }
    if (ciro === null) continue;
    satirlar.push({ ticker, yogunluk: tl / ciro, buyume: g.g, adet, tl, fyCiro: ciro });
  }
  nominal.sort();
  return { donem, sozYili, satirlar, nominal, sirketler };
}
