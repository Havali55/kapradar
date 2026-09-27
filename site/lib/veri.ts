import type { HisseSecenek } from "./arama";
import { supabase } from "./supabase";
import {
  buyuklukBul,
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
  MEGA_ORAN,
  ONEMLI_ESIGI,
  ONEMLI_ORAN,
  TABAN_ORAN,
  TAVAN_ORAN,
  buyuklukBul,
  fOran,
  guvenilirlik,
  kademeBul,
  kademeRengi,
  siklikBayragi,
  siklikRenk,
  oranRengi,
  tahtaRenk,
} from "./skor";

/**
 * PostgREST sorgu başına en fazla 1.000 satır döndürüyor ve bunu hata
 * olarak BİLDİRMİYOR. Arşiv 2026-09-24'te 1.000 yayına hazır bildirimi
 * aşınca akış, özet sayılar, akran grupları ve `/kap` sayfaları en eski
 * bildirimleri sessizce kaybetti. Tabloyu bütün okuyan her sorgu buradan
 * geçer.
 *
 * Son sayfa "1.000'den az geldi" diye değil BOŞ sayfayla anlaşılıyor:
 * sunucunun sınırı değişirse (ör. 500) ilk yarım sayfa sonun sanılırdı.
 * Sorgunun sırası tekil olmalı (`kap_id` bağ bozucu), yoksa sayfa
 * sınırında satır tekrarlanır ya da atlanır.
 */
type SayfaSonucu = {
  data: unknown[] | null;
  error: { message: string } | null;
};

async function hepsiniOku<T>(
  ad: string,
  sorgu: (bas: number, son: number) => PromiseLike<SayfaSonucu>,
  sayfa = 1000,
): Promise<T[]> {
  const sonuc: T[] = [];
  for (let bas = 0; ; ) {
    const { data, error } = await sorgu(bas, bas + sayfa - 1);
    if (error) throw new Error(`${ad} okunamadı: ${error.message}`);
    const parca = (data ?? []) as T[];
    if (parca.length === 0) return sonuc;
    sonuc.push(...parca);
    bas += parca.length;
  }
}

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
  /**
   * Karşı taraf gerçekten isimle açıklanmış mı (`kap_radar.karsi_taraf`).
   * Alan dolu olabilir ama isim olmayabilir: "Uluslararası Müşteri", ".".
   * İsteğe bağlı: view'a 2026-09-24'te eklendi; eski önbellekten gelen
   * satırda hiç olmayabilir (bkz. `zenginlestir`).
   */
  karsi_taraf_acik?: boolean | null;
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
  /**
   * car_Ng'nin formülü. ew = Σ r − (α + β·r_ew), kıyas eşit ağırlıklı BIST
   * (2026-09-22'den beri); piyasa = aynısı XU100'e karşı; beta1 = Σ r − r_m.
   */
  tepki_modeli: "ew" | "piyasa" | "beta1" | null;
  /** CAR'da kullanılan (Vasicek-küçültülmüş) beta. */
  beta: number | null;
  /**
   * evren_ort: hisse yeni halka açıldı, tahmin penceresinde 60 gözlem yok;
   * beta evren ortalaması, α = 0. Kullanıcıya söylenmesi gereken bir şey.
   */
  beta_kaynak: "tahmin" | "evren_ort" | null;
  /**
   * Bildirim anında yürürlükteki VBTS kademesi: 0 yok, 1 kredili işlem
   * yasağı, 2 brüt takas, 3 emir paketi, 4 tek fiyat. `tahta_v90/v5`
   * `tahta_yontem = kap_v1` iken devre kesicinin başladığı ayrı seans günü.
   */
  tahta_vbts_kademe: number | null;
  tahta_vbts_bitis: string | null;
  tahta_yontem: string | null;
  /** Bildirimden önceki 12 aydaki tüm KAP özel durum açıklamaları. */
  kap_aciklama_12a: number | null;
  /** 365'ten azsa 12 aylık sayım eksik pencereden (yeni halka arz). */
  siklik_arsiv_gun: number | null;
  /**
   * Bildirim anındaki fon durumu (point-in-time): her fonun bildirimden
   * önce yayınlanmış son Portföy Dağılım Raporu. Tasfiye tutarı yalnız
   * SPK kararından sonraki bildirimlerde dolu.
   */
  fon_sayisi: number | null;
  fon_tl: number | null;
  fon_tasfiye_tl: number | null;
  gunluk_hacim_tl: number | null;
  /**
   * Elle karar (`data/elle_duzeltmeler.json`, 2026-09-26). Anlam kapısı
   * şüpheli bulduğunda insan karar verdi; gerekçe kullanıcıya gösterilir.
   * Aşağıdaki alanların hepsi 2026-09-26'da eklendi, eski önbellekte yok.
   */
  elle_karar?: "onayla" | "skorsuz" | "duzelt" | null;
  elle_not?: string | null;
  /**
   * Önceki bildirime bağ (`kap_radar.bag`): duzeltme (öncekinin yerini
   * aldı, önceki yayından kalktı) · ayni_is (tutar önceki bildirimde
   * zaten sayıldı) · guncelleme (bağlı, tutar yeni).
   */
  onceki_kap_id?: string | null;
  onceki_tur?: "duzeltme" | "ayni_is" | "guncelleme" | null;
  onceki_yayin?: string | null;
  /** Bildirim günü piyasadaki hisselerin "çok oynak" kuralını sağlayan payı. */
  tahta_piyasa_orani?: number | null;
};

