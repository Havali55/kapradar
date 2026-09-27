import Link from "next/link";
import { KADEME_ADI, buyukTl, gunAy, yuzdeIyelik } from "@/lib/bicim";
import { karsiTarafMetni, ozetMetni } from "@/lib/anasayfa";
import { buyuklukBul, oranRengi, type Kademe } from "@/lib/skor";
import type { AnaSatir } from "@/lib/veri";
import Cetvel from "./Cetvel";

/**
 * Ana sayfanın "en büyük üç iş" kartı; kanıt sayfasına gider. İçerik
 * `span`: bağlantı satır içi başlıyor, düzeni CSS `display: grid` kuruyor.
 */
export default function IsKarti({ s }: { s: AnaSatir }) {
  const oran = s.ciro_orani as number;
  const kademe = buyuklukBul(oran) as Kademe;
  const karsi = karsiTarafMetni(s);
  return (
    <Link className="is-karti" href={`/kap/${s.kap_id}`}>
      <span className="is-karti-ust">
        <span className="tk">{s.ticker}</span>
        <span className="sr unvan">{s.sirket}</span>
        <span className="zm">{gunAy(s.yayin_zamani)}</span>
      </span>
      <span className="is-karti-olcu">
        <span className="ne">son 12 aylık cirosunun</span>
        <span className="sayi" style={{ color: oranRengi(oran) }}>
          {yuzdeIyelik(oran, 1)}
        </span>
        <span className={`kademe kademe-${kademe}`}>{KADEME_ADI[kademe]}</span>
      </span>
      <Cetvel oran={oran} />
      <span className="oz">{ozetMetni(s)}</span>
      <span className="dip">
        <span>{karsi ?? "Karşı tarafın adı verilmemiş"}</span>
        {s.net_tutar_tl !== null && <span className="mono">{buyukTl(s.net_tutar_tl)}</span>}
      </span>
    </Link>
  );
}
