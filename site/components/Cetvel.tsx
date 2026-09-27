import { MEGA_ORAN, ONEMLI_ORAN, fOran, oranRengi } from "@/lib/skor";

/**
 * Ölçek cetveli: skorun log f(r) ekseninde işin yeri, %5 ve %15 çentikli.
 * İki işin büyüklüğü göz kararı karşılaştırılabilsin diye her satırda aynı
 * ölçek. Sayının kendisi yanında yazılı; cetvel ekran okuyucudan gizli.
 */
export default function Cetvel({ oran }: { oran: number }) {
  return (
    <span className="cetvel" aria-hidden="true">
      <span className="cetvel-ray" />
      <span
        className="cetvel-dolu"
        style={{ width: `${(fOran(oran) * 100).toFixed(1)}%`, background: oranRengi(oran) }}
      />
      {[ONEMLI_ORAN, MEGA_ORAN].map((v) => (
        <span key={v} className="cetvel-centik" style={{ left: `${(fOran(v) * 100).toFixed(1)}%` }} />
      ))}
    </span>
  );
}
