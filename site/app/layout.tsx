import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Serif, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Baslik from "@/components/Baslik";

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
  // Paylaşım kartlarının mutlak adresi: Vercel'in kendi alan adı değil.
  metadataBase: new URL("https://kap.calibresolve.com"),
  title: {
    default: "KAP·RADAR — BIST yeni iş ilişkisi bildirimleri",
    template: "%s · KAP·RADAR",
  },
  description:
    "Borsa İstanbul'daki 'yeni iş ilişkisi' bildirimlerini şirketin kendi cirosuna göre boyutlandıran deterministik bir analiz katmanı. Fiyat tahmini üretmez.",
  robots: { index: true, follow: true },
  // Kart görselleri app/**/opengraph-image.png'den (film/src/og/OgKartlar.tsx).
  openGraph: { siteName: "KAP·RADAR", locale: "tr_TR", type: "website" },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>
        <Baslik />
        {children}
        <footer className="altbilgi">
          <div className="altbilgi-ic">
            <span>
              KAP·RADAR · Kişisel araştırma projesi. Yatırım tavsiyesi değildir,
              fiyat tahmini üretmez.
            </span>
            <span>
              Kaynak: KAP, TCMB · <Link href="/metodoloji">Yöntem ve sınırlar</Link>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
