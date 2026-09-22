"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { Bildirim } from "@/lib/veri";
import BildirimDetayi from "./BildirimDetayi";

/**
 * Akıştaki yan panel: ayrıntının kendisi `BildirimDetayi`'nde, burada
 * yalnız kabuk var — gezinme, kapatma, kalıcı bağlantı.
 *
 * Panelin var olma sebebi hız: akışta kaybolmadan bakıp devam etmek.
 * Kalıcı adres gerektiğinde `/kap/[kap_id]` sayfası aynı gövdeyi
 * sunucuda üretiyor.
 */
export default function DetayPanel({
  bildirim: b,
  onKapat,
  onOnceki,
  onSonraki,
  oncekiVar,
  sonrakiVar,
  konum,
}: {
  bildirim: Bildirim;
  onKapat: () => void;
  onOnceki: () => void;
  onSonraki: () => void;
  oncekiVar: boolean;
  sonrakiVar: boolean;
  konum: string;
}) {
  const [kopyaEtiketi, setKopyaEtiketi] = useState("Bağlantıyı kopyala");
  const kapatRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    kapatRef.current?.focus();
  }, []);

  useEffect(() => {
    setKopyaEtiketi("Bağlantıyı kopyala");
  }, [b.kap_id]);

  const kopyala = async () => {
    // Kalıcı adres artık gerçek bir sayfa; kopyalanan bağlantı da o
    // olmalı. `?b=` sorgu parametresi akışta panel açmaya devam ediyor
    // ama paylaşılan bağlantının bir başlığı ve önizlemesi olsun.
    const adres = `${window.location.origin}/kap/${b.kap_id}`;
    try {
      await navigator.clipboard.writeText(adres);
      setKopyaEtiketi("Kopyalandı ✓");
    } catch {
      setKopyaEtiketi("Kopyalanamadı");
    }
  };

  return (
    <>
      <button
        type="button"
        className="perde"
        onClick={onKapat}
        aria-label="Ayrıntı panelini kapat"
      />
      <aside
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-label={`${b.ticker} bildirim ayrıntısı`}
      >
        <div className="panel-bas">
          <Link href={`/hisse/${b.ticker}`} className="panel-ticker mono">
            {b.ticker}
          </Link>
          <span className="mono" style={{ fontSize: 11, color: "var(--mut-2)" }}>
            {konum}
          </span>
          <div className="panel-gezin">
            <button
              type="button"
              className="panel-dugme"
              onClick={onOnceki}
              disabled={!oncekiVar}
              aria-label="Önceki bildirim"
              title="Önceki (↑)"
            >
              ↑
            </button>
            <button
              type="button"
              className="panel-dugme"
              onClick={onSonraki}
              disabled={!sonrakiVar}
              aria-label="Sonraki bildirim"
              title="Sonraki (↓)"
            >
              ↓
            </button>
            <button
              ref={kapatRef}
              type="button"
              className="panel-dugme"
              onClick={onKapat}
              aria-label="Kapat"
              title="Kapat (Esc)"
            >
              ×
            </button>
          </div>
        </div>

        <div className="panel-govde">
          <BildirimDetayi bildirim={b} />

          <div className="panel-eylem">
            <Link className="bag" href={`/kap/${b.kap_id}`}>
              Kalıcı sayfası →
            </Link>
            <Link className="bag" href={`/hisse/${b.ticker}`}>
              {b.ticker} sayfası →
            </Link>
            {b.kaynak_url && (
              <a
                className="bag"
                href={b.kaynak_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                KAP&apos;taki orijinal bildirim ↗
              </a>
            )}
            <button type="button" className="bag" onClick={kopyala}>
              {kopyaEtiketi}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
