import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Serif, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Baslik from "@/components/Baslik";
import { hisseSecenekleriGetir } from "@/lib/veri";

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

// Başlıktaki arama listesi veritabanından geliyor; statik sayfalarda da
// (film, metodoloji) saatlik tazelensin, yoksa yeni hisse bir sonraki
// yayına kadar aranamaz.
export const revalidate = 3600;

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const hisseler = await hisseSecenekleriGetir();
  return (
    <html lang="tr" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>
        <Baslik hisseler={hisseler} />
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
