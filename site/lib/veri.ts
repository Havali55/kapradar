import { supabase } from "./supabase";

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
  kademe: "rutin" | "onemli" | "mega" | null;
  /** Güvenilirlik çarpanı K; skordan türetilmiyor, yeniden gösteriliyor. */
  k: number;
  panel: TepkiPaneli | null;
};

const ESAS_ASGARI_N = 20;

export function kademeBul(skor: number | null): Bildirim["kademe"] {
  if (skor === null) return null;
  if (skor >= 3) return "mega";
  if (skor >= 2) return "onemli";
  return "rutin";
}

/**
 * K — skorun içindeki güvenilirlik çarpanı. Burada YENİDEN HESAPLANMIYOR,
 * yalnızca gösterim için aynı tablodan okunuyor; skorun kendisi veritabanından
 * geliyor (`etki_skoru`). Formülün iki kopyası olmasın diye kural bu.
 */
export function guvenilirlik(ktAcik: boolean, guncelleme: boolean): number {
  if (ktAcik) return guncelleme ? 0.85 : 1.0;
  return guncelleme ? 0.7 : 0.5;
}

/**
 * En yakın sıra istatistiği; ara değer üretmiyor. Python tarafındaki
 * `skor._yuzdelik` ile birebir aynı: gerçekten gözlenmiş bir getiriyi
 * göstermek, iki gözlem arasında hiç yaşanmamış bir sayı uydurmaktan dürüst.
 */
function yuzdelik(sirali: number[], oran: number): number {
  return sirali[Math.floor(oran * (sirali.length - 1))];
}

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
function panelleriHesapla(satirlar: AkisSatiri[]): Map<string, TepkiPaneli> {
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

  return satirlar.map((s) => ({
    ...s,
    kademe: kademeBul(s.etki_skoru),
    k: guvenilirlik(s.karsi_taraf !== null, s.guncelleme_mi),
    panel: paneller.get(s.kap_id) ?? null,
  }));
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
