"use client";

import { useEffect, useRef } from "react";
import type { Bildirim } from "@/lib/veri";
import { fOran, oranRengi, tahtaRenk } from "@/lib/skor";
import { KADEME_ADI, gecenSure, yuzdeIyelik } from "@/lib/bicim";

// oranRengi / tahtaRenk lib/skor.ts'te — hem istemci bileşenleri
// hem sunucuda render edilen /kap sayfası kullanıyor.
export { oranRengi, tahtaRenk };

/**
 * Akış kartı — yatırımcının dört sorusu, jargon yok.
 *
 * Her satır bir bulguya dayanıyor (docs/arastirma, Adım 16 + 16b):
 * büyüklük ciroya oranla ölçülür; gizli karşı taraf ve güncelleme daha
 * az güvenilir; tedbirli tahtada fiyat habere değil oynaklığa bağlı;
 * sık bildirim yapan şirkette tepki sönük. Tepki paneli bilerek kartta
 * YOK: tepki öngörülemiyor ve karttaki kırmızı/yeşil bir yüzde tahmin
 * gibi okunur. Sayılar, formül ve panel detayda (`BildirimDetayi`).
 *
 * Kart bir `article`; tıklanabilir alan içindeki tek butonun ::after
 * katmanı. Böylece hem tüm yüzey tıklanabiliyor hem de klavyeyle tek
 * odak durağı oluyor.
 */
export default function Kart({
  bildirim: b,
  onAc,
  imlec = false,
}: {
  bildirim: Bildirim;
  onAc: () => void;
  /** J/K imleci bu kartta mı — vurgulanır ve görünür alana kaydırılır. */
  imlec?: boolean;
}) {
  const ref = useRef<HTMLElement>(null);
  const renk = oranRengi(b.ciro_orani);

  useEffect(() => {
    if (imlec) ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [imlec]);

  return (
    <article ref={ref} className={`kart${imlec ? " kart-imlec" : ""}`}>
      <span className="kart-ray" style={{ background: renk }} aria-hidden="true" />
      <div className="kart-ic">
        <div className="kart-ust">
          <button type="button" className="kart-ac" onClick={onAc}>
            <span className="kart-ticker mono">{b.ticker}</span>
            <span className="gizli-metin">
              {" "}
              — {b.is_tanimi ?? "bildirim"} ayrıntısını aç
            </span>
          </button>
          <span className="kart-sirket">{b.sirket}</span>
          <span className="kart-bos" />
          <time className="kart-zaman mono" dateTime={b.yayin_zamani}>
            {gecenSure(b.yayin_zamani)}
          </time>
        </div>

        <p className="kart-is">{b.is_tanimi ?? "Yeni iş ilişkisi"}</p>

        <dl className="dort-soru">
          <div>
            <dt>Ne kadar büyük?</dt>
            <dd>
              <Buyukluk b={b} renk={renk} />
            </dd>
          </div>
          <div>
            <dt>Bilgi ne kadar net?</dt>
            <dd className="netlik">
              <span className="etiket">
                Karşı taraf {b.karsi_taraf ? "açık" : "gizli"}
              </span>
              <span className="etiket">
                Tutar{" "}
                {b.tutar_gizli ? "gizli" : b.net_tutar_tl === null ? "belirsiz" : "açık"}
              </span>
              <span className="etiket">
                {b.guncelleme_mi ? "Güncelleme bildirimi" : "İlk bildirim"}
              </span>
            </dd>
          </div>
          <div>
            <dt>Fiyata bakmak anlamlı mı?</dt>
            <dd>
              <Tahta tahta={b.tahta} />
            </dd>
          </div>
          <div>
            <dt>Şirket bunu sık yapıyor mu?</dt>
            <dd>
              {b.bildirim_sikligi !== null
                ? `Son 12 ayda ${b.bildirim_sikligi}. iş bildirimi`
                : "—"}
            </dd>
          </div>
        </dl>
      </div>
    </article>
  );
}

function Buyukluk({ b, renk }: { b: Bildirim; renk: string }) {
  if (b.ciro_orani !== null && b.kademe) {
    const ad = b.kademe === "rutin" ? "Rutin iş" : KADEME_ADI[b.kademe];
    return (
      <span className="buyukluk">
        <strong>
          Cirosunun {yuzdeIyelik(b.ciro_orani)} · {ad}
        </strong>
        <span className="buyukluk-cubuk" aria-hidden="true">
          <span
            style={{ width: `${fOran(b.ciro_orani) * 100}%`, background: renk }}
          />
        </span>
      </span>
    );
  }
  // Skor yoksa sebebi tek cümle: uydurma bir büyüklük göstermiyoruz.
  const neden = b.tutar_gizli
    ? "Şirket tutarı açıklamadı"
    : b.net_tutar_tl === null
      ? "Tutar metinden okunamadı"
      : "Şirketin cirosu henüz bilinmiyor";
  return <span className="skorsuz">{neden} · skor yok</span>;
}

const TAHTA_CUMLESI: Record<string, string> = {
  tedbirli: "⚠ Tedbirli tahta: fiyat hareketi bu haberle ilgili olmayabilir",
  hareketli: "Hareketli tahta: fiyat zaman zaman sert oynuyor",
  temiz: "Temiz tahta: son dönemde olağandışı oynaklık yok",
};

function Tahta({ tahta }: { tahta: string | null }) {
  if (!tahta) return <span className="skorsuz">Tahta durumu hesaplanamadı</span>;
  return (
    <span className="tahta-cumle" style={{ color: `var(--${tahtaRenk(tahta)})` }}>
      {TAHTA_CUMLESI[tahta]}
    </span>
  );
}
