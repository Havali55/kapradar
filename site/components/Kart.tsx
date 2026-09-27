"use client";

import { useEffect, useRef } from "react";
import type { Bildirim } from "@/lib/veri";
import { ozetMetni } from "@/lib/anasayfa";
import { gosterilenKalemler } from "@/lib/hikaye";
import { KADEME_ADI, buyukTl, gunAy, istanbulGunu, kalemTutari, yuzdeIyelik } from "@/lib/bicim";
import { oranRengi } from "@/lib/skor";
import Cetvel from "./Cetvel";

const SAAT = new Intl.DateTimeFormat("tr-TR", {
  timeZone: "Europe/Istanbul",
  hour: "2-digit",
  minute: "2-digit",
});

/**
 * Akış satırı. Hisse sayfasındaki iş listesiyle aynı dil (site v3): solda
 * saat, ortada ne ve kiminle, sağda asıl para birimiyle tutar ve şirketin
 * cirosuna göre büyüklük; cetvel her satırda aynı ölçekte.
 *
 * Satırda yalnız her iki yılın verisinde de ayakta kalan ve herkesin
 * okuyabileceği olgular var (2026-09-24 sadeleştirmesi): büyüklük (ciroya
 * oran), karşı tarafın adı ya da "adı verilmemiş", bildirim sıklığı
 * (sayım, tepki iddiası yok). Tahta ve tepki paneli bilerek satırda yok:
 * kırmızı/yeşil bir yüzde tahmin gibi okunur; ikisi de ayrıntıda.
 *
 * Satır bir `article`; tıklanabilir alan içindeki tek butonun ::after
 * katmanı. Böylece hem tüm yüzey tıklanabiliyor hem de klavyeyle tek
 * odak durağı oluyor.
 */
export default function Kart({
  bildirim: b,
  onAc,
  imlec = false,
  gunlu = true,
}: {
  bildirim: Bildirim;
  onAc: () => void;
  /** J/K imleci bu satırda mı — vurgulanır ve görünür alana kaydırılır. */
  imlec?: boolean;
  /** Liste günlere bölünmüşse saat, değilse gün yazılır. */
  gunlu?: boolean;
}) {
  const ref = useRef<HTMLElement>(null);
  const ozet = ozetMetni(b);
  const kalemler = gosterilenKalemler(b.tutarlar);

  useEffect(() => {
    // Yapışkan başlık ve süzgeç çubuğunun altında kalmaması için satırın
    // scroll-margin-top'u var (globals.css .akis-satir).
    if (imlec) ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [imlec]);

  const sinif = ["akis-satir", imlec && "imlec", b.oncedenDuyuruldu && "tekrar"]
    .filter(Boolean)
    .join(" ");

  return (
    <article ref={ref} className={sinif}>
      <time className="as-zaman" dateTime={b.yayin_zamani}>
        {gunlu ? (
          SAAT.format(new Date(b.yayin_zamani))
        ) : (
          <>
            {gunAy(b.yayin_zamani)}
            <small>{b.yayin_zamani.slice(0, 4)}</small>
          </>
        )}
      </time>

      <div className="as-ne">
        <div className="as-kim">
          <button type="button" className="as-ac" onClick={onAc}>
            <span className="tk">{b.ticker}</span>
            <span className="gizli-metin"> — {ozet} ayrıntısını aç</span>
          </button>
          <span className="unvan">{b.sirket}</span>
        </div>
        <p className="as-ozet">{ozet}</p>
        <p className="as-alt">
          <Kiminle b={b} />
          {b.bildirim_sikligi !== null && (
            <span className="as-siklik">Son 12 ayda {b.bildirim_sikligi}. iş duyurusu</span>
          )}
        </p>
        {b.oncedenDuyuruldu ? (
          <span className="isaret">
            <b>Tekrar</b>
            {b.onceki_yayin ? `ilk duyuru ${istanbulGunu(b.onceki_yayin)}; ` : ""}bir kez sayılır
          </span>
        ) : b.guncelleme_mi ? (
          <span className="isaret">
            <b>Güncelleme</b>önceki bir duyurunun devamı
          </span>
        ) : null}
      </div>

      <div className="as-tutar">
        {kalemler[0] ? (
          <b>
            {kalemTutari(kalemler[0].deger, kalemler[0].para_birimi)}
            {kalemler.length > 1 && ` +${kalemler.length - 1}`}
          </b>
        ) : b.tutar_gizli ? (
          <span>tutar açıklanmadı</span>
        ) : null}
        {/* Asıl para birimi TL ise TL karşılığı aynı sayıyı ikinci kez yazardı. */}
        {b.net_tutar_tl !== null && kalemler[0]?.para_birimi !== "TRY" && (
          <span>{buyukTl(b.net_tutar_tl)}</span>
        )}
      </div>

      <div className="olc">
        <Buyukluk b={b} />
      </div>
    </article>
  );
}

function Buyukluk({ b }: { b: Bildirim }) {
  if (b.ciro_orani !== null && b.oncedenDuyuruldu) {
    // Aynı iş daha önce aynı tutarla duyuruldu: oran bilgi olarak kalır,
    // kademe ve renk ikinci kez verilmez.
    return (
      <>
        <span className="deger">
          cirosunun <b>{yuzdeIyelik(b.ciro_orani, 1)}</b>
        </span>
        <span className="deger">önceden duyurulan iş</span>
      </>
    );
  }
  if (b.ciro_orani !== null && b.kademe) {
    return (
      <>
        <span className="deger">
          cirosunun{" "}
          <b style={{ color: oranRengi(b.ciro_orani) }}>{yuzdeIyelik(b.ciro_orani, 1)}</b>
        </span>
        <Cetvel oran={b.ciro_orani} />
        <span className={`kademe kademe-${b.kademe}`}>
          {b.kademe === "rutin" ? "Rutin iş" : KADEME_ADI[b.kademe]}
        </span>
      </>
    );
  }
  // Büyüklük yoksa sebebi tek cümle: uydurma bir büyüklük göstermiyoruz.
  const neden =
    b.elle_karar === "skorsuz"
      ? "Tutar şirketin geliri olarak okunamadı; ayrıntıda"
      : b.tutar_gizli
        ? "Şirket tutarı açıklamadı"
        : b.net_tutar_tl === null
          ? "Tutar metinden okunamadı"
          : "Şirketin cirosu henüz bilinmiyor";
  return (
    <>
      <span className="deger">büyüklük bilinmiyor</span>
      <span className="as-neden">{neden}</span>
    </>
  );
}

/**
 * Karşı taraf. Adı açıksa adın kendisi; değilse "adı verilmemiş" ve —
 * şirket bir tanım yazdıysa — o tanım, çünkü "Yurt dışı yerleşik" gibi
 * bir ifade de bilgi. Tek noktalık ya da harfsiz değerler gösterilmiyor.
 */
function Kiminle({ b }: { b: Bildirim }) {
  const tanim =
    b.karsi_taraf && /[A-Za-zÇĞİÖŞÜçğıöşü]{3}/.test(b.karsi_taraf) ? b.karsi_taraf : null;
  if (b.karsiTarafAcik && tanim) {
    return (
      <span className="as-karsi">
        Karşı taraf: <strong title={tanim}>{tanim}</strong>
      </span>
    );
  }
  return (
    <span
      className="as-karsi as-gizli"
      title="Şirket karşı tarafın adını vermemiş; iş bağımsız olarak doğrulanamıyor."
    >
      Karşı tarafın adı verilmemiş
      {tanim && <span className="as-tanim"> · {tanim}</span>}
    </span>
  );
}
