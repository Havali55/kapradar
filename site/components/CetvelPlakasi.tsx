"use client";

import { useState } from "react";
import { buyukTl, gunAy, yuzdeIyelik } from "@/lib/bicim";
import { etiketYerlestir, kovanYerlesimi, seyrekEtiketler } from "@/lib/cetvel";
import {
  MEGA_ORAN,
  ONEMLI_ORAN,
  TABAN_ORAN,
  TAVAN_ORAN,
  buyuklukBul,
  fOran,
  type Kademe,
} from "@/lib/skor";
import { useGenislik } from "./useGenislik";

export type CetvelIsi = {
  kap_id: string;
  ticker: string;
  oran: number;
  tl: number | null;
  ozet: string;
  karsi: string | null;
  zaman: string;
};

// Plakadaki renkler (tasarım §3): koyu zeminde doğrulanmış seri.
const RENK: Record<Kademe, string> = {
  mega: "var(--p-mega)",
  onemli: "var(--p-onemli)",
  rutin: "var(--p-rutin)",
};
const BOLGELER: { k: Kademe; a: number; b: number; ad: string; opak: number }[] = [
  { k: "rutin", a: TABAN_ORAN, b: ONEMLI_ORAN, ad: "RUTİN", opak: 0.05 },
  { k: "onemli", a: ONEMLI_ORAN, b: MEGA_ORAN, ad: "ÖNEMLİ", opak: 0.05 },
  { k: "mega", a: MEGA_ORAN, b: TAVAN_ORAN, ad: "MEGA", opak: 0.08 },
];
const ISARETLER: [number, string][] = [
  [0.0025, "%0,25"],
  [0.01, "%1"],
  [0.05, "%5"],
  [0.15, "%15"],
  [0.5, "%50"],
  [1, "%100"],
];
const VARSAYILAN = 640;
const ETIKETLI = 5;
/** 11 px JetBrains Mono'da bir karakterin genişliği (0,6 em). */
const KARAKTER = 6.6;

/**
 * Pencerenin her işi, sitenin skor ölçeğinde (log f(r)) bir nokta. Arka
 * planda kademe bölgeleri ve sayıları. En büyük beş iş çakışmasız
 * etiketli; nokta kanıt sayfasına bağlantı, ipucu imleçte ve odakta.
 */
