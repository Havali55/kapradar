"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const BAGLANTILAR = [
  { href: "/akis", ad: "Akış" },
  { href: "/hisse", ad: "Hisseler" },
  { href: "/metodoloji", ad: "Yöntem" },
  { href: "/proje-hakkinda", ad: "Proje" },
] as const;

/**
 * Site menüsü. Masaüstünde satır içi; telefonda "Menü" düğmesiyle açılır
 * ve sayfa değişince kapanır. Film menüde yok, proje sayfasından bağlı.
 */
export default function SiteMenu() {
  const yol = usePathname();
  const [acik, setAcik] = useState(false);

  useEffect(() => {
    setAcik(false);
  }, [yol]);

  return (
    <>
      <button
        type="button"
        className="menu-dugme"
        aria-expanded={acik}
        aria-controls="site-menu"
        onClick={() => setAcik((a) => !a)}
      >
        Menü
      </button>
      <nav id="site-menu" className={acik ? "site-nav acik" : "site-nav"} aria-label="Site">
        {BAGLANTILAR.map((b) => {
          const burada = yol === b.href || yol.startsWith(`${b.href}/`);
          return (
            <Link key={b.href} href={b.href} aria-current={burada ? "page" : undefined}>
              {b.ad}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
