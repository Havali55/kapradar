/** Biçimleme — hepsi tr-TR. Sayılar tabular, binlik ayracı nokta. */

const TR = "tr-TR";

export function sayi(v: number, ondalik = 2): string {
  return v.toLocaleString(TR, {
    minimumFractionDigits: ondalik,
    maximumFractionDigits: ondalik,
  });
}

/** Büyük TL tutarları: 1,2 Mr TL gibi. Kartta yer dar. */
export function buyukTl(tl: number): string {
  if (tl >= 1e12) return `${sayi(tl / 1e12, 2)} Trilyon TL`;
  if (tl >= 1e9) return `${sayi(tl / 1e9, 2)} Mr TL`;
  if (tl >= 1e6) return `${sayi(tl / 1e6, 0)} Mn TL`;
  return `${sayi(tl, 0)} TL`;
}

/** Tam tutar — detay panelinde, yuvarlama saklanmadan. */
export function tamTl(tl: number): string {
  return `${sayi(tl, 2)} TL`;
}

export function yuzde(oran: number, ondalik = 1): string {
  return `%${sayi(oran * 100, ondalik)}`;
}

/**
 * İyelik ekli yüzde: "%2,3'ü", "%46'sı", "%5,46'sı". Ek sayının sesli
 * okunuşundaki SON sözcüğe uyar. Ondalık varsa virgülden sonrası ayrı bir
 * sayı gibi okunur ("beş virgül kırk altı" → 'sı), yoksa tam kısım.
 * Birler sıfırsa onlar sözcüğü belirler (kırk → 'ı), o da sıfırsa
 * yüz/bin. Eski sürüm yalnız tek ondalığı biliyordu; tam sayı ve iki
 * ondalık basan yerler eki elle "'i" yazıyordu ("%46'i", "%5,46'i").
 */
