import type { Metadata } from "next";
import Link from "next/link";
import Akis from "@/components/Akis";
import { bildirimleriGetir, ozetCikar, piyasaBandiGetir } from "@/lib/veri";
import { gunEtiketi, isaretliYuzde, kisaTarih, yuzde } from "@/lib/bicim";

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

  return (
    <>
      {bant && (
        // Bağlam katmanı: piyasanın geneli. Olgu + tarih, yorum yok.
        <div className="bant">
          <div className="bant-ic">
            <span className="rozet mono">PİYASA</span>
            <span>
              Son 5 seans ({kisaTarih(bant.son_tarih)} itibarıyla): eşit ağırlıklı
              BIST{" "}
              <strong className="mono">
                {bant.ew_5s !== null ? isaretliYuzde(bant.ew_5s, 1) : "—"}
              </strong>{" "}
              · XU100{" "}
              <strong className="mono">
                {bant.xu100_5s !== null ? isaretliYuzde(bant.xu100_5s, 1) : "—"}
              </strong>
              {bant.tasfiye_tarihi && (
                <>
                  {" "}
                  · SPK {kisaTarih(bant.tasfiye_tarihi)} tarihinde{" "}
                  {bant.tasfiye_sirket_sayisi} portföy şirketinin fonlarını
                  tasfiyeye aldı.
                </>
              )}
            </span>
          </div>
        </div>
      )}

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
            Her haberde üç soru: iş şirket için ne kadar büyük, kiminle
            yapıldı, şirket bunu sık yapıyor mu. Büyüklük, işin tutarının
            şirketin son 12 aylık cirosuna oranıdır. Ayrıntı ve hesabın
            tamamı karta tıklayınca açılır. Fiyat tahmini üretilmez.
          </p>
        </div>

        <div className="olcuum">
          <div className="olcu">
            <div className="olcu-et mono">ARŞİV</div>
            <div className="olcu-deger mono">{ozet.toplam}</div>
            <div className="olcu-alt">yayına hazır bildirim</div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">MEDYAN CİRO ORANI</div>
            <div className="olcu-deger mono" style={{ color: "var(--mavi-k)" }}>
              {ozet.medyanOran === null ? "—" : yuzde(ozet.medyanOran, 1)}
            </div>
            <div className="olcu-alt">
              sözleşme / son 12 ay ciro · {ozet.skorlu} bildirim
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">SAKİN TAHTA</div>
            <div className="olcu-deger mono" style={{ color: "var(--yes)" }}>
              {ozet.temizOran === null ? "—" : yuzde(ozet.temizOran, 0)}
            </div>
            <div className="olcu-alt">devre kesici seyrek, borsa tedbiri yok</div>
          </div>
          {/* "Son 24 saat" yerine bu: arşiv toplu yüklendiği için o sayaç
              çoğu zaman 0 gösterirdi. Skorsuz oranı ise ürünün duruşunu
              anlatan kalıcı bir ölçü. */}
          <div className="olcu">
            <div className="olcu-et mono">BÜYÜKLÜK BİLİNMİYOR</div>
            <div className="olcu-deger mono">
              {yuzde((ozet.toplam - ozet.skorlu) / Math.max(1, ozet.toplam), 0)}
            </div>
            <div className="olcu-alt">
              tutar ya da ciro yok · akışta gizli, filtreden açılır
            </div>
          </div>
        </div>

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
