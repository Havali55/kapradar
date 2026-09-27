import Link from "next/link";
import { gunAy, yuzdeIyelik } from "@/lib/bicim";
import { ozetMetni } from "@/lib/anasayfa";
import type { AnaSatir } from "@/lib/veri";
import Cetvel from "./Cetvel";

/** Son bildirimler satırı: gün, ticker, özet, ciro oranı ve cetvel. */
export default function IsSatiri({ s }: { s: AnaSatir }) {
  const tekrar = s.onceki_tur === "ayni_is";
  return (
    <Link className="is-satiri" href={`/kap/${s.kap_id}`}>
      <span className="zm">{gunAy(s.yayin_zamani)}</span>
      <span className="tk">{s.ticker}</span>
      <span className="oz">{ozetMetni(s)}</span>
      <span className="olc">
        {s.ciro_orani !== null && !tekrar ? (
          <>
            <span className="deger">
              cirosunun <b>{yuzdeIyelik(s.ciro_orani, 1)}</b>
            </span>
            <Cetvel oran={s.ciro_orani} />
          </>
        ) : (
          <span className="deger">{tekrar ? "önceden duyurulan iş" : "büyüklük bilinmiyor"}</span>
        )}
      </span>
    </Link>
  );
}
