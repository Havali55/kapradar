import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Serif, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { isaretliYuzde, kisaTarih } from "@/lib/bicim";
import { piyasaBandiGetir } from "@/lib/veri";

// Yazı tipleri build anında indirilip kendi sunucumuzdan veriliyor:
// CDN çağrısı yok, layout kayması yok.
const sans = IBM_Plex_Sans({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
  variable: "--yazi-sans",
  display: "swap",
});

// Başlıklar: filmle aynı serif.
const serif = IBM_Plex_Serif({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  variable: "--yazi-serif",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
  variable: "--yazi-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "KAP·RADAR — BIST yeni iş ilişkisi bildirimleri",
    template: "%s · KAP·RADAR",
  },
  description:
    "Borsa İstanbul'daki 'yeni iş ilişkisi' bildirimlerini şirketin kendi cirosuna göre boyutlandıran deterministik bir analiz katmanı. Fiyat tahmini üretmez.",
  robots: { index: true, follow: true },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const bant = await piyasaBandiGetir();
  return (
    <html lang="tr" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>
        <div className="serit">
          <div className="serit-ic">
            <span className="rozet mono">UYARI</span>
            <span>
              Bu bir kişisel araştırma projesidir. Yatırım tavsiyesi değildir,
              fiyat tahmini üretmez.
            </span>
          </div>
        </div>
        {bant && (
          // Bağlam katmanı: piyasanın geneli. Olgu + tarih, yorum yok.
          <div className="bant">
            <div className="bant-ic">
              <span className="rozet mono">PİYASA</span>
              <span>
                Son 5 seans ({kisaTarih(bant.son_tarih)} itibarıyla): eşit ağırlıklı
                BIST{" "}
                <strong className="mono">
                  {bant.ew_5s !== null ? isaretliYuzde(bant.ew_5s, 1) : "—"}
                </strong>{" "}
                · XU100{" "}
                <strong className="mono">
                  {bant.xu100_5s !== null ? isaretliYuzde(bant.xu100_5s, 1) : "—"}
                </strong>
                {bant.tasfiye_tarihi && (
                  <>
                    {" "}
                    · SPK {kisaTarih(bant.tasfiye_tarihi)} tarihinde{" "}
                    {bant.tasfiye_sirket_sayisi} portföy şirketinin fonlarını
                    tasfiyeye aldı.
                  </>
                )}
              </span>
            </div>
          </div>
        )}
        {children}
      </body>
    </html>
  );
}
