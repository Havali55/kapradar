import { buyukTl } from "@/lib/bicim";
import type { KiminleSatiri } from "@/lib/hikaye";

/** Son 12 ayın sayılan işleri karşı tarafa göre; adı verilmeyenler sonda. */
export default function Kiminle({ satirlar }: { satirlar: KiminleSatiri[] }) {
  const maks = Math.max(1, ...satirlar.map((s) => s.tl));
  return (
    <section className="yan-kutu" aria-labelledby="kim-bas">
      <span className="ust-yazi">Son 12 ay</span>
      <h3 id="kim-bas">Kiminle iş yapıyor?</h3>
      {satirlar.length === 0 ? (
        <p className="yan-bos">Son 12 ayda büyüklüğü hesaplanabilen iş yok.</p>
      ) : (
        <ul className="kim">
          {satirlar.map((s) => (
            <li key={s.ad ?? "—"} className={s.ad === null ? "gizli" : undefined}>
              <span className="kim-ust">
                <span>{s.ad ?? "Adı verilmemiş"}</span>
                <span className="mono">
                  {buyukTl(s.tl)} · {s.adet} iş
                </span>
              </span>
              <span className="kim-cubuk" aria-hidden="true">
                <i style={{ width: `${((s.tl / maks) * 100).toFixed(1)}%` }} />
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
