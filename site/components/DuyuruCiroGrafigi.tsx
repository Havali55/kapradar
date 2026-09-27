"use client";

import { useState, type MouseEvent } from "react";
import { buyukTl, cirosununKati, gunAy, sayi, yuzdeIyelik } from "@/lib/bicim";
import {
  birimSec,
  cikisNoktalari,
  ciroBasamagi,
  guzelAdim,
  kisaAd,
  onIkiAyAraligi,
  tabloSatirlari,
  type CiroBasamagi,
  type SeriNoktasi,
} from "@/lib/hikaye";
import { buyuklukBul, type Kademe } from "@/lib/skor";
import { useGenislik } from "./useGenislik";

export type GrafikIsi = {
  kap_id: string;
  t: number;
  tl: number;
  oran: number;
  ozet: string;
  karsi: string | null;
};

const RENK: Record<Kademe, string> = {
  mega: "var(--p-mega)",
  onemli: "var(--p-onemli)",
  rutin: "var(--p-rutin)",
};
const VARSAYILAN = 720;
const KARAKTER = 6.6;
const AY = new Intl.DateTimeFormat("tr-TR", { month: "short", timeZone: "Europe/Istanbul" });
const tamGun = (t: number) =>
  new Date(t).toLocaleDateString("tr-TR", {
    timeZone: "Europe/Istanbul",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

type Kutu = { x1: number; x2: number; y1: number; y2: number };
const cakisir = (a: Kutu, b: Kutu) =>
  a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;

/**
 * Kayan 12 ayda duyurulan toplam (mavi, dolgulu) ile aynı gün bilinen son
 * 12 aylık ciro (toprak, kesikli; boşlukta kopuk). Çubuklar tek tek işler,
 * kanıt sayfasına bağlantı. Boş halkalar, bir önceki yılın 12 ayını dolup
 * hesaptan çıkan işleri: mavi çizginin her inişinin sebebi. İmleçle gün gün
 * okunur; tablo alternatifi `<details>` içinde, JS'siz de açılır.
 */
export default function DuyuruCiroGrafigi({
  seri,
  isler,
  oncekiYil,
  basamaklar,
  baslikId,
}: {
  seri: SeriNoktasi[];
  isler: GrafikIsi[];
  /** Grafik başlamadan önceki 12 ayın işleri; grafik boyunca hesaptan çıkarlar. */
  oncekiYil: GrafikIsi[];
  basamaklar: CiroBasamagi[];
  baslikId: string;
}) {
  const [kap, W] = useGenislik<HTMLDivElement>(VARSAYILAN);
  const [imlec, setImlec] = useState<number | null>(null);
  const [aktifIs, setAktifIs] = useState<number | null>(null);
  const [aktifCikis, setAktifCikis] = useState<number | null>(null);

  const dar = W < 560;
  const H = dar ? 270 : 340;
  const m = { l: 44, r: dar ? 14 : 104, t: 26, b: 30 };
  const t0 = seri[0].t;
  const t1 = seri[seri.length - 1].t;
  const maks = Math.max(
    1,
    ...seri.map((n) => Math.max(n.duyurulan, n.ciro ?? 0)),
    ...isler.map((i) => i.tl),
  );
  const adim = guzelAdim(maks);
  const ust = Math.ceil(maks / adim) * adim;
  const birim = birimSec(ust);
  const ondalik = adim / birim.bolen < 1 ? 1 : 0;
  const x = (t: number) => m.l + ((t - t0) / (t1 - t0)) * (W - m.l - m.r);
  const y = (v: number) => m.t + (1 - v / ust) * (H - m.t - m.b);
  const birimde = (v: number) => sayi(v / birim.bolen, v / birim.bolen < 10 ? 1 : 0);

  const cizgiler: number[] = [];
  for (let v = 0; v <= ust + adim / 1e6; v += adim) cizgiler.push(v);

  const aylar: number[] = [];
  const d = new Date(t0);
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(1);
  d.setUTCMonth(d.getUTCMonth() + 1);
  for (; d.getTime() <= t1; d.setUTCMonth(d.getUTCMonth() + (dar ? 3 : 1))) aylar.push(d.getTime());

  const duyuruYolu = seri
    .map((n, i) => `${i ? "L" : "M"}${x(n.t).toFixed(1)},${y(n.duyurulan).toFixed(1)}`)
    .join("");
  const alan = `${duyuruYolu}L${x(t1).toFixed(1)},${y(0)}L${x(t0).toFixed(1)},${y(0)}Z`;
  let ciroYolu = "";
  let acik = false;
  for (const n of seri) {
    if (n.ciro === null) {
      acik = false;
      continue;
    }
    ciroYolu += `${acik ? "L" : "M"}${x(n.t).toFixed(1)},${y(n.ciro).toFixed(1)}`;
    acik = true;
  }

  const cikislar = cikisNoktalari(seri, oncekiYil);

  // En büyük üç işin doğrudan etiketi (geniş ekranda): kısa ad + tutar.
  // Başka bir etikete ya da çıkış halkasına binen, çizim alanından taşan
  // konmaz.
  const etiketler: { i: number; x: number; y: number; metin: string }[] = [];
  if (!dar) {
    const kutular: Kutu[] = cikislar.map((c) => {
      const cx = x(seri[c.i].t);
      const cy = y(seri[c.i].duyurulan);
      return { x1: cx - 7, x2: cx + 7, y1: cy - 7, y2: cy + 7 };
    });
    const sira = isler.map((_, i) => i).sort((a, b) => isler[b].tl - isler[a].tl);
    for (const i of sira.slice(0, 3)) {
      const is = isler[i];
      const metin = [kisaAd(is.karsi), birimde(is.tl)].filter(Boolean).join(" ");
      const w = metin.length * KARAKTER;
      const cx = Math.min(Math.max(x(is.t), m.l + w / 2), W - m.r - w / 2);
      const ty = y(is.tl) - 8;
      const kt = { x1: cx - w / 2, x2: cx + w / 2, y1: ty - 11, y2: ty + 3 };
      if (kt.y1 < 0 || kutular.some((k) => cakisir(k, kt))) continue;
      kutular.push(kt);
      etiketler.push({ i, x: cx, y: ty, metin });
    }
  }

  // Serilerin uç etiketleri: 14 px'ten yakınsa birbirinden uzaklaşır.
  const son = seri[seri.length - 1];
  let evY = y(son.duyurulan) + 4;
  let ecY = son.ciro !== null ? y(son.ciro) + 4 : null;
  if (ecY !== null && Math.abs(evY - ecY) < 14) {
    const orta = (evY + ecY) / 2;
    const ustte = evY <= ecY;
    evY = orta + (ustte ? -7 : 7);
    ecY = orta + (ustte ? 7 : -7);
  }

  const hareket = (e: MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    if (px < m.l || px > W - m.r) {
      setImlec(null);
      return;
    }
    const i = Math.round(((px - m.l) / (W - m.l - m.r)) * (seri.length - 1));
    setImlec(Math.min(seri.length - 1, Math.max(0, i)));
  };

  const ai = aktifIs === null ? null : isler[aktifIs];
  const cn = ai === null && aktifCikis !== null ? cikislar[aktifCikis] : null;
  const gn = ai === null && cn === null && imlec !== null ? seri[imlec] : null;
  const gnCiro = gn && gn.ciro !== null ? ciroBasamagi(basamaklar, gn.t) : null;
  const ipucuX = ai ? x(ai.t) : cn ? x(seri[cn.i].t) : gn ? x(gn.t) : 0;
  const ipucuY = ai
    ? y(ai.tl)
    : cn
      ? y(seri[cn.i].duyurulan)
      : gn
        ? y(Math.max(gn.duyurulan, gn.ciro ?? 0))
        : 0;
  const ipucuAlt = ipucuY < 100;

  return (
    <>
      <div className="grafik" ref={kap}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="group"
          aria-labelledby={baslikId}
          onMouseMove={hareket}
          onMouseLeave={() => setImlec(null)}
        >
          {cizgiler.map((v) => (
            <g key={v}>
              <line
                x1={m.l}
                x2={W - m.r}
                y1={y(v)}
                y2={y(v)}
                style={{ stroke: v ? "var(--plaka-ken)" : "var(--plaka-mut)" }}
              />
              <text x={m.l - 8} y={y(v) + 3.5} textAnchor="end">
                {v ? sayi(v / birim.bolen, ondalik) : "0"}
              </text>
            </g>
          ))}
          <text x={m.l} y={m.t - 12} textAnchor="start">
            {birim.ad}
          </text>
          {aylar.map((t) => {
            const a = new Date(t);
            return (
              <text key={t} x={x(t)} y={H - 9} textAnchor="middle">
                {AY.format(a)}
                {a.getUTCMonth() === 0 ? ` '${String(a.getUTCFullYear()).slice(2)}` : ""}
              </text>
            );
          })}
          <path d={alan} style={{ fill: "var(--p-duyuru)" }} fillOpacity={0.1} />
          {isler.map((is, i) => {
            const X = x(is.t);
            const Y = y(is.tl);
            const ac = () => setAktifIs(i);
            const kapat = () => setAktifIs(null);
            return (
              <a
                key={is.kap_id}
                href={`/kap/${is.kap_id}`}
                aria-label={`${gunAy(new Date(is.t).toISOString())}: ${buyukTl(is.tl)}, cironun ${yuzdeIyelik(is.oran)}`}
                onMouseEnter={ac}
                onMouseLeave={kapat}
                onFocus={ac}
                onBlur={kapat}
              >
                <rect
                  className="cubuk"
                  x={X - 2.5}
                  y={Y}
                  width={5}
                  height={Math.max(1, y(0) - Y)}
                  rx={2.5}
                  style={{ fill: RENK[buyuklukBul(is.oran) as Kademe] }}
                />
                <rect x={X - 9} y={m.t} width={18} height={y(0) - m.t} fill="transparent" />
              </a>
            );
          })}
          {ciroYolu && (
            <path
              d={ciroYolu}
              fill="none"
              style={{ stroke: "var(--p-ciro)" }}
              strokeWidth={2.25}
              strokeDasharray="7 5"
            />
          )}
          <path
            d={duyuruYolu}
            fill="none"
            style={{ stroke: "var(--p-duyuru)" }}
            strokeWidth={2.75}
            strokeLinejoin="round"
          />
          {cikislar.map((c, k) => {
            const n = seri[c.i];
            const inis = c.cikan.reduce((t, is) => t + is.tl, 0);
            const goster = () => setAktifCikis(k);
            const gizle = () => setAktifCikis(null);
            return (
              <a
                key={n.t}
                href={`/kap/${c.cikan[0].kap_id}`}
                aria-label={`${tamGun(n.t)}: ${tamGun(c.cikan[0].t)} tarihli ${buyukTl(inis)} tutarındaki iş 12 ayını doldurdu, toplamdan çıktı`}
                onMouseEnter={goster}
                onMouseLeave={gizle}
                onFocus={goster}
                onBlur={gizle}
              >
                <circle
                  className="cikis"
                  cx={x(n.t)}
                  cy={y(n.duyurulan)}
                  r={4}
                  style={{ fill: "var(--plaka)", stroke: "var(--p-duyuru)" }}
                  strokeWidth={2}
                />
                <rect x={x(n.t) - 8} y={y(n.duyurulan) - 8} width={16} height={16} fill="transparent" />
              </a>
            );
          })}
          {etiketler.map((e) => (
            <text key={e.i} x={e.x} y={e.y} textAnchor="middle" className="yazi-acik">
              {e.metin}
            </text>
          ))}
          <circle
            cx={x(son.t)}
            cy={y(son.duyurulan)}
            r={5}
            style={{ fill: "var(--p-duyuru)", stroke: "var(--plaka)" }}
            strokeWidth={2.5}
          />
          {son.ciro !== null && (
            <circle
              cx={x(son.t)}
              cy={y(son.ciro)}
              r={4.5}
              style={{ fill: "var(--p-ciro)", stroke: "var(--plaka)" }}
              strokeWidth={2.5}
            />
          )}
          {!dar && (
            <>
              <text x={x(son.t) + 11} y={evY} className="uc-etiket" style={{ fill: "var(--p-duyuru)" }}>
                {birimde(son.duyurulan)} {birim.kisa}
              </text>
              {son.ciro !== null && ecY !== null && (
                <text x={x(son.t) + 11} y={ecY} className="uc-etiket" style={{ fill: "var(--p-ciro)" }}>
                  {birimde(son.ciro)} {birim.kisa} ciro
                </text>
              )}
            </>
          )}
          {gn && (
            <line
              x1={x(gn.t)}
              x2={x(gn.t)}
              y1={m.t}
              y2={y(0)}
              style={{ stroke: "var(--plaka-yazi)" }}
              opacity={0.35}
            />
          )}
        </svg>
        {(ai || cn || gn) && (
          <div
            className={ipucuAlt ? "ipucu ipucu-alt" : "ipucu"}
            aria-hidden="true"
            style={{
              left: `${(Math.min(Math.max(ipucuX, 130), W - 130) / W) * 100}%`,
              top: `${(ipucuY / H) * 100}%`,
            }}
          >
            {ai ? (
              <>
                <b>
                  {gunAy(new Date(ai.t).toISOString())} · {buyukTl(ai.tl)}
                </b>
                <br />
                {ai.ozet}
                <br />
                <span className="soluk">
                  cironun {yuzdeIyelik(ai.oran)} ·{" "}
                  {ai.karsi ?? "karşı tarafın adı verilmemiş"}
                </span>
              </>
            ) : cn ? (
              <>
                <b>{tamGun(seri[cn.i].t)}: toplamdan çıktı</b>
                {cn.cikan.map((is) => (
                  <span key={is.kap_id}>
                    <br />
                    {is.ozet}
                    <br />
                    <span className="soluk">
                      {tamGun(is.t)} duyurusu · {buyukTl(is.tl)}
                    </span>
                  </span>
                ))}
                <br />
                <span className="soluk">
                  12 ayını doldurdu; mavi çizgi{" "}
                  {buyukTl(cn.cikan.reduce((t, is) => t + is.tl, 0))} indi
                </span>
              </>
            ) : (
              gn && (
                <>
                  <b>{tamGun(gn.t)}</b>
                  <br />
                  12 ayda duyurulan: <b>{buyukTl(gn.duyurulan)}</b>
                  <br />
                  12 aylık ciro: <b>{gn.ciro !== null ? buyukTl(gn.ciro) : "bilinmiyor"}</b>
                  {gnCiro?.donem_sonu && (
                    <>
                      <br />
                      <span className="soluk">
                        {onIkiAyAraligi(gnCiro.donem_sonu)} satışı,{" "}
                        {tamGun(Date.parse(gnCiro.gecerlilik_basi))} raporundan
                      </span>
                    </>
                  )}
                  {gn.ciro !== null && gn.ciro > 0 && (
                    <>
                      <br />
                      <span className="soluk">
                        yıllık cironun {cirosununKati(gn.duyurulan / gn.ciro)}
                      </span>
                    </>
                  )}
                </>
              )
            )}
          </div>
        )}
      </div>
      <details className="grafik-tablo">
        <summary>Tablo olarak göster</summary>
        <div className="tablo-sar">
          <table className="veri-tablo">
            <thead>
              <tr>
                <th scope="col">Gün</th>
                <th scope="col">12 ayda duyurulan</th>
                <th scope="col">12 aylık ciro</th>
                <th scope="col">Oran</th>
              </tr>
            </thead>
            <tbody>
              {tabloSatirlari(seri).map((n) => (
                <tr key={n.t}>
                  <td>{tamGun(n.t)}</td>
                  <td>{buyukTl(n.duyurulan)}</td>
                  <td>{n.ciro !== null ? buyukTl(n.ciro) : "—"}</td>
                  <td>{n.ciro ? cirosununKati(n.duyurulan / n.ciro) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
