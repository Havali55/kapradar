import { supabase } from "./supabase";
import {
  guvenilirlik,
  kademeBul,
  siklikBayragi,
  yuzdelik,
  type Kademe,
  type SiklikBayragi,
} from "./skor";

// Skor ölçeğinin aynaları `lib/skor.ts`'te; istemci bileşenleri de
// kullandığı için oradan geçiyorlar. Buradan yeniden dışa vuruluyorlar
// ki çağıranlar tek bir yerden alabilsin.
export {
  F_ORAN_METNI,
  MEGA_ESIGI,
  ONEMLI_ESIGI,
  TABAN_ORAN,
  TAVAN_ORAN,
  fOran,
  guvenilirlik,
  kademeBul,
  siklikBayragi,
  siklikRenk,
  skorRengi,
  tahtaRenk,
} from "./skor";

/** Bir tutar kalemi. `alinti` denetlenebilirliğin taşıyıcısı. */
export type Tutar = {
  tip: "ilave_siparis" | "fiyat_farki" | "toplam_sozlesme" | "tek_seferlik";
  deger: string;
  para_birimi: string;
  alinti: string;
};

/** `public.akis` view'ının satırı — sitenin gördüğü her şey. */
export type AkisSatiri = {
  kap_id: string;
  ticker: string;
  sirket: string;
  is_tanimi: string | null;
  yayin_zamani: string;
  kaynak_url: string | null;
  guncelleme_mi: boolean;
  karsi_taraf: string | null;
  karsi_taraf_niteligi: string | null;
  baslangic: string | null;
  etki_skoru: number | null;
  ciro_orani: number | null;
  net_tutar_tl: number | null;
  ttm_hasilat: number | null;
  hap_ozet: string[] | null;
  tutarlar: Tutar[] | null;
  tutar_gizli: boolean;
  car_1g: number | null;
  car_3g: number | null;
  car_5g: number | null;
  tahta: "temiz" | "hareketli" | "tedbirli" | null;
  tahta_v90: number | null;
  tahta_v5: number | null;
  /**
   * Şirketin arşiv penceresindeki (12 ay) toplam bildirim sayısı.
   * `bildirim` tablosunun tamamından sayılıyor — 613'ün hepsi, yayına
   * hazır 597 değil: şirketin ne sıklıkta bildirim yaptığı bizim kaçını
   * skorlayabildiğimizden bağımsız bir gerçek.
   */
  bildirim_sikligi: number | null;
};

export type TepkiPaneli = {
  n: number;
  medyan: number;
  altCeyrek: number;
  ustCeyrek: number;
  pozitifOrani: number;
  /** Akran grubu neye göre kuruldu — kullanıcıya söylenmesi gereken bir şey. */
  esas: "skor+tahta" | "skor";
  /** Bulgu 10–12: tedbirli tahtada panel fiyat oluşumunu değil oynaklığı yansıtır. */
  guvenilir: boolean;
};

export type Bildirim = AkisSatiri & {
  /** Skorun kademesi — akran grubunun da temeli. */
  kademe: Kademe | null;
  /** Güvenilirlik çarpanı K; skordan türetilmiyor, yeniden gösteriliyor. */
  k: number;
  /** Bildirim yorgunluğu kademesi — skora girmez, bağlam etiketi. */
  siklik: SiklikBayragi | null;
  panel: TepkiPaneli | null;
};

/**
 * Panelin ihtiyaç duyduğu her şey. Tek bir bildirim sayfası için 597
 * satırın tamamını çekmek gerekmiyor: akran grubu yalnız bu dört alana
 * bakıyor.
 */
export type PanelGirdi = Pick<
  AkisSatiri,
  "kap_id" | "etki_skoru" | "car_3g" | "tahta"
>;

const ESAS_ASGARI_N = 20;

function panelKur(
  carlar: number[],
  esas: TepkiPaneli["esas"],
  guvenilir: boolean,
): TepkiPaneli | null {
  if (carlar.length === 0) return null;
  const s = [...carlar].sort((a, b) => a - b);
  return {
    n: s.length,
    medyan: yuzdelik(s, 0.5),
    altCeyrek: yuzdelik(s, 0.25),
    ustCeyrek: yuzdelik(s, 0.75),
    pozitifOrani: s.filter((c) => c > 0).length / s.length,
    esas,
    guvenilir,
  };
}

/**
 * Akran grubu: aynı skor kademesi VE aynı tahta kalitesi. Hücre 20'nin
 * altına düşerse yalnız kademeye geriliyor ve bu kullanıcıya söyleniyor.
 *
 * Tahtanın gruba girmesi Adım 16b'nin sonucu: limit günü sayısı mutlak
 * tepkiyi güçlü biçimde artırıyor (t=+4,80) ama yönle ilişkisi sıfır.
 * Tahtaları karıştıran bir panel, spekülatif hareketi "benzer bildirimin
 * tepkisi" diye gösterirdi.
 */