const BIRLER_EKI = ["", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u"];
const ONLAR_EKI = ["", "'u", "'si", "'u", "'ı", "'si", "'ı", "'i", "'i", "'ı"];

function okunusEki(rakamlar: string): string {
  const n = rakamlar.replace(/^0+/, "");
  if (n === "") return "'ı"; // sıfır
  const birler = Number(n[n.length - 1]);
  if (birler) return BIRLER_EKI[birler];
  const onlar = n.length > 1 ? Number(n[n.length - 2]) : 0;
  if (onlar) return ONLAR_EKI[onlar];
  const sondakiSifir = n.length - n.replace(/0+$/, "").length;
  if (sondakiSifir === 2) return "'ü"; // yüz
  return sondakiSifir < 6 ? "'i" : "'u"; // bin … milyon
}

export function yuzdeIyelik(oran: number, ondalik = 1): string {
  const metin = yuzde(oran, ondalik);
  const [tam, kesir] = metin.slice(1).replace(/\./g, "").split(",");
  return metin + okunusEki(kesir ?? tam);
}

/** "+%3,00" · "−%4,48" · sıfıra yuvarlanan değer işaretsiz. */
export function isaretliYuzde(oran: number, ondalik = 2): string {
  const metin = sayi(Math.abs(oran) * 100, ondalik);
  const sifir = /^[0.,]+$/.test(metin);
  const isaret = sifir ? "" : oran > 0 ? "+" : "−";
  return `${isaret}%${metin}`;
}

const PARA_ADI: Record<string, string> = {
  TRY: "TL",
  USD: "USD",
  EUR: "EUR",
  GBP: "GBP",
  JPY: "JPY",
  CHF: "CHF",
  DIGER: "—",
};

/** Kalem tutarı: "70 Milyon USD" gibi. */
export function kalemTutari(deger: string, paraBirimi: string): string {
  const v = Number(deger);
  if (!Number.isFinite(v)) return `${deger} ${PARA_ADI[paraBirimi] ?? paraBirimi}`;
  const birim = PARA_ADI[paraBirimi] ?? paraBirimi;
  if (v >= 1e9) return `${sayi(v / 1e9, 2)} Milyar ${birim}`;
  // 10 milyonun altında tam sayı fazla kaba: 1.882.423 USD "2 Milyon" olurdu.
  if (v >= 1e6) return `${sayi(v / 1e6, v < 1e7 ? 1 : 0)} Milyon ${birim}`;
  return `${sayi(v, 0)} ${birim}`;
}

export const TIP_ADI: Record<string, string> = {
  ilave_siparis: "İlave sipariş",
  fiyat_farki: "Fiyat farkı",
  tek_seferlik: "Tek seferlik iş",
  toplam_sozlesme: "Toplam sözleşme bedeli",
};

/** Skora giren tipler — `skor.SKORA_GIREN_TIPLER` ile aynı küme. */
export const SKORA_GIREN = new Set([
  "ilave_siparis",
  "fiyat_farki",
  "tek_seferlik",
]);

export function gecenSure(isoTarih: string, simdi = Date.now()): string {
  const fark = simdi - new Date(isoTarih).getTime();
  const dk = Math.round(fark / 60000);
  if (dk < 1) return "az önce";
  if (dk < 60) return `${dk} dk önce`;
  const sa = Math.round(dk / 60);
  if (sa < 24) return `${sa} sa önce`;
  const gun = Math.round(sa / 24);
  if (gun < 30) return `${gun} gün önce`;
  const ay = Math.round(gun / 30);
  return ay < 12 ? `${ay} ay önce` : `${Math.round(ay / 12)} yıl önce`;
}

export function gunEtiketi(isoTarih: string, simdi = new Date()): string {
  const d = new Date(isoTarih);
  const gunFarki = Math.floor(
    (new Date(simdi.getFullYear(), simdi.getMonth(), simdi.getDate()).getTime() -
      new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()) /
      86400000,
  );
  if (gunFarki === 0) return "Bugün";
  if (gunFarki === 1) return "Dün";
  return d.toLocaleDateString(TR, {
    day: "numeric",
    month: "long",
    year: d.getFullYear() === simdi.getFullYear() ? undefined : "numeric",
  });
}

/** "2026-10-15" → "15.10.2026". Saat dilimi dönüşümü yok: gün olduğu gibi. */
export function kisaTarih(isoGun: string): string {
  const [y, a, g] = isoGun.slice(0, 10).split("-");
  return `${g}.${a}.${y}`;
}

/** İstanbul takvimiyle gün: "08.12.2025". Zaman damgasının UTC gününü
 * kesmek akşam 21:00'den sonraki bildirimi bir gün önceye yazardı. */
export function istanbulGunu(isoTarih: string): string {
  return new Date(isoTarih).toLocaleDateString(TR, {
    timeZone: "Europe/Istanbul",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function tamTarih(isoTarih: string): string {
  return new Date(isoTarih).toLocaleString(TR, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Tahtanın kullanıcıya görünen adı ve açıklaması — tek kaynak; kart,
 * detay ve hisse sayfası buradan okur.
 *
 * Veritabanındaki bayrak üç değerli (`skor.py::tahta_bayragi`):
 * tedbirli = yürürlükte VBTS YA DA 90 seansta >8 devre kesici günü YA DA
 * son 5 seansta ≥2; temiz = 90 seansta ≤4 ve son 5 seansta 0; arası
 * hareketli. Görünen ad dört değerli, çünkü "tedbirli" borsada resmî
 * tedbir demek: 2026-09-24'te "tedbirli" etiketli son 2,5 ayın 81
 * bildiriminin 73'ünde resmî tedbir YOKTU, yalnız devre kesici sayımı
 * vardı. Resmî tedbir olmadan "tedbirli" demek yanlış bir olgu
 * bildirmekti; o durum artık "Çok oynak".
 *
 * Eski açıklama "fiyat hareketi habere değil oynaklığa bağlı olabilir"
 * diyordu; dayandığı bulgu (Bulgu 10) örneklem dışında tekrarlanmadı.
 * Açıklamalar artık yalnız sayılan olguyu söylüyor.
 */
export type TahtaGorunumu = {
  ad: string;
  not: string;
  /** globals.css renk değişkeni: yes · kehribar · kir */
  renk: string;
};

export function tahtaGorunumu(
  tahta: string | null,
  v90: number | null,
  v5: number | null,
  vbtsKademe: number | null,
  piyasaOrani: number | null = null,
): TahtaGorunumu | null {
  if (!tahta) return null;
  const sonuc = tahtaAdi(tahta, v90, v5, vbtsKademe);
  if (piyasaOrani === null || piyasaOrani === undefined) return sonuc;
  // Taban oranı (2026-09-26): Eylül 2026'da bildirimlerin %66'sı "çok
  // oynak"tı ama piyasanın da %44'ü öyleydi. Olmadan etiket şirkete özgü
  // okunuyor.
  const taban =
    sonuc.ad === "Sakin" || sonuc.ad === "Oynak"
      ? `Aynı gün piyasadaki hisselerin ${yuzdeIyelik(piyasaOrani, 0)} çok oynaktı.`
      : `Aynı gün piyasadaki hisselerin ${yuzdeIyelik(piyasaOrani, 0)} de bu durumdaydı.`;
  return { ...sonuc, not: `${sonuc.not} ${taban}` };
}

function tahtaAdi(
  tahta: string,
  v90: number | null,
  v5: number | null,
  vbtsKademe: number | null,
): TahtaGorunumu {
  const gun90 = v90 === null ? "" : `Son 90 seansta devre kesici ${v90} gün tetiklenmiş`;
  if (vbtsKademe && vbtsKademe > 0) {
    return {
      ad: "Borsa tedbiri altında",
      not: `Bildirim anında Borsa İstanbul'un volatilite tedbiri yürürlükteydi (${
        VBTS_KADEME_ADI[vbtsKademe] ?? `kademe ${vbtsKademe}`
      }).${gun90 ? ` ${gun90}.` : ""}`,
      renk: "kir",
    };
  }
  if (tahta === "tedbirli") {
    const neden =
      v5 !== null && v5 >= 2
        ? `Son 5 seansta devre kesici ${v5} gün tetiklenmiş`
        : gun90;
    return {
      ad: "Çok oynak",
      not: `${neden}. Resmî bir tedbir yok.`,
      renk: "kir",
    };
  }
  if (tahta === "hareketli") {
    return {
      ad: "Oynak",
      not: gun90 ? `${gun90}.` : "Devre kesici zaman zaman tetikleniyor.",
      renk: "kehribar",
    };
  }
  return {
    ad: "Sakin",
    not: "Son 90 seansta devre kesici en fazla 4 gün tetiklenmiş, son 5 seansta hiç; volatilite tedbiri yok.",
    renk: "yes",
  };
}

/**
 * Bayrağın sınırı: oynaklık ölçüyor. 2026-09 soruşturmasında adı geçen
 * dönemlerde devre kesici AZALMIŞTI — kontrollü bir
 * yükseliş sakin görünür. "Sakin" bu yüzden "sağlıklı" demek değil.
 */
export const TAHTA_SINIR_NOTU =
  "“Sakin” yalnızca oynaklığın düşük olduğunu söyler. Kontrollü, yavaş bir fiyat yükselişi devre kesiciyi tetiklemez; bu bilgi onu ayırt edemez.";

/** Borsa İstanbul Volatilite Bazlı Tedbir Sistemi kademeleri. */
export const VBTS_KADEME_ADI: Record<number, string> = {
  1: "kredili işlem yasağı",
  2: "brüt takas",
  3: "emir paketi",
  4: "tek fiyat",
};

export const SIKLIK_ADI: Record<string, string> = {
  seyrek: "Seyrek bildirimci",
  orta: "Orta sıklıkta",
  sik: "Sık bildirimci",
};

/**
 * Notlar yalnız olguyu söylüyor. "Sık bildirimcide tepki sönük" iddiası
 * 2026-09-24'te kaldırıldı: ilk yılda t = −2,48 iken örneklem dışı yılda
 * t = −0,74 — tekrarlanmayan bir bulgu kullanıcıya olgu diye sunulmaz.
 */
export const SIKLIK_NOTU: Record<string, string> = {
  seyrek:
    "Bu şirket seyrek bildirim yapıyor.",
  orta: "Bu şirketin bildirim sıklığı arşivin orta bandında.",
  sik: "Bu şirket sık bildirim yapıyor.",
};

export const KADEME_ADI: Record<string, string> = {
  rutin: "Rutin",
  onemli: "Önemli iş",
  mega: "Mega iş",
};

/** İstanbul takvimiyle "26 Eyl" ya da uzun hâli "26 Eylül". */
export function gunAy(isoTarih: string, uzun = false): string {
  return new Date(isoTarih).toLocaleDateString(TR, {
    timeZone: "Europe/Istanbul",
    day: "numeric",
    month: uzun ? "long" : "short",
  });
}

/**
 * Yıl + bulunma eki: "2025'te", "2026'da". Ek, yılın okunuşundaki son
 * sözcüğe uyar (beş → te, altı → da). Birler sıfırsa onlar, o da
 * sıfırsa yüz/bin ("de").
 */
const BIRLER_DE = ["", "'de", "'de", "'te", "'te", "'te", "'da", "'de", "'de", "'da"];
const ONLAR_DE = ["", "'da", "'de", "'da", "'ta", "'de", "'ta", "'te", "'de", "'da"];

export function yilda(yil: number): string {
  const birler = yil % 10;
  const onlar = Math.floor(yil / 10) % 10;
  if (birler) return `${yil}${BIRLER_DE[birler]}`;
  if (onlar) return `${yil}${ONLAR_DE[onlar]}`;
  return `${yil}'de`;
}
