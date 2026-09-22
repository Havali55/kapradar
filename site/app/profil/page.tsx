import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Profil — Hüseyin Dinçer",
  description:
    "Sistem mimarisi, veri hatları ve öngörücü analitik üzerine çalışan bir mühendislik öğrencisi. KAP·RADAR, Calibre ve RouteWise projeleri.",
};

const LINKEDIN =
  "https://www.linkedin.com/in/h%C3%BCseyin-din%C3%A7er-663345247";

export default function Profil() {
  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo">
            <span className="logo-ad mono">
              KAP<i>·</i>RADAR
            </span>
            <span className="logo-alt mono">PROFİL</span>
          </Link>
          <div className="bas-bos" />
          <Link href="/proje-hakkinda" className="bag">
            Proje hakkında
          </Link>
          <Link href="/" className="bag bag-koyu">
            Akışa dön
          </Link>
        </div>
      </header>

      <main className="govde govde-dar yazi">
        <div className="ust-etiket mono">PROFİL</div>

        <div className="profil-bas">
          {/* Kaynak 800×800 PNG (925 KB) idi; 640 px JPEG'e indirildi.
              Ölçü 124 px, yani retina ekranda bile fazlasıyla keskin. */}
          <Image
            src="/huseyin-dincer.jpg"
            alt="Hüseyin Dinçer"
            width={124}
            height={124}
            className="profil-foto"
            priority
          />
          <div className="profil-kimlik">
            <h1>Hüseyin Dinçer</h1>
            <p className="profil-alt">
              Mühendislik ilkeleri ile ölçeklenebilir yazılım mimarisi
              arasındaki boşlukta çalışıyorum: veriyle beslenen ürünler ve
              karmaşık, gerçek dünya problemlerini çözen sistemler.
            </p>
            <div className="profil-meta mono">
              <span>BODRUM, MUĞLA</span>
              <span>BURSA TEKNİK ÜNİVERSİTESİ</span>
              <span>CALIBRESOLVE</span>
            </div>
            <a href={LINKEDIN} target="_blank" rel="noopener noreferrer">
              LinkedIn profili →
            </a>
          </div>
        </div>

        <div className="olcuum">
          <div className="olcu">
            <div className="olcu-et mono">ODAK</div>
            <div className="olcu-deger olcu-kisa">Sistem mimarisi</div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">ODAK</div>
            <div className="olcu-deger olcu-kisa">Öngörücü analitik</div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">ODAK</div>
            <div className="olcu-deger olcu-kisa">Veri hatları</div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">ODAK</div>
            <div className="olcu-deger olcu-kisa">Ürün mühendisliği</div>
          </div>
        </div>

        <section style={{ marginTop: 56 }}>
          <h2 className="mono">01 · YAKLAŞIM</h2>
          <h3>Sayının kaynağına kadar geri izlenebilmesi</h3>
          <p>
            İlgilendiğim şey tek bir modelin ne kadar iyi olduğu değil, bir
            sistemin ürettiği sayının nereden geldiğinin gösterilebilmesi.
            Yüksek hacimli veriyle çalışan hatlarda asıl zorluk çıkarım değil;
            hangi kaydın hesaba girmeye hakkı olduğuna karar veren kapılar,
            geriye dönük düzenlenemeyen kayıtlar ve aynı girdinin her koşuda
            aynı çıktıyı vermesi.
          </p>
          <p>
            Bu sitede gördüğünüz proje o duruşun bir örneği: dil modeli yalnızca
            metinden okuma yapıyor, aritmetiğe hiç dokunmuyor, çıkarılan her
            sayının yanında ham cümlesi duruyor ve sistem emin olmadığında sayı
            üretmek yerine susuyor.
          </p>
        </section>

        <section>
          <h2 className="mono">02 · PROJELER</h2>
          <h3>Üçü de veri katmanından başlayıp arayüzde bitiyor</h3>

          <div className="yigin-kutu" style={{ marginBottom: 14 }}>
            <h4>KAP·RADAR — bu proje</h4>
            <div className="cip-dizi">
              <span className="cip cip-notr mono">KİŞİSEL ARAŞTIRMA</span>
              <span className="cip cip-notr mono">ÇALIŞIR PROTOTİP</span>
              <span className="cip cip-notr mono">PYTHON · POSTGRES · NEXT.JS</span>
            </div>
            <p style={{ marginBottom: 0 }}>
              Borsa İstanbul&apos;da düşen &ldquo;yeni iş ilişkisi&rdquo;
              bildirimlerini şirketin kendi cirosuna göre boyutlandıran
              deterministik bir analiz katmanı: 613 bildirim, 111 hisse, 12 ay.
              Kapsam ve metodoloji kararları, veri hattı mimarisi ve arayüz
              tasarımı bana ait; uygulama ile istatistiksel analiz Claude (Opus
              5) ile ortak yürütüldü.{" "}
              <Link href="/proje-hakkinda">Vaka çalışması</Link> ve{" "}
              <Link href="/metodoloji">araştırma notu</Link>.
            </p>
          </div>

          <div className="yigin-kutu" style={{ marginBottom: 14 }}>
            <h4>Calibre — öngörücü analitik motoru</h4>
            <div className="cip-dizi">
              <span className="cip cip-notr mono">CALIBRESOLVE</span>
              <span className="cip cip-notr mono">ORTAK GELİŞTİRİCİ</span>
              <span className="cip cip-notr mono">ML HATTI · OLASILIK MODELİ</span>
            </div>
            <p>
              Yüksek hacimli piyasa verisini makine öğrenmesi hatlarından ve
              olasılık modellerinden (Dixon–Coles) geçirip dinamik kapı
              eşikleriyle süzen kurumsal ölçekte bir sinyal motoru. Katmanlı
              mimari: birinci katman sıkı eşiklerle sinyal saflığını korurken,
              ikinci katman gevşetilmiş eşiklerle istatistiksel gücü artırıyor.
            </p>
            <p style={{ marginBottom: 0 }}>
              Mühendislik tarafında belirleyici olan üç karar: walk-forward
              doğrulama, yalnızca örneklem-dışı ölçüm ve ilk günden itibaren
              PostgreSQL&apos;e yazılan, geriye dönük düzenlenmeyen sinyal
              kaydı. 16 ay sessiz geliştirmenin ardından gerçek sermayeyle
              canlıya alındı; otomatik mutabakat işçisi kâr-zararı insan eli
              değmeden güncelliyor.
            </p>
          </div>

          <div className="yigin-kutu">
            <h4>RouteWise — şehir keşif uygulaması</h4>
            <div className="cip-dizi">
              <span className="cip cip-notr mono">ORTAK GELİŞTİRİCİ</span>
              <span className="cip cip-notr mono">OFFLINE-FIRST PWA</span>
              <span className="cip cip-notr mono">MAPBOX · VANILLA JS</span>
            </div>
            <p style={{ marginBottom: 0 }}>
              Bursa&apos;nın mekânlarını, etkinliklerini ve az bilinen
              rotalarını tek ekranda toplayan mobil şehir rehberi; liste
              vermekle kalmayıp &ldquo;sessiz bir çalışma kahvecisi&rdquo; gibi
              niyete göre filtreliyor. Veri mimarisinden erken aşama iş
              planlamasına kadar kapsamı birlikte kurduk. Teknik seçimler:
              offline-first PWA, harita üzerinde gerçek zamanlı mekân kümeleme,
              framework bağımlılığı olmadan düşük gecikmeli arayüz, özel
              yetkilendirme ve konum önbellekleme (TTL).
            </p>
          </div>
        </section>

        <section style={{ borderTop: "1px solid var(--ken)", paddingTop: 30 }}>
          <div className="ust-etiket mono">İLETİŞİM</div>
          <p>
            Projelerin ayrıntısı, mimari şemalar ve geri test raporları için{" "}
            <a href={LINKEDIN} target="_blank" rel="noopener noreferrer">
              LinkedIn profili
            </a>
            . Mesaj kutusu açık.
          </p>
          <p style={{ fontSize: 12.5, color: "var(--mut-2)", marginBottom: 0 }}>
            Bu sayfa KAP·RADAR&apos;ın yapanlar künyesinin uzun hâlidir. Calibre
            ve RouteWise bu projeden bağımsız, ayrı ekiplerle yürütülen
            çalışmalardır.
          </p>
        </section>
      </main>
    </>
  );
}
