import Link from "next/link";
import { sayi } from "@/lib/bicim";

// Veritabanında olmayan iki sayı, kaynağıyla: kapının kuralları
// `src/kap_radar/cikarim.py` (A1–A7, B1–B6); çıkarım doğruluğu README
// ("47/50 tam doğru"). Kalan sayılar sayfanın sorgusundan.
const KURAL_SAYISI = 13;
const ALTIN_KUME = "50'de 47";

type Props = {
  yayinda: number;
  /** Arşivdeki ilk bildirimin günü, "2 Eylül 2024". */
  ilk: string;
  elleKarar: number;
  ciroluSirket: number;
};

export default function NasilCalisiyor({ yayinda, ilk, elleKarar, ciroluSirket }: Props) {
  return (
    <section className="ana-bolum nasil" aria-labelledby="nasil-bas">
      <div className="nasil-sol">
        <div className="ust-yazi">Bu site nasıl çalışıyor</div>
        <h2 id="nasil-bas">Her iş günü 19:30&apos;da kendi kendine güncellenen bir veri hattı.</h2>
        <p>Hüseyin Dinçer&apos;in projesi. Kararlar yazılı, her sayı kaynağına iniyor.</p>
        <p>
          <Link href="/proje-hakkinda">Nasıl yapıldığını oku →</Link>
        </p>
      </div>
      <ol className="adimlar">
        <li>
          <span className="no">01</span>
          <b>KAP bildirimi okunur</b>
          <span>
            Karşı taraf, tarih ve güncelleme bayrağı KAP&apos;ın yapılandırılmış
            alanlarından; serbest metinden yalnız tutar.
          </span>
          <span className="kanit">
            {sayi(yayinda, 0)} bildirim · ilki {ilk}
          </span>
        </li>
        <li>
          <span className="no">02</span>
          <b>Tutar çıkarılır, kapıdan geçer</b>
          <span>
            Dil modeli tutarı birebir alıntısıyla verir; {KURAL_SAYISI} kural onu
            metne, aritmetiğe ve anlamına karşı sınar. Geçemeyen yayınlanmaz,
            insan karar verir.
          </span>
          <span className="kanit">
            altın kümede {ALTIN_KUME} tam doğru · {elleKarar} elle karar
          </span>
        </li>
        <li>
          <span className="no">03</span>
          <b>Şirketin cirosuna bölünür</b>
          <span>
            O gün açıklanmış son raporlardan, enflasyon düzeltmeli son 12 aylık
            ciro; tutar o günün TCMB kuruyla. Sonradan gelen rapor kullanılmaz.
          </span>
          <span className="kanit">{ciroluSirket} şirketin cirosu, bildirim gününün raporlarından</span>
        </li>
      </ol>
    </section>
  );
}
