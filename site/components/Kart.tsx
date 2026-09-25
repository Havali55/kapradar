"use client";

import { useEffect, useRef } from "react";
import type { Bildirim } from "@/lib/veri";
import { fOran, oranRengi } from "@/lib/skor";
import { KADEME_ADI, gecenSure, yuzdeIyelik } from "@/lib/bicim";

/**
 * Akış kartı — üç soru, jargon yok: iş şirket için ne kadar büyük,
 * kiminle yapıldı, şirket bunu sık yapıyor mu.
 *
 * Kartta yalnız her iki yılın verisinde de ayakta kalan ve herkesin
 * okuyabileceği olgular var (2026-09-24 sadeleştirmesi):
 *   - Büyüklük: ciroya oran. Ürünün asıl ölçüsü.
 *   - Kiminle: karşı tarafın ADI ya da "adı verilmemiş". Eskiden üç çip
 *     vardı (karşı taraf açık/gizli, tutar açık, ilk/güncelleme); "tutar
 *     açık" skorlu kartta hep doğru olduğu için bilgi taşımıyordu,
 *     "karşı taraf açık" ise 254 bildirimde yanlıştı ("Uluslararası
 *     Müşteri" gibi tanımlar isim sayılıyordu).
 *   - Sıklık: sayılan olgu, tepki iddiası yok.
 * "Fiyata bakmak anlamlı mı?" satırı kaldırıldı: kart fiyat göstermiyor,
 * dayandığı bulgu (Bulgu 10) örneklem dışında tekrarlanmadı ve son
 * aylarda kartların üçte ikisinde ⚠ çıkıyordu. Tahta bilgisi detayda.
 * Tepki paneli de bilerek kartta yok: karttaki kırmızı/yeşil bir yüzde
 * tahmin gibi okunur.
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
    // Yapışkan başlık ve filtre çubuğunun altında kalmaması için kartın
    // scroll-margin-top'u var (globals.css .kart).
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
            <dt>Kiminle?</dt>
            <dd>
              <Kiminle b={b} />
            </dd>
          </div>
          <div>
            <dt>Şirket bunu sık yapıyor mu?</dt>
            <dd>
              {b.bildirim_sikligi !== null
                ? `Son 12 ayda ${b.bildirim_sikligi}. iş duyurusu`
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
  // Büyüklük yoksa sebebi tek cümle: uydurma bir büyüklük göstermiyoruz.
  const neden = b.tutar_gizli
    ? "Şirket tutarı açıklamadı"
    : b.net_tutar_tl === null
      ? "Tutar metinden okunamadı"
      : "Şirketin cirosu henüz bilinmiyor";
  return <span className="skorsuz">{neden}</span>;
}

/**
 * Karşı taraf. Adı açıksa adın kendisi; değilse "adı verilmemiş" ve —
 * şirket bir tanım yazdıysa — o tanım, çünkü "Yurt dışı yerleşik"
 * gibi bir ifade de bilgi. Tek noktalık ya da harfsiz değerler
 * gösterilmiyor.
 */
function Kiminle({ b }: { b: Bildirim }) {
  const tanim =
    b.karsi_taraf && /[A-Za-zÇĞİÖŞÜçğıöşü]{3}/.test(b.karsi_taraf)
      ? b.karsi_taraf
      : null;
  return (
    <span className="kiminle">
      {b.karsiTarafAcik && tanim ? (
        <span className="kiminle-ad" title={tanim}>
          {tanim}
        </span>
      ) : (
        <span
          className="kiminle-gizli"
          title="Şirket karşı tarafın adını vermemiş; iş bağımsız olarak doğrulanamıyor."
        >
          Adı verilmemiş
          {tanim && <span className="kiminle-tanim"> · {tanim}</span>}
        </span>
      )}
      {b.guncelleme_mi && (
        <span className="etiket" title="Bu duyuru daha önce açıklanmış bir işin güncellemesi.">
          Önceki duyurunun güncellemesi
        </span>
      )}
    </span>
  );
}
