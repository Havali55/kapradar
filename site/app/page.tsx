import Link from "next/link";
import Akis from "@/components/Akis";
import { bildirimleriGetir, ozetCikar } from "@/lib/veri";
import { gunEtiketi, yuzde } from "@/lib/bicim";

// Veri hattı toplu koşuyor; saatlik tazeleme yeterli.
export const revalidate = 3600;

export default async function AnaSayfa() {
  const bildirimler = await bildirimleriGetir();
  const ozet = ozetCikar(bildirimler);

  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo">
            <span className="logo-ad mono">
              KAP<i>·</i>RADAR
            </span>
            <span className="logo-alt mono">BIST · YENİ İŞ İLİŞKİSİ</span>
          </Link>
          {/* "CANLI" demiyoruz: canlı poller henüz yok ve arşiv toplu
              yükleniyor. Rozet gerçekte ne olduğunu söylüyor — verinin
              hangi tarihe kadar geldiğini. */}
          <span className="canli mono" title="Arşivdeki en yeni bildirim">
            <span className="canli-nokta" aria-hidden="true" />
            {ozet.sonBildirim
              ? `ARŞİV · ${gunEtiketi(ozet.sonBildirim).toLocaleUpperCase("tr")}`
              : "ARŞİV"}
          </span>
          <div className="bas-bos" />
          <Link href="/film" className="bag">
            Filmi izle ▸
          </Link>
          <Link href="/profil" className="bag">
            Profil
          </Link>
          <Link href="/proje-hakkinda" className="bag">
            Proje hakkında
          </Link>
          <Link href="/metodoloji" className="bag bag-koyu">
            Metodoloji
          </Link>
        </div>
      </header>

      <main className="govde">
        <div className="baslik-blok">
          <p className="baslik-ust mono">BİLDİRİM AKIŞI</p>
          <h1>Yeni iş ilişkisi bildirimleri</h1>
          <p>
            Her haberde dört soru: iş şirket için ne kadar büyük, bilgi ne
            kadar net, fiyata bakmak anlamlı mı, şirket bunu sık yapıyor mu.
            Ayrıntı ve hesabın tamamı karta tıklayınca açılır. Fiyat tahmini
            üretilmez.
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
            <div
              className="olcu-deger mono"
              style={{ color: "var(--mavi-k)" }}
            >
              {ozet.medyanOran === null ? "—" : yuzde(ozet.medyanOran, 1)}
            </div>
            <div className="olcu-alt">
              sözleşme / son 12 ay ciro · {ozet.skorlu} bildirim
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">TEMİZ TAHTA</div>
            <div className="olcu-deger mono" style={{ color: "var(--yes)" }}>
              {ozet.temizOran === null ? "—" : yuzde(ozet.temizOran, 0)}
            </div>
            <div className="olcu-alt">devre kesici seyrek, tedbir yok</div>
          </div>
          {/* "Son 24 saat" yerine bu: arşiv toplu yüklendiği için o sayaç
              çoğu zaman 0 gösterirdi. Skorsuz oranı ise ürünün duruşunu
              anlatan kalıcı bir ölçü. */}
          <div className="olcu">
            <div className="olcu-et mono">SKOR ÜRETİLMEDİ</div>
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
          yalnızca geçmiş bildirimlerin gözlenmiş dağılımını raporlar. Skorlar
          kamuya açık KAP metinleri ve finansal tablolar üzerinden hesaplanır.{" "}
          <Link href="/metodoloji">Yöntemin tamamı ve sınırları</Link>.
        </p>
      </main>
    </>
  );
}