function panelleriHesapla(satirlar: PanelGirdi[]): Map<string, TepkiPaneli> {
  const kademeli = satirlar.map((s) => ({
    ...s,
    kademe: kademeBul(s.etki_skoru),
  }));

  const grupla = (anahtar: (x: (typeof kademeli)[number]) => string | null) => {
    const m = new Map<string, number[]>();
    for (const s of kademeli) {
      const a = anahtar(s);
      if (a === null || s.car_3g === null) continue;
      const liste = m.get(a) ?? [];
      liste.push(s.car_3g);
      m.set(a, liste);
    }
    return m;
  };

  const dar = grupla((s) => (s.kademe && s.tahta ? `${s.kademe}|${s.tahta}` : null));
  const genis = grupla((s) => s.kademe);

  const sonuc = new Map<string, TepkiPaneli>();
  for (const s of kademeli) {
    if (!s.kademe) continue;
    const darAnahtar = s.tahta ? `${s.kademe}|${s.tahta}` : null;
    const darListe = darAnahtar ? (dar.get(darAnahtar) ?? []) : [];
    const guvenilir = s.tahta !== "tedbirli";

    // Kendini akran sayma: tek gözlemlik gruplarda panel kendi tepkisini
    // "benzerlerin tepkisi" diye gösterirdi.
    const cikar = (liste: number[]) => {
      if (s.car_3g === null) return liste;
      const i = liste.indexOf(s.car_3g);
      return i === -1 ? liste : [...liste.slice(0, i), ...liste.slice(i + 1)];
    };

    let panel: TepkiPaneli | null;
    if (darListe.length >= ESAS_ASGARI_N) {
      panel = panelKur(cikar(darListe), "skor+tahta", guvenilir);
    } else {
      panel = panelKur(cikar(genis.get(s.kademe) ?? []), "skor", guvenilir);
    }
    if (panel) sonuc.set(s.kap_id, panel);
  }
  return sonuc;
}

/** Tüm yayına hazır bildirimleri getirir ve panelleri iliştirir. */
export async function bildirimleriGetir(): Promise<Bildirim[]> {
  const { data, error } = await supabase
    .from("akis")
    .select("*")
    .order("yayin_zamani", { ascending: false });

  if (error) {
    throw new Error(`Akış okunamadı: ${error.message}`);
  }
  const satirlar = (data ?? []) as AkisSatiri[];
  const paneller = panelleriHesapla(satirlar);

  return satirlar.map((s) => zenginlestir(s, paneller.get(s.kap_id) ?? null));
}

/**
 * Akran grubu girdileri — süreç ömrü boyunca saatlik önbellekte.
 *
 * Neden gerekli: `/kap/[kap_id]` 597 sayfa statik üretiliyor ve her biri
 * akran grubunu kurmak için tüm arşivin skor/tepki/tahta üçlüsüne
 * bakmak zorunda. Önbelleksiz 597 kez aynı sorgu koşardı.
 *
 * Neden modül düzeyinde: derleme tek bir Node süreci, orada bir kez
 * çekiliyor. Çalışma anında ise TTL sayfaların `revalidate = 3600`
 * değeriyle aynı — yani önbellek sayfadan daha uzun yaşamıyor.
 */
const PANEL_TTL_MS = 3600_000;
let panelBellek: { zaman: number; veri: PanelGirdi[] } | null = null;

async function panelGirdileriGetir(): Promise<PanelGirdi[]> {
  if (panelBellek && Date.now() - panelBellek.zaman < PANEL_TTL_MS) {
    return panelBellek.veri;
  }
  const { data, error } = await supabase
    .from("akis")
    .select("kap_id, etki_skoru, car_3g, tahta");

  if (error) {
    throw new Error(`Akran grubu okunamadı: ${error.message}`);
  }
  const veri = (data ?? []) as PanelGirdi[];
  panelBellek = { zaman: Date.now(), veri };
  return veri;
}

function zenginlestir(satir: AkisSatiri, panel: TepkiPaneli | null): Bildirim {
  return {
    ...satir,
    kademe: kademeBul(satir.etki_skoru),
    k: guvenilirlik(satir.karsi_taraf !== null, satir.guncelleme_mi),
    siklik: siklikBayragi(satir.bildirim_sikligi),
    panel,
  };
}

/** Tek bir bildirim — `/kap/[kap_id]` sayfasının kaynağı. */
export async function bildirimGetir(kapId: string): Promise<Bildirim | null> {
  const [{ data, error }, girdiler] = await Promise.all([
    supabase.from("akis").select("*").eq("kap_id", kapId).maybeSingle(),
    panelGirdileriGetir(),
  ]);

  if (error) {
    throw new Error(`Bildirim okunamadı: ${error.message}`);
  }
  if (!data) return null;

  const satir = data as AkisSatiri;
  return zenginlestir(satir, panelleriHesapla(girdiler).get(kapId) ?? null);
}

