import Link from "next/link";
import SiteMenu from "./SiteMenu";

/**
 * Radar işareti (marka şeması 2a): iki halka, artı ekseni, 45° tarama
 * kolu ve arkasındaki iz. Nokta kolun iç halkayla (r=11) kesiştiği yerde:
 * konumu rastgele değil, ölçülü. Renk `currentColor`, CSS'ten gelir.
 */
function RadarIsareti() {
  return (
    <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <path d="M20 20 L32.02 7.98 A17 17 0 0 0 18.52 3.06 Z" fill="currentColor" fillOpacity={0.16} />
      <circle cx="20" cy="20" r="17" stroke="currentColor" strokeWidth={1.6} />
      <circle cx="20" cy="20" r="11" stroke="currentColor" strokeWidth={0.8} strokeOpacity={0.55} />
      <line x1="3" y1="20" x2="37" y2="20" stroke="currentColor" strokeWidth={0.6} strokeOpacity={0.4} />
      <line x1="20" y1="3" x2="20" y2="37" stroke="currentColor" strokeWidth={0.6} strokeOpacity={0.4} />
      <line x1="20" y1="20" x2="32.02" y2="7.98" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" />
      <circle cx="27.78" cy="12.22" r="3.2" fill="currentColor" />
    </svg>
  );
}

/**
 * Her sayfanın üst bandı: solda logo, sağda gezinme; altında tek satır
 * ibare. Arama bantta yok: ana sayfanın, hisse dizininin ve akışın kendi
 * araması var.
 */
export default function Baslik() {
  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo" aria-label="KAP·RADAR ana sayfa">
            <RadarIsareti />
            <span className="logo-ad">
              KAP<i>·</i>RADAR
            </span>
          </Link>
          <SiteMenu />
        </div>
      </header>
      <div className="ibare">
        {/* Telefonda tek satıra sığsın diye kısa hâli; tam künye altbilgide. */}
        <div className="ibare-ic">
          <span className="ibare-genis">
            Yatırım tavsiyesi değildir · fiyat tahmini üretmez
          </span>
          <span className="ibare-dar">
            Yatırım tavsiyesi değildir · fiyat tahmini üretmez
          </span>
        </div>
      </div>
    </>
  );
}