/** Hisse sayfasındaki BUGÜNKÜ fon durumu (`hisse_fon_guncel`). */
export type HisseFon = {
  ticker: string;
  fon_sayisi: number;
  fon_tl: number;
  portfoy_sirketi_sayisi: number;
  en_buyuk_pay: number | null;
  tasfiye_tl: number;
  tasfiye_fon_sayisi: number;
  gunluk_hacim_tl: number | null;
  fon_tl_3ay_once: number | null;
  son_rapor_donemi: string | null;
  muaf_fon_sayisi: number;
};

export async function hisseFonGetir(ticker: string): Promise<HisseFon | null> {
  const { data, error } = await supabase
    .from("hisse_fon_guncel")
    .select("*")
    .eq("ticker", ticker)
    .maybeSingle();
  if (error) throw new Error(`Fon durumu okunamadı: ${error.message}`);
  return (data as HisseFon | null) ?? null;
}

/** Sitenin üstündeki tek satırlık piyasa bandı (`piyasa_bandi` view). */
export type PiyasaBandi = {
  son_tarih: string;
  ew_5s: number | null;
  xu100_5s: number | null;
  tasfiye_tarihi: string | null;
  tasfiye_sirket_sayisi: number | null;
};

export async function piyasaBandiGetir(): Promise<PiyasaBandi | null> {
  const { data, error } = await supabase.from("piyasa_bandi").select("*").maybeSingle();
  // Bant süs; okunamazsa sayfa düşmesin.
  if (error) return null;
  return (data as PiyasaBandi | null) ?? null;
}

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
  /** Sınıflandırılmışsa `karsi_taraf_acik`, değilse eski kural (alan dolu mu). */
  karsiTarafAcik: boolean;
  /**
   * Görünen büyüklük kademesi — ciro oranından, S'den değil. Akran
   * grubu bunu KULLANMIYOR; o `panelleriHesapla` içinde S kademesiyle
   * ayrıca kuruluyor (metodolojideki tanım).
   */
  kademe: Kademe | null;
  /** Güvenilirlik çarpanı K; skordan türetilmiyor, yeniden gösteriliyor. */
  k: number;
  /** Bildirim yorgunluğu kademesi — skora girmez, bağlam etiketi. */
  siklik: SiklikBayragi | null;
  panel: TepkiPaneli | null;
  /**
   * İş daha önce aynı tutarla duyurulmuştu (ihale → sözleşme). Kart
   * gösterilir ama yeni iş sayılmaz: büyüklük filtresine, "en büyük iş"
   * sıralamasına ve özet medyanlarına girmez.
   */
  oncedenDuyuruldu: boolean;
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
 * Tahtanın gruba girmesi Bulgu 12'nin sonucu: devre kesici gören
 * tahtada ortalama tepki aşağı yönlü — ilk yılda t=−2,62, örneklem dışı
 * yılda t=−2,85. (İlk gerekçe "oynaklık var, yön yok" idi; o çöktü.)
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
  const satirlar = await hepsiniOku<AkisSatiri>("Akış", (bas, son) =>
    supabase
      .from("akis")
      .select("*")
      .order("yayin_zamani", { ascending: false })
      .order("kap_id")
      .range(bas, son),
  );
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
  const veri = await hepsiniOku<PanelGirdi>("Akran grubu", (bas, son) =>
    supabase
      .from("akis")
      .select("kap_id, etki_skoru, car_3g, tahta")
      .order("kap_id")
      .range(bas, son),
  );
  panelBellek = { zaman: Date.now(), veri };
  return veri;
}

