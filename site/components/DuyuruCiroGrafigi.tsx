"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { buyukTl, cirosununKati, gunAy, sayi, yuzdeIyelik } from "@/lib/bicim";
import {
  birimSec,
  ciroBasamagi,
  ciroSicramalari,
  donemEtiketi,
  gunDegisimi,
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
/** Rapor etiketi 10 px mono. */
const KUCUK_KARAKTER = 6;
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

/** Eksenin üstü: değeri kapsayan ilk "güzel" adım. */
function olcek(maks: number): { adim: number; ust: number } {
  const adim = guzelAdim(maks);
  return { adim, ust: Math.ceil(maks / adim) * adim };
}

/**
 * Kayan 12 ayda duyurulan toplam (mavi, dolgulu) ile aynı gün bilinen son
 * 12 aylık ciro (toprak, kesikli; boşlukta kopuk). Çubuklar tek tek işler,
 * kanıt sayfasına bağlantı. Ciro çizgisinin her sıçrayışında o raporun
 * dönemi yazılı ("6A26"). İmleçle gün gün okunur; mavi çizginin indiği
 * günün ipucu, 12 ayını dolup hesaptan çıkan işi söyler. Tablo alternatifi
 * `<details>` içinde, JS'siz de açılır.
 *
 * Dokunmatik ekranda çubuğa ilk dokunuş ipucunu açar, ikincisi kanıt
 * sayfasına gider; boş yere dokunuş o günün ipucunu açar. Fare ve klavyede
 * tık doğrudan gider (ipucu üstüne gelince zaten açık).
 *
 * Ciro işleri ezdiğinde (TCKRC: 5,6 milyar ciro, 0,3 milyar iş) "İşlere
 * odaklan" dikey ekseni işlere göre kurar; ciro çizgisi çizim alanında
 * kırpılır, ölçeğin üstünde kaldığı ok ve yazıyla söylenir.
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
  const [odak, setOdak] = useState(false);
  /** İpucu dokunuşla açıldıysa "bir kez daha dokunun" satırı görünür. */
  const [dokunmali, setDokunmali] = useState(false);
  /** Son işaretçi türü: "mouse", "touch", "pen" ya da klavye. */
  const isaretci = useRef<string>("mouse");
  /** İlk dokunuşu almış öğe; aynı öğeye ikinci dokunuş sayfaya gider. */
  const dokunulan = useRef<string | null>(null);
  const klipId = `grafik-klip-${useId().replace(/:/g, "")}`;

  const sifirla = () => {
    dokunulan.current = null;
    setAktifIs(null);
    setDokunmali(false);
  };

  // Grafiğin dışına dokunulunca açık ipucu kapansın.
  useEffect(() => {
    const disari = (e: PointerEvent) => {
      if (kap.current && !kap.current.contains(e.target as Node)) {
        dokunulan.current = null;
        setAktifIs(null);
        setDokunmali(false);
        setImlec(null);
      }
    };
    document.addEventListener("pointerdown", disari);
    return () => document.removeEventListener("pointerdown", disari);
  }, [kap]);

  const dar = W < 560;
  const H = dar ? 270 : 340;
  const m = { l: 44, r: dar ? 14 : 104, t: 26, b: 30 };
  const t0 = seri[0].t;
  const t1 = seri[seri.length - 1].t;

  // Ölçek. Odaklama yalnız bir şey değiştiriyorsa sunuluyor: işlerin
  // kendi ölçeği cirolu ölçekten küçükse.
  const maksIs = Math.max(1, ...seri.map((n) => n.duyurulan), ...isler.map((i) => i.tl));
  const maksCiro = Math.max(0, ...seri.map((n) => n.ciro ?? 0));
  const tam = olcek(Math.max(maksIs, maksCiro));
  const odakOlcegi = olcek(maksIs);
  const odakAnlamli = odakOlcegi.ust < tam.ust;
  const odakta = odak && odakAnlamli;
  const { adim, ust } = odakta ? odakOlcegi : tam;
  const birim = birimSec(ust);
  const ondalik = adim / birim.bolen < 1 ? 1 : 0;
  const x = (t: number) => m.l + ((t - t0) / (t1 - t0)) * (W - m.l - m.r);
  const y = (v: number) => m.t + (1 - v / ust) * (H - m.t - m.b);
  const birimde = (v: number) => sayi(v / birim.bolen, v / birim.bolen < 10 ? 1 : 0);
  const ciroBirimi = birimSec(maksCiro);
  const ciroMetni = (v: number) =>
    `${sayi(v / ciroBirimi.bolen, v / ciroBirimi.bolen < 10 ? 1 : 0)} ${ciroBirimi.kisa}`;

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
  const ciroTasiyor = odakta && seri.some((n) => n.ciro !== null && n.ciro > ust);

  // Çizim alanındaki yazılar çakışmasın: önce en büyük üç işin etiketi
  // (geniş ekranda), sonra rapor etiketleri. Başka bir kutuya binen ya da
  // alandan taşan konmaz.
  const kutular: Kutu[] = [];
  const etiketler: { i: number; x: number; y: number; metin: string }[] = [];
  if (!dar) {
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
  /** Mavi çizginin bir parçası kutudan geçiyor mu (basamakların dikeyleri dahil). */
  const maviyeDeger = (k: Kutu) =>
    seri.some((n, i) => {
      if (i === 0) return false;
      const xa = x(seri[i - 1].t);
      const xb = x(n.t);
      const ya = y(seri[i - 1].duyurulan);
      const yb = y(n.duyurulan);
      return xb >= k.x1 && xa <= k.x2 && Math.max(ya, yb) >= k.y1 - 2 && Math.min(ya, yb) <= k.y2 + 2;
    });
  const raporlar: { x: number; y: number; metin: string }[] = [];
  for (const i of ciroSicramalari(seri)) {
    const n = seri[i];
    if (n.ciro === null || n.ciro > ust) continue;
    const b = ciroBasamagi(basamaklar, n.t);
    if (!b?.donem_sonu) continue;
    const metin = donemEtiketi(b.donem_sonu);
    const tx = x(n.t) + 4;
    // Önce çizginin üstü, sığmazsa altı.
    for (const ty of [y(n.ciro) - 6, y(n.ciro) + 14]) {
      const kt = { x1: tx - 1, x2: tx + metin.length * KUCUK_KARAKTER + 1, y1: ty - 10, y2: ty + 2 };
      if (kt.x2 > W - m.r || kt.y1 < m.t - 2 || kt.y2 > y(0) - 2) continue;
      if (kutular.some((k) => cakisir(k, kt)) || maviyeDeger(kt)) continue;
      kutular.push(kt);
      raporlar.push({ x: tx, y: ty, metin });
      break;
    }
  }

  // Serilerin uç etiketleri: 16 px'ten yakınsa birbirinden uzaklaşır (11,5 px
  // yazının kutusu ~15 px). Ciro ölçeğin üstündeyse ucu çizim alanının
  // tepesinde, okla.
  const son = seri[seri.length - 1];
  const sonCiroUstte = son.ciro !== null && son.ciro > ust;
  const noktaEv = y(son.duyurulan);
  const noktaEc = son.ciro === null ? null : sonCiroUstte ? m.t : y(son.ciro);
  let evY = noktaEv + 4;
  let ecY = noktaEc !== null ? noktaEc + 4 : null;
  if (ecY !== null && Math.abs(evY - ecY) < 16) {
    const orta = (evY + ecY) / 2;
    const ustte = evY <= ecY;
    evY = orta + (ustte ? -8 : 8);
    ecY = orta + (ustte ? 8 : -8);
  }
  // Dar ekranda uç etiketleri yok: ölçeğin üstündeki ciro sağ üstte.
  // Geniş ekranda son ciro ölçeğin üstündeyse bunu uç etiketi söylüyor.
  const sagUst = !ciroTasiyor
    ? null
    : sonCiroUstte && son.ciro !== null
      ? dar
        ? `ciro ${ciroMetni(son.ciro)} ↑`
        : null
      : "ciro yer yer ölçeğin üstünde ↑";

  /** İmleci işaretçinin altındaki güne koyar; çizim alanı dışında kaldırır. */
  const imleciKoy = (svg: SVGSVGElement, clientX: number) => {
    const r = svg.getBoundingClientRect();
    const px = ((clientX - r.left) / r.width) * W;
    if (px < m.l || px > W - m.r) {
      setImlec(null);
      return;
    }
    const i = Math.round(((px - m.l) / (W - m.l - m.r)) * (seri.length - 1));
    setImlec(Math.min(seri.length - 1, Math.max(0, i)));
  };
  const hareket = (e: MouseEvent<SVGSVGElement>) => imleciKoy(e.currentTarget, e.clientX);

  // İşaretçi türü her basışta güncellenir; çubuk dışına basılınca açık
  // ipucu kapanır. Dokunmatikte boş yere dokunuş o günün ipucunu açar
  // (fare bunu zaten hareketle yapıyor).
  const bas = (e: ReactPointerEvent<SVGSVGElement>) => {
    isaretci.current = e.pointerType;
    if ((e.target as Element).closest("a")) return;
    sifirla();
    if (e.pointerType !== "mouse") imleciKoy(e.currentTarget, e.clientX);
  };
  /** Dokunmatikte ilk dokunuş ipucu, ikincisi bağlantı. */
  const ikiAsama = (anahtar: string, goster: () => void) => (e: MouseEvent<HTMLAnchorElement>) => {
    const dokunma = isaretci.current === "touch" || isaretci.current === "pen";
    if (!dokunma || dokunulan.current === anahtar) return;
    e.preventDefault();
    dokunulan.current = anahtar;
    goster();
    setDokunmali(true);
  };
  const fareyle = (f: () => void) => (e: ReactPointerEvent) => {
    if (e.pointerType === "mouse") f();
  };

  const ai = aktifIs === null ? null : isler[aktifIs];
  const gn = ai === null && imlec !== null ? seri[imlec] : null;
  const gnCiro = gn && gn.ciro !== null ? ciroBasamagi(basamaklar, gn.t) : null;
  // Mavi çizginin o gün inişi: bir önceki yılın 12 ayını dolduran işler.
  const gnCikan = gn && imlec !== null ? gunDegisimi(seri, imlec, oncekiYil).cikan : [];
  const ipucuX = ai ? x(ai.t) : gn ? x(gn.t) : 0;
  const ipucuY = ai ? y(ai.tl) : gn ? y(Math.max(gn.duyurulan, Math.min(gn.ciro ?? 0, ust))) : 0;
  const ipucuAlt = ipucuY < 100;

  return (
    <>
      {odakAnlamli && (
        <div className="olcek-sec" role="group" aria-label="Dikey ölçek">
          <button type="button" aria-pressed={!odak} onClick={() => setOdak(false)}>
            Ciroya göre
          </button>
          <button type="button" aria-pressed={odak} onClick={() => setOdak(true)}>
            İşlere odaklan
          </button>
        </div>
      )}
      <div className="grafik" ref={kap}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="group"
          aria-labelledby={baslikId}
          onMouseMove={hareket}
          onMouseLeave={() => setImlec(null)}
          onPointerDown={bas}
          onKeyDown={() => {
            isaretci.current = "klavye";
          }}
        >
          <defs>
            <clipPath id={klipId}>
              <rect x={m.l} y={m.t - 1} width={W - m.l - m.r} height={y(0) - m.t + 2} />
            </clipPath>
          </defs>
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
          {sagUst && (
            <text x={W - m.r} y={m.t - 12} textAnchor="end" className="sag-ust">
              {sagUst}
            </text>
          )}
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
                onPointerEnter={fareyle(ac)}
                onPointerLeave={fareyle(kapat)}
                onFocus={ac}
                onBlur={() => {
                  kapat();
                  dokunulan.current = null;
                  setDokunmali(false);
                }}
                onClick={ikiAsama(`i${i}`, ac)}
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
              clipPath={odakta ? `url(#${klipId})` : undefined}
            />
          )}
          <path
            d={duyuruYolu}
            fill="none"
            style={{ stroke: "var(--p-duyuru)" }}
            strokeWidth={2.75}
            strokeLinejoin="round"
          />
          {etiketler.map((e) => (
            <text key={e.i} x={e.x} y={e.y} textAnchor="middle" className="yazi-acik">
              {e.metin}
            </text>
          ))}
          {raporlar.map((r) => (
            <text key={`${r.x}-${r.metin}`} x={r.x} y={r.y} className="rapor-etiket">
              {r.metin}
            </text>
          ))}
          <circle
            cx={x(son.t)}
            cy={noktaEv}
            r={5}
            style={{ fill: "var(--p-duyuru)", stroke: "var(--plaka)" }}
            strokeWidth={2.5}
          />
          {noktaEc !== null &&
            (sonCiroUstte ? (
              // Ölçeğin üstünde: çizim alanının tepesinde yukarı ok.
              <path
                d={`M${x(son.t) - 5},${m.t + 4}L${x(son.t)},${m.t - 4}L${x(son.t) + 5},${m.t + 4}Z`}
                style={{ fill: "var(--p-ciro)" }}
              />
            ) : (
              <circle
                cx={x(son.t)}
                cy={noktaEc}
                r={4.5}
                style={{ fill: "var(--p-ciro)", stroke: "var(--plaka)" }}
                strokeWidth={2.5}
              />
            ))}
          {!dar && (
            <>
              <text x={x(son.t) + 11} y={evY} className="uc-etiket" style={{ fill: "var(--p-duyuru)" }}>
                {birimde(son.duyurulan)} {birim.kisa}
              </text>
              {son.ciro !== null && ecY !== null && (
                <text x={x(son.t) + 11} y={ecY} className="uc-etiket" style={{ fill: "var(--p-ciro)" }}>
                  {sonCiroUstte ? `${ciroMetni(son.ciro)} ciro ↑` : `${birimde(son.ciro)} ${birim.kisa} ciro`}
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
        {(ai || gn) && (
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
                {dokunmali && (
                  <>
                    <br />
                    <span className="soluk">Kanıt sayfası için bir kez daha dokunun.</span>
                  </>
                )}
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
                  {gnCikan.length > 0 && (
                    <>
                      <br />
                      <span className="soluk">
                        12 ayını doldurup hesaptan çıkan:{" "}
                        {gnCikan.map((is) => `${tamGun(is.t)} duyurusu, ${buyukTl(is.tl)}`).join("; ")}
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
