import type { Metadata } from "next";
import Link from "next/link";
import Akis from "@/components/Akis";
import { bildirimleriGetir, ozetCikar, piyasaBandiGetir } from "@/lib/veri";
import { gunEtiketi, isaretliYuzde, kisaTarih, sayi, yuzde, yuzdeIyelik } from "@/lib/bicim";

// Veri hattı toplu koşuyor; saatlik tazeleme yeterli.
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Bildirim akışı",
  description:
    "Borsa İstanbul yeni iş ilişkisi bildirimlerinin süzgeçli akışı; her iş şirketin son 12 aylık cirosuna göre boyutlandırılmış.",
};

export default async function AkisSayfasi() {
  const [bildirimler, bant] = await Promise.all([
    bildirimleriGetir(),
    piyasaBandiGetir(),
  ]);
  const ozet = ozetCikar(bildirimler);

  const bilinmeyen = (ozet.toplam - ozet.skorlu) / Math.max(1, ozet.toplam);

  return (
    <>
      <main className="govde">
        <div className="baslik-blok">
          {/* "CANLI" demiyoruz: veri günde bir toplu koşuyla geliyor. Satır
              verinin hangi tarihe kadar geldiğini söylüyor. */}
          <p className="baslik-ust mono">
            BİLDİRİM AKIŞI
            {ozet.sonBildirim &&
              ` · SON BİLDİRİM ${gunEtiketi(ozet.sonBildirim).toLocaleUpperCase("tr")}`}
          </p>
          <h1>Yeni iş ilişkisi bildirimleri</h1>
          <p>
            Her satır bir iş duyurusu: ne, kiminle ve şirketin son 12 aylık
            cirosuna göre ne kadar büyük. Satıra tıklayınca hesabın tamamı
            açılır. Fiyat tahmini üretilmez.
          </p>
        </div>

        {/* Künye: arşivin kendisi hakkında dört olgu. "Son 24 saat" gibi bir
            sayaç yok; arşiv toplu yüklendiği için çoğu zaman 0 derdi. */}
        <dl className="akis-kunye">
          <div>
            <dt>yayında bildirim</dt>
            <dd>{sayi(ozet.toplam, 0)}</dd>
          </div>
          <div>
            <dt>ortanca iş, cirosunun</dt>
            <dd className="mavi">
              {ozet.medyanOran === null ? "—" : yuzdeIyelik(ozet.medyanOran, 1)}
            </dd>
            <dd className="alt">büyüklüğü bilinen {sayi(ozet.skorlu, 0)} bildirimde</dd>
          </div>
          <div>
            <dt>sakin tahtadan</dt>
            <dd>{ozet.temizOran === null ? "—" : yuzde(ozet.temizOran, 0)}</dd>
            <dd className="alt">bildirim gününde devre kesici seyrek, tedbir yok</dd>
          </div>
          <div>
            <dt>büyüklüğü bilinmeyen</dt>
            <dd>{yuzde(bilinmeyen, 0)}</dd>
            <dd className="alt">tutar ya da ciro yok; süzgeçten açılır</dd>
          </div>
        </dl>

        {bant && (
          // Bağlam: piyasanın geneli. Olgu + tarih, yorum yok.
          <p className="piyasa-satiri">
            Piyasa bağlamı, son 5 seans ({kisaTarih(bant.son_tarih)} itibarıyla): eşit
            ağırlıklı BIST{" "}
            <b className="mono">{bant.ew_5s !== null ? isaretliYuzde(bant.ew_5s, 1) : "—"}</b> ·
            XU100{" "}
            <b className="mono">
              {bant.xu100_5s !== null ? isaretliYuzde(bant.xu100_5s, 1) : "—"}
            </b>
            {bant.tasfiye_tarihi && (
              <>
                {" "}
                · SPK {kisaTarih(bant.tasfiye_tarihi)} tarihinde{" "}
                {bant.tasfiye_sirket_sayisi} portföy şirketinin fonlarını tasfiyeye aldı.
              </>
            )}
          </p>
        )}

        <Akis bildirimler={bildirimler} />

        <p className="dipnot">
          KAP·RADAR yatırım tavsiyesi vermez; tekil getiri tahmini üretmez,
          yalnızca geçmiş bildirimlerin gözlenmiş dağılımını raporlar. Büyüklük
          oranları kamuya açık KAP metinleri ve finansal tablolar üzerinden
          hesaplanır. <Link href="/metodoloji">Yöntemin tamamı ve sınırları</Link>.
        </p>
      </main>
    </>
  );
}
