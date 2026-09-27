"use client";

import Link from "next/link";
import { useState } from "react";
import { eslesir } from "@/lib/arama";
import { isaretliYuzde, istanbulGunu, kat } from "@/lib/bicim";
import { dizinSirala, type DizinAnahtari, type DizinSatiri } from "@/lib/hikaye";
import { donemAdi } from "@/lib/soz";

export type DizinOgesi = DizinSatiri & {
  tahtaAd: string | null;
  tahtaRenk: string | null;
};

const SUTUNLAR: { k: DizinAnahtari; ad: string; sayi: boolean; ipucu?: string }[] = [
  { k: "ticker", ad: "Hisse", sayi: false },
  { k: "adet12", ad: "Son 12 ayda iş", sayi: true, ipucu: "Büyüklüğü hesaplanan, tekrar olmayan işler" },
  { k: "sonIs", ad: "Son bildirim", sayi: true },
  { k: "kat", ad: "Duyurulan / ciro", sayi: true, ipucu: "Son 12 ayda duyurulan TL ÷ son 12 aylık ciro" },
  { k: "buyume", ad: "Reel ciro büyümesi", sayi: true, ipucu: "Son dönem raporu, enflasyondan arındırılmış" },
];

/** 144 şirketin sıralanabilir, süzülebilir dizini. Telefonda kart listesi. */
export default function HisseDizini({ satirlar }: { satirlar: DizinOgesi[] }) {
  const [sorgu, setSorgu] = useState("");
  const [sira, setSira] = useState<{ k: DizinAnahtari; azalan: boolean }>({
    k: "sonIs",
    azalan: true,
  });
  const gorunen = dizinSirala(
    satirlar.filter((s) => eslesir({ t: s.ticker, s: s.sirket }, sorgu)),
    sira.k,
    sira.azalan,
  );
  const sirala = (k: DizinAnahtari) =>
    setSira((o) => (o.k === k ? { k, azalan: !o.azalan } : { k, azalan: k !== "ticker" }));

  return (
    <>
      <div className="dizin-ust">
        <input
          type="search"
          className="dizin-suzgec"
          placeholder="Süz: ticker ya da unvan"
          aria-label="Hisseleri süz"
          autoComplete="off"
          spellCheck={false}
          value={sorgu}
          onChange={(e) => setSorgu(e.target.value)}
        />
        <span className="dizin-sayi" aria-live="polite">
          {gorunen.length} / {satirlar.length} şirket
        </span>
      </div>
      <table className="dizin">
        <thead>
          <tr>
            {SUTUNLAR.map((c) => (
              <th
                key={c.k}
                scope="col"
                className={c.sayi ? "sayi" : undefined}
                aria-sort={sira.k === c.k ? (sira.azalan ? "descending" : "ascending") : "none"}
                title={c.ipucu}
              >
                <button type="button" onClick={() => sirala(c.k)}>
                  {c.ad}
                  <span aria-hidden="true" className="sira-isareti">
                    {sira.k === c.k ? (sira.azalan ? " ↓" : " ↑") : ""}
                  </span>
                </button>
              </th>
            ))}
            <th scope="col" className="dizin-tahta-bas">
              Tahta
            </th>
          </tr>
        </thead>
        <tbody>
          {gorunen.map((s) => (
            <tr key={s.ticker}>
              <td data-et="Hisse">
                <Link href={`/hisse/${s.ticker}`} className="dizin-hisse">
                  <b className="mono">{s.ticker}</b>
                  <span className="unvan">{s.sirket}</span>
                </Link>
              </td>
              <td data-et="Son 12 ayda iş" className="sayi">
                {s.adet12}
              </td>
              <td data-et="Son bildirim" className="sayi">
                {istanbulGunu(s.sonIs)}
              </td>
              <td data-et="Duyurulan / ciro" className="sayi">
                {s.kat !== null ? kat(s.kat) : "—"}
              </td>
              <td
                data-et="Reel ciro büyümesi"
                className="sayi"
                title={
                  s.nominal
                    ? "Rapor enflasyona göre yeniden ifade edilmemiş; büyüme nominal"
                    : s.buyumeDonemi
                      ? donemAdi(s.buyumeDonemi)
                      : undefined
                }
              >
                {s.buyume !== null ? isaretliYuzde(s.buyume, 1) : "—"}
              </td>
              <td data-et="Tahta">
                {s.tahtaAd ? (
                  <span className={`durum durum-${s.tahtaRenk}`}>{s.tahtaAd}</span>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {gorunen.length === 0 && (
        <p className="isler-bos">Bu adla bildirim yok; arşivde {satirlar.length} şirket var.</p>
      )}
    </>
  );
}