function zenginlestir(satir: AkisSatiri, panel: TepkiPaneli | null): Bildirim {
  // `!= null`: sütun yoksa undefined, sınıflandırılmamışsa null gelir.
  const acik =
    satir.karsi_taraf_acik != null
      ? satir.karsi_taraf_acik
      : satir.karsi_taraf !== null;
  return {
    ...satir,
    kademe: buyuklukBul(satir.ciro_orani),
    karsiTarafAcik: acik,
    k: guvenilirlik(acik, satir.guncelleme_mi),
    siklik: siklikBayragi(satir.bildirim_sikligi),
    panel,
    oncedenDuyuruldu: satir.onceki_tur === "ayni_is",
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
 * Sayfalı okunuyor (bkz. `hepsiniOku`); birkaç bin satır bellekte
 * toplanacak kadar küçük.
 */
export async function hisseleriGetir(): Promise<HisseOzeti[]> {
  const satirlar = await hepsiniOku<
    Pick<AkisSatiri, "ticker" | "sirket" | "etki_skoru" | "yayin_zamani" | "tahta">
  >("Hisse listesi", (bas, son) =>
    supabase
      .from("akis")
      .select("ticker, sirket, etki_skoru, yayin_zamani, tahta")
      .order("yayin_zamani", { ascending: false })
      .order("kap_id")
      .range(bas, son),
  );

  const gruplar = new Map<string, HisseOzeti & { skorlar: number[] }>();
  for (const s of satirlar) {
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

/**
 * Başlıktaki arama listesi. Layout her statik sayfada koşuyor (1.400+
 * sayfa), bu yüzden `panelGirdileriGetir` gibi süreç düzeyinde ve aynı
 * TTL ile önbellekte.
 */
let aramaBellek: { zaman: number; veri: HisseSecenek[] } | null = null;

export async function hisseSecenekleriGetir(): Promise<HisseSecenek[]> {
  if (aramaBellek && Date.now() - aramaBellek.zaman < PANEL_TTL_MS) {
    return aramaBellek.veri;
  }
  const veri = (await hisseleriGetir()).map((h) => ({
    t: h.ticker,
    s: h.sirket,
    n: h.adet,
  }));
  aramaBellek = { zaman: Date.now(), veri };
  return veri;
}

/** `/kap/[kap_id]` için statik parametreler. */
export async function kapIdleriGetir(): Promise<string[]> {
  const satirlar = await hepsiniOku<{ kap_id: string }>("kap_id listesi", (bas, son) =>
    supabase.from("akis").select("kap_id").order("kap_id").range(bas, son),
  );
  return satirlar.map((s) => s.kap_id);
}

export type Ozet = {
  toplam: number;
  skorlu: number;
  medyanSkor: number | null;
  /** Skorlu bildirimlerde sözleşme / TTM hasılat medyanı — ana sayfa bunu gösteriyor, S'yi değil. */
  medyanOran: number | null;
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

  const oranlar = bildirimler
    .filter(
      (b) => b.etki_skoru !== null && b.ciro_orani !== null && !b.oncedenDuyuruldu,
    )
    .map((b) => b.ciro_orani as number)
    .sort((a, b) => a - b);

  const tahtali = bildirimler.filter((b) => b.tahta !== null);
  const esik = Date.now() - 24 * 3600 * 1000;

  return {
    toplam: bildirimler.length,
    skorlu: skorlar.length,
    medyanSkor: skorlar.length ? yuzdelik(skorlar, 0.5) : null,
    medyanOran: oranlar.length ? yuzdelik(oranlar, 0.5) : null,
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
