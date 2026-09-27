"use client";

import Link from "next/link";
import { useState } from "react";
import { eslesir } from "@/lib/arama";
import { isaretliYuzde, istanbulGunu, kat } from "@/lib/bicim";
import { dizinSirala, type DizinAnahtari, type DizinSatiri, type seansDurumu } from "@/lib/hikaye";
import { donemAdi } from "@/lib/soz";

export type DizinOgesi = DizinSatiri & {
  /** Son 20 seansın durumu; bildirim günündeki tahta değil. */
  seans: ReturnType<typeof seansDurumu>;
  /** Son 20 seansın ortalama |günlük getiri|si; sıralama anahtarı. */
  hareket: number | null;
};

// Bu büyüklükte bir değişim (±%200) çoğu zaman organik büyüme değil:
// TEHOL'un 6A2026 hasılatı bir yılda 59 milyon TL'den 4,6 milyar TL'ye
// çıktı (+%5.785). Değer gösteriliyor, yanında uyarı.
const OLAGANDISI = 2;

const SUTUNLAR: { k: DizinAnahtari; ad: string; sayi: boolean; ipucu?: string }[] = [
  { k: "ticker", ad: "Hisse", sayi: false },
  { k: "adet12", ad: "Son 12 ayda iş", sayi: true, ipucu: "Büyüklüğü hesaplanan, tekrar olmayan işler" },
  { k: "sonIs", ad: "Son bildirim", sayi: true },
  { k: "kat", ad: "Duyurulan / ciro", sayi: true, ipucu: "Son 12 ayda duyurulan TL ÷ son 12 aylık ciro" },
  { k: "buyume", ad: "Reel ciro büyümesi", sayi: true, ipucu: "Son dönem raporu, enflasyondan arındırılmış" },
  {
    k: "hareket",
    ad: "Son 20 seans",
    sayi: false,
    ipucu: "Günlük ortalama hareket, listedeki hisselerin ortasına göre; süren taban/tavan serisi önce",
  },
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
              <td
                data-et="Duyurulan / ciro"
                className="sayi"
                title={s.adet12 === 0 ? "Son 12 ayda büyüklüğü hesaplanan iş yok" : undefined}
              >
                {s.kat !== null && s.adet12 > 0 ? kat(s.kat) : "—"}
              </td>
              <td
                data-et="Reel ciro büyümesi"
                className="sayi"
                title={
                  s.nominal
                    ? "Rapor enflasyona göre yeniden ifade edilmemiş; büyüme nominal"
                    : s.buyume !== null && Math.abs(s.buyume) > OLAGANDISI
                      ? `${s.buyumeDonemi ? donemAdi(s.buyumeDonemi) + ". " : ""}Olağandışı büyük değişim: birleşme, konsolidasyon ya da çok küçük bir karşılaştırma tabanı olabilir; organik büyüme sanılmamalı.`
                      : s.buyumeDonemi
                        ? donemAdi(s.buyumeDonemi)
                        : undefined
                }
              >
                {s.buyume !== null ? isaretliYuzde(s.buyume, 1) : "—"}
                {s.buyume !== null && Math.abs(s.buyume) > OLAGANDISI && (
                  <span className="olagandisi" aria-label="olağandışı">
                    {" "}
                    ⚠
                  </span>
                )}
              </td>
              <td data-et="Son 20 seans" className="dizin-seans">
                {s.seans ? (
                  <>
                    <span className="dizin-hareket mono" title="Günlük ortalama hareket">
                      {s.seans.hareket !== null
                        ? `%${(s.seans.hareket * 100).toFixed(1).replace(".", ",")}`
                        : ""}
                    </span>
                    <span className={`durum durum-${s.seans.renk}`} title={s.seans.aciklama}>
                      {s.seans.kisa}
                    </span>
                  </>
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