export default function CetvelPlakasi({ isler, baslikId }: { isler: CetvelIsi[]; baslikId: string }) {
  const [kap, W] = useGenislik<HTMLDivElement>(VARSAYILAN);
  const [aktif, setAktif] = useState<number | null>(null);

  if (isler.length === 0) {
    return <p className="bos-grafik">Bu pencerede büyüklüğü hesaplanabilen iş yok.</p>;
  }

  const r = W < 520 ? 6.5 : 8.5;
  const sol = 16;
  const sag = 16;
  const x = (o: number) => sol + fOran(o) * (W - sol - sag);
  const xs = isler.map((i) => x(i.oran));
  const dy = kovanYerlesimi(xs, r, 3);
  const pay = Math.max(3 * r, ...dy.map(Math.abs)) + r + 22;
  const eksenY = 48 + pay;
  const H = eksenY + pay + 30;
  const noktalar = isler.map((_, i) => ({ x: xs[i], y: eksenY + dy[i], r }));
  const buyukler = isler
    .map((_, i) => i)
    .sort((a, b) => isler[b].oran - isler[a].oran)
    .slice(0, ETIKETLI);
  const etiketler = etiketYerlestir(
    // Kenar çizgisi (2 px) noktayı 1 px büyütüyor.
    noktalar.map((n) => ({ ...n, r: n.r + 1 })),
    buyukler.map((i) => ({ i, genislik: isler[i].ticker.length * 7.2 + 4 })),
    { w: W, h: H - 28 },
  );
  // Eksen yazıları: uçlar kenara yaslı, aradakiler ortalı; dar ekranda
  // birbirine binen ara yazı düşer, tik çizgisi kalır.
  const hiza = (i: number) =>
    i === 0 ? "start" : i === ISARETLER.length - 1 ? "end" : "middle";
  const eksenYazisi = new Set(
    seyrekEtiketler(
      ISARETLER.map(([v, metin], i) => {
        const w = metin.length * KARAKTER;
        const x1 = hiza(i) === "start" ? x(v) : hiza(i) === "end" ? x(v) - w : x(v) - w / 2;
        return { x1, x2: x1 + w };
      }),
    ),
  );
  const sayim: Record<Kademe, number> = { rutin: 0, onemli: 0, mega: 0 };
  for (const i of isler) sayim[buyuklukBul(i.oran) as Kademe] += 1;

  const a = aktif === null ? null : isler[aktif];
  const ap = aktif === null ? null : noktalar[aktif];

  return (
    <div className="grafik" ref={kap}>
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={baslikId}>
        {BOLGELER.map((b) => {
          const x1 = x(b.a);
          const x2 = x(b.b);
          return (
            <g key={b.k}>
              <rect
                x={x1}
                y={12}
                width={x2 - x1}
                height={H - 42}
                style={{ fill: RENK[b.k] }}
                fillOpacity={b.opak}
              />
              <text x={(x1 + x2) / 2} y={27} textAnchor="middle" className="bolge-ad">
                {b.ad}
              </text>
              <text x={(x1 + x2) / 2} y={41} textAnchor="middle">
                {sayim[b.k]} iş
              </text>
            </g>
          );
        })}
        {[ONEMLI_ORAN, MEGA_ORAN].map((v) => (
          <line
            key={v}
            x1={x(v)}
            x2={x(v)}
            y1={12}
            y2={H - 30}
            style={{ stroke: "var(--plaka-ken)" }}
            strokeDasharray="2 3"
          />
        ))}
        <line x1={sol} x2={W - sag} y1={eksenY} y2={eksenY} style={{ stroke: "var(--plaka-ken)" }} />
        {ISARETLER.map(([v, metin], i) => (
          <g key={v}>
            <line
              x1={x(v)}
              x2={x(v)}
              y1={eksenY - 4}
              y2={eksenY + 4}
              style={{ stroke: "var(--plaka-mut)" }}
            />
            {eksenYazisi.has(i) && (
              <text x={x(v)} y={H - 12} textAnchor={hiza(i)}>
                {metin}
              </text>
            )}
          </g>
        ))}
        {isler.map((is, i) => {
          const e = etiketler.get(i);
          const ac = () => setAktif(i);
          const kapat = () => setAktif(null);
          return (
            <a
              key={is.kap_id}
              href={`/kap/${is.kap_id}`}
              aria-label={`${is.ticker}: cirosunun ${yuzdeIyelik(is.oran)}, ${gunAy(is.zaman)}`}
              onMouseEnter={ac}
              onMouseLeave={kapat}
              onFocus={ac}
              onBlur={kapat}
            >
              <circle
                className="nokta"
                cx={noktalar[i].x}
                cy={noktalar[i].y}
                r={r}
                style={{ fill: RENK[buyuklukBul(is.oran) as Kademe], stroke: "var(--plaka)" }}
                strokeWidth={2}
              />
              {/* Büyük dokunma alanı: parmak 8 px'lik noktayı ıskalamasın. */}
              <circle cx={noktalar[i].x} cy={noktalar[i].y} r={r + 7} fill="transparent" />
              {e && (
                <text x={e.x} y={e.y} textAnchor="middle" className="yazi-acik">
                  {is.ticker}
                </text>
              )}
            </a>
          );
        })}
      </svg>
      {a && ap && (
        <div
          className={ap.y < 100 ? "ipucu ipucu-alt" : "ipucu"}
          aria-hidden="true"
          style={{
            left: `${(Math.min(Math.max(ap.x, 130), W - 130) / W) * 100}%`,
            top: `${((ap.y < 100 ? ap.y + r : ap.y - r) / H) * 100}%`,
          }}
        >
          <b>
            {a.ticker} · cirosunun {yuzdeIyelik(a.oran)}
          </b>{" "}
          <span className="soluk">{gunAy(a.zaman)}</span>
          <br />
          {a.ozet}
          <br />
          <span className="soluk">
            {a.karsi ?? "Karşı tarafın adı verilmemiş"}
            {a.tl !== null && ` · ${buyukTl(a.tl)}`}
          </span>
        </div>
      )}
    </div>
  );
}
