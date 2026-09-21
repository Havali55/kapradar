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

export function isaretliYuzde(oran: number, ondalik = 2): string {
  const s = oran > 0 ? "+" : "";
  return `${s}%${sayi(oran * 100, ondalik)}`;
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
  if (v >= 1e6) return `${sayi(v / 1e6, 0)} Milyon ${birim}`;
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

export function tamTarih(isoTarih: string): string {
  return new Date(isoTarih).toLocaleString(TR, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const TAHTA_ADI: Record<string, string> = {
  temiz: "Temiz",
  hareketli: "Hareketli",
  tedbirli: "Tedbirli",
};

export const TAHTA_NOTU: Record<string, string> = {
  temiz: "Son 5 günde limit yakını hareket yok, son 90 günde en fazla iki gün.",
  hareketli: "Tahtada zaman zaman limit yakını hareket görülüyor.",
  tedbirli:
    "Tahta sık limit görüyor. Bu hisselerde fiyat hareketi habere değil oynaklığa bağlı olabilir.",
};

export const KADEME_ADI: Record<string, string> = {
  rutin: "Rutin",
  onemli: "Önemli iş",
  mega: "Mega iş",
};