/** Bir hissenin tüm bildirimleri, yeniden eskiye. */
export async function hisseGetir(ticker: string): Promise<Bildirim[]> {
  const [{ data, error }, girdiler] = await Promise.all([
    supabase
      .from("akis")
      .select("*")
      .eq("ticker", ticker)
      .order("yayin_zamani", { ascending: false }),
    panelGirdileriGetir(),
  ]);

  if (error) {
    throw new Error(`Hisse okunamadı: ${error.message}`);
  }
  const paneller = panelleriHesapla(girdiler);
  return ((data ?? []) as AkisSatiri[]).map((s) =>
    zenginlestir(s, paneller.get(s.kap_id) ?? null),
  );
}

export type HisseOzeti = {
  ticker: string;
  sirket: string;
  adet: number;
  medyanSkor: number | null;
  sonBildirim: string;
  tahta: AkisSatiri["tahta"];
};

/**
 * Hisse listesi — hem `/hisse` dizini hem `generateStaticParams` için.
 * Tek sorguda okunuyor; 597 satır zaten bellekte toplanacak kadar küçük.
 */
export async function hisseleriGetir(): Promise<HisseOzeti[]> {
  const { data, error } = await supabase
    .from("akis")
    .select("ticker, sirket, etki_skoru, yayin_zamani, tahta")
    .order("yayin_zamani", { ascending: false });

  if (error) {
    throw new Error(`Hisse listesi okunamadı: ${error.message}`);
  }

  const gruplar = new Map<string, HisseOzeti & { skorlar: number[] }>();
  for (const s of (data ?? []) as Pick<
    AkisSatiri,
    "ticker" | "sirket" | "etki_skoru" | "yayin_zamani" | "tahta"
  >[]) {
    const mevcut = gruplar.get(s.ticker);
    if (mevcut) {
      mevcut.adet += 1;
      if (s.etki_skoru !== null) mevcut.skorlar.push(s.etki_skoru);
      // Sorgu yeniden eskiye sıralı: ilk görülen en yeni olan.
      if (mevcut.tahta === null) mevcut.tahta = s.tahta;
    } else {
      gruplar.set(s.ticker, {
        ticker: s.ticker,
        sirket: s.sirket,
        adet: 1,
        medyanSkor: null,
        sonBildirim: s.yayin_zamani,
        tahta: s.tahta,
        skorlar: s.etki_skoru !== null ? [s.etki_skoru] : [],
      });
    }
  }

  return [...gruplar.values()]
    .map(({ skorlar, ...h }) => ({
      ...h,
      medyanSkor: skorlar.length
        ? yuzdelik([...skorlar].sort((a, b) => a - b), 0.5)
        : null,
    }))
    .sort((a, b) => b.adet - a.adet || a.ticker.localeCompare(b.ticker, "tr"));
}

/** `/kap/[kap_id]` için statik parametreler. */
export async function kapIdleriGetir(): Promise<string[]> {
  const { data, error } = await supabase.from("akis").select("kap_id");
  if (error) {
    throw new Error(`kap_id listesi okunamadı: ${error.message}`);
  }
  return ((data ?? []) as { kap_id: string }[]).map((s) => s.kap_id);
}

export type Ozet = {
  toplam: number;
  skorlu: number;
  medyanSkor: number | null;
  temizOran: number | null;
  son24: number;
  /** Arşivdeki en yeni bildirimin zamanı — başlıktaki tazelik rozeti. */
  sonBildirim: string | null;
};

export function ozetCikar(bildirimler: Bildirim[]): Ozet {
  const skorlar = bildirimler
    .map((b) => b.etki_skoru)
    .filter((s): s is number => s !== null)
    .sort((a, b) => a - b);

  const tahtali = bildirimler.filter((b) => b.tahta !== null);
  const esik = Date.now() - 24 * 3600 * 1000;

  return {
    toplam: bildirimler.length,
    skorlu: skorlar.length,
    medyanSkor: skorlar.length ? yuzdelik(skorlar, 0.5) : null,
    temizOran: tahtali.length
      ? tahtali.filter((b) => b.tahta === "temiz").length / tahtali.length
      : null,
    son24: bildirimler.filter(
      (b) => new Date(b.yayin_zamani).getTime() >= esik,
    ).length,
    sonBildirim:
      bildirimler.reduce<string | null>(
        (enYeni, b) =>
          enYeni === null || b.yayin_zamani > enYeni ? b.yayin_zamani : enYeni,
        null,
      ) ?? null,
  };
}
