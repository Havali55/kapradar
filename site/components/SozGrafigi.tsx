"use client";

import { useState } from "react";
import { isaretliYuzde, kat, yilda } from "@/lib/bicim";
import { kovanYerlesimi } from "@/lib/cetvel";
import type { Grup, SozSatiriAyrintili } from "@/lib/soz";
import { useGenislik } from "./useGenislik";

// Ölçek sınırı: bunun dışındaki büyüme kenarda, içi boş halkayla çizilir;
// ipucu gerçek değeri söyler. Tek uç değer 60 şirketin şeridini ezmesin.
const ALT = -1;
const UST = 2;
const VARSAYILAN = 600;

type Props = {
  gruplar: Grup<SozSatiriAyrintili>[];
  sozYili: number;
  donem: string;
  baslikId: string;
};

/** Üç grup yan yana şerit; her nokta bir şirket, çizgi grubun medyanı. */
export default function SozGrafigi({ gruplar, sozYili, donem, baslikId }: Props) {
  const [kap, W] = useGenislik<HTMLDivElement>(VARSAYILAN);
  const [aktif, setAktif] = useState<string | null>(null);

  const H = W < 520 ? 300 : 340;
  const m = { l: 46, r: 12, t: 16, b: 48 };
  const hepsi = gruplar.flatMap((g) => g.satirlar.map((s) => s.buyume));
  const lo = Math.max(ALT, Math.floor(Math.min(0, ...hepsi) * 2) / 2);
  const hi = Math.min(UST, Math.ceil(Math.max(0, ...hepsi) * 2) / 2);
  const y = (g: number) =>
    m.t + (1 - (Math.min(hi, Math.max(lo, g)) - lo) / (hi - lo)) * (H - m.t - m.b);
  const adim = hi - lo > 1.5 ? 0.5 : 0.25;
  const isaretler: number[] = [];
  for (let t = Math.ceil(lo / adim) * adim; t <= hi + 1e-9; t += adim) {
    isaretler.push(Math.round(t * 100) / 100);
  }
  const kolon = (W - m.l - m.r) / 3;
  const noktalar = gruplar.flatMap((g, gi) => {
    const cx = m.l + kolon * (gi + 0.5);
    const ys = g.satirlar.map((s) => y(s.buyume));
    const dx = kovanYerlesimi(ys, 4, 1, kolon / 2 - 8);
    return g.satirlar.map((s, i) => ({
      s,
      gi,
      x: cx + dx[i],
      y: ys[i],
      disarida: s.buyume < lo || s.buyume > hi,
    }));
  });
  const a = noktalar.find((p) => p.s.ticker === aktif) ?? null;
  const disarida = noktalar.filter((p) => p.disarida).length;
  // "medyan +%20,8" 13 karakter (~86 px); telefonda sütun ~85 px, yalnız değer.
  const medyanOnEki = kolon >= 100 ? "medyan " : "";

  return (
    <>
      <div className="grafik" ref={kap}>
        <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={baslikId}>
          {isaretler.map((t) => (
            <g key={t}>
              <line
                x1={m.l}
                x2={W - m.r}
                y1={y(t)}
                y2={y(t)}
                style={{ stroke: t === 0 ? "var(--plaka-mut)" : "var(--plaka-ken)" }}
              />
              <text x={m.l - 8} y={y(t) + 3.5} textAnchor="end">
                {t === 0 ? "0" : isaretliYuzde(t, 0)}
              </text>
            </g>
          ))}
          {gruplar.map((g, gi) => {
            const cx = m.l + kolon * (gi + 0.5);
            return (
              <g key={g.ad}>
                <line
                  x1={cx - kolon * 0.36}
                  x2={cx + kolon * 0.36}
                  y1={y(g.medyanBuyume)}
                  y2={y(g.medyanBuyume)}
                  style={{ stroke: "var(--plaka-yazi)" }}
                  strokeWidth={2.5}
                  strokeLinecap="round"
                />
                <text x={cx} y={H - 26} textAnchor="middle" className="yazi-acik">
                  {g.ad}
                </text>
                <text x={cx} y={H - 10} textAnchor="middle">
                  {medyanOnEki}
                  {isaretliYuzde(g.medyanBuyume, 1)}
                </text>
              </g>
            );
          })}
          {noktalar.map((p) => {
            const renk = p.gi === 2 ? "var(--p-duyuru)" : "var(--plaka-mut)";
            const ac = () => setAktif(p.s.ticker);
            const kapat = () => setAktif(null);
            return (
              <a
                key={p.s.ticker}
                href={`/hisse/${p.s.ticker}`}
                aria-label={`${p.s.ticker}: ${yilda(sozYili)} duyurulan / ciro ${kat(p.s.yogunluk)}, ${donem} reel büyüme ${isaretliYuzde(p.s.buyume, 1)}`}
                onMouseEnter={ac}
                onMouseLeave={kapat}
                onFocus={ac}
                onBlur={kapat}
              >
                <circle
                  className="nokta"
                  cx={p.x}
                  cy={p.y}
                  r={4}
                  style={{
                    fill: p.disarida ? "var(--plaka)" : renk,
                    stroke: p.disarida ? renk : "var(--plaka)",
                  }}
                  strokeWidth={p.disarida ? 1.5 : 1}
                />
                <circle cx={p.x} cy={p.y} r={9} fill="transparent" />
              </a>
            );
          })}
        </svg>
        {a && (
          <div
            className={a.y < 100 ? "ipucu ipucu-alt" : "ipucu"}
            aria-hidden="true"
            style={{
              left: `${(Math.min(Math.max(a.x, 130), W - 130) / W) * 100}%`,
              top: `${((a.y < 100 ? a.y + 4 : a.y - 4) / H) * 100}%`,
            }}
          >
            <b>{a.s.ticker}</b>
            <br />
            {yilda(sozYili)} duyurulan: cironun <b>{kat(a.s.yogunluk)}</b> ({a.s.adet} iş)
            <br />
            {donem} reel büyüme: <b>{isaretliYuzde(a.s.buyume, 1)}</b>
          </div>
        )}
      </div>
      {/* Kabın dışında: ipucu kabın yüksekliğine göre yüzdeyle konumlanıyor. */}
      {disarida > 0 && (
        <p className="grafik-not">
          {disarida} şirket ölçeğin dışında ({isaretliYuzde(lo, 0)} ile {isaretliYuzde(hi, 0)}{" "}
          arası çizildi): kenarda içi boş halka.
        </p>
      )}
    </>
  );
}
