import type { Metadata } from "next";
import { IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Yazı tipleri build anında indirilip kendi sunucumuzdan veriliyor:
// CDN çağrısı yok, layout kayması yok.
const sans = IBM_Plex_Sans({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
  variable: "--yazi-sans",
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className={`${sans.variable} ${mono.variable}`}>
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
        {children}
      </body>
    </html>
  );
}
