"use client";

import Link from "next/link";
import { useState } from "react";
import { KADEME_ADI, buyukTl, yuzdeIyelik } from "@/lib/bicim";
import { aylaraBol, isleriSuz, type Suzgec } from "@/lib/hikaye";
import { ONEMLI_ORAN, buyuklukBul, oranRengi, type Kademe } from "@/lib/skor";
import Cetvel from "./Cetvel";

/** Listenin bir satırı; biçimleme sunucuda yapılıp küçük tutuluyor. */
export type IsOgesi = {
  kap_id: string;
  zaman: string;
  ozet: string;
  karsi: string | null;
  /** Asıl para birimindeki ilk kalem, "44,4 Milyon USD". */
  kalem: string | null;
  kalemEk: number;
  tl: number | null;
  oran: number | null;
  tekrar: boolean;
  guncelleme: boolean;
  duzeltme: boolean;
};

const ILK = 16;
const SUZGECLER: [Suzgec, string][] = [
  ["tum", "Tümü"],
  ["onemli", "Önemli ve üstü"],
  ["acik", "Karşı tarafı belli"],
];
const GUN = new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", day: "numeric" });
const AY_YIL = new Intl.DateTimeFormat("tr-TR", {
  timeZone: "Europe/Istanbul",
  month: "short",
  year: "2-digit",
});

/** Şirketin bütün işleri, yeniden eskiye, aylara bölünmüş. */
export default function IsListesi({ isler }: { isler: IsOgesi[] }) {
  const [suzgec, setSuzgec] = useState<Suzgec>("tum");
  const [hepsi, setHepsi] = useState(false);
  const liste = isleriSuz(isler, suzgec, ONEMLI_ORAN);
  const gorunen = hepsi ? liste : liste.slice(0, ILK);

  return (
    <section className="isler" aria-labelledby="isler-bas">
      <div className="isler-bas">
        <h2 id="isler-bas">Bütün işler</h2>
        <div className="suzgec" role="group" aria-label="İşleri süz">
          {SUZGECLER.map(([k, ad]) => (
            <button
              key={k}
              type="button"
              aria-pressed={suzgec === k}
              onClick={() => {
                setSuzgec(k);
                setHepsi(false);
              }}
            >
              {ad}
            </button>
          ))}
        </div>
      </div>
      {liste.length === 0 && <p className="isler-bos">Bu süzgeçte iş yok.</p>}
      {aylaraBol(liste, gorunen).map((g) => (
        <div key={g.ay}>
          <div className="ay-bas">
            <b>{g.ay}</b>
            <span>{g.adet} iş</span>
          </div>
          {g.isler.map((i) => (
            <Satir key={i.kap_id} i={i} />
          ))}
        </div>
      ))}
      {!hepsi && liste.length > gorunen.length && (
        <button type="button" className="daha" onClick={() => setHepsi(true)}>
          Daha eski {liste.length - gorunen.length} işi göster
        </button>
      )}
    </section>
  );
}

function Satir({ i }: { i: IsOgesi }) {
  const d = new Date(i.zaman);
  const kademe = i.oran !== null ? (buyuklukBul(i.oran) as Kademe) : null;
  return (
    <Link href={`/kap/${i.kap_id}`} className={i.tekrar ? "isl-satir tekrar" : "isl-satir"}>
      <span className="gun">
        {GUN.format(d)}
        <small>{AY_YIL.format(d)}</small>
      </span>
      <span className="ne">
        <span className="ozet">{i.ozet}</span>
        <span className="kimle">
          {i.karsi ? (
            <>
              Karşı taraf: <strong>{i.karsi}</strong>
            </>
          ) : (
            "Karşı tarafın adı verilmemiş"
          )}
        </span>
        {i.tekrar ? (
          <span className="isaret">
            <b>Tekrar</b>aynı iş daha önce duyuruldu; bir kez sayılır
          </span>
        ) : i.duzeltme ? (
          <span className="isaret">
            <b>Düzeltme</b>önceki duyurunun yerini aldı
          </span>
        ) : i.guncelleme ? (
          <span className="isaret">
            <b>Güncelleme</b>önceki bir duyurunun devamı
          </span>
        ) : null}
      </span>
      <span className="tutar">
        {i.kalem && (
          <b>
            {i.kalem}
            {i.kalemEk > 0 && ` +${i.kalemEk}`}
          </b>
        )}
        {i.tl !== null && <span>{buyukTl(i.tl)}</span>}
      </span>
      <span className="olc">
        {i.oran !== null && kademe ? (
          <>
            <span className="deger">
              cirosunun <b style={{ color: oranRengi(i.oran) }}>{yuzdeIyelik(i.oran, 1)}</b>
            </span>
            <Cetvel oran={i.oran} />
            <span className="deger">{KADEME_ADI[kademe]}</span>
          </>
        ) : (
          <span className="deger">büyüklük bilinmiyor</span>
        )}
      </span>
    </Link>
  );
}
