import Link from "next/link";
import type { HisseSecenek } from "@/lib/arama";
import HisseArama from "./HisseArama";
import SiteMenu from "./SiteMenu";

/** Her sayfanın başlığı: logo · hisse arama · menü, altında tek satır ibare. */
export default function Baslik({ hisseler }: { hisseler: HisseSecenek[] }) {
  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo" aria-label="KAP·RADAR ana sayfa">
            <svg viewBox="0 0 22 22" aria-hidden="true">
              <rect x="1" y="1" width="20" height="20" rx="5" fill="#16150f" />
              <path d="M5 15.5h12" stroke="#6b665a" strokeWidth="1.2" />
              <path
                d="M8 15.5v-3M11 15.5v-6M14 15.5v-9"
                stroke="#4a8fd6"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            <span className="logo-ad mono">
              KAP<i>·</i>RADAR
            </span>
          </Link>
          <HisseArama hisseler={hisseler} kisayol />
          <SiteMenu />
        </div>
      </header>
      <div className="ibare">
        {/* Telefonda tek satıra sığsın diye kısa hâli; tam künye altbilgide. */}
        <div className="ibare-ic">
          <span className="ibare-genis">
            Kişisel araştırma projesi · yatırım tavsiyesi değildir · fiyat
            tahmini üretmez
          </span>
          <span className="ibare-dar">
            Yatırım tavsiyesi değildir · fiyat tahmini üretmez
          </span>
        </div>
      </div>
    </>
  );
}
