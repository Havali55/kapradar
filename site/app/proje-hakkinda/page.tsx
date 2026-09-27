import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { bildirimleriGetir, ozetCikar } from "@/lib/veri";
import { sayi, yuzdeIyelik } from "@/lib/bicim";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Proje hakkında",
  description:
    "KAP bildirimlerini yorumdan arındırmak: problem, mimari, tasarım kararları ve ölçülen sonuçlar.",
};

export default async function ProjeHakkinda() {
  // Sayılar elle yazılmıyor: sayfa her tazelendiğinde veritabanından
  // geliyor. Maketteki "yaklaşık altıda biri" gibi bir ifade, veri
  // büyüdükçe sessizce yanlışa dönüşürdü.
  const bildirimler = await bildirimleriGetir();
  const ozet = ozetCikar(bildirimler);
  const skorsuz = ozet.toplam - ozet.skorlu;
  const hisseSayisi = new Set(bildirimler.map((b) => b.ticker)).size;
  const zamanlar = bildirimler.map((b) => new Date(b.yayin_zamani).getTime());
  // Arşivin kapsadığı ay sayısı, ilk ve son bildirim arasından.
  const aySayisi = zamanlar.length
    ? Math.round((Math.max(...zamanlar) - Math.min(...zamanlar)) / (30.44 * 86400000))
    : 0;

  return (
    <>
      <main className="govde govde-dar yazi">
        <div className="ust-etiket mono">VAKA ÇALIŞMASI · 2026</div>
        <h1>KAP bildirimlerini yorumdan arındırmak</h1>
        <p style={{ fontSize: 16, marginBottom: 12 }}>
          Borsa İstanbul&apos;da her gün &ldquo;yeni iş ilişkisi&rdquo;
          bildirimleri düşer. Hangisi şirketin cirosuna göre gerçekten büyük,
          hangisi gürültü — bunu ayırt etmek için deterministik bir
          boyutlandırma katmanı kurduk. Sistem tahmin üretmez; ölçer, kaynağını
          gösterir, emin olmadığında susar.
        </p>

        <div className="olcuum" style={{ marginTop: 32 }}>
          <div className="olcu">
            <div className="olcu-et mono">KAPSAM</div>
            <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
              Veri hattı + analiz + arayüz
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">VERİ</div>
            <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
              {sayi(ozet.toplam, 0)} bildirim · {hisseSayisi} hisse · {aySayisi} ay
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">DOĞRULUK</div>
            <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
              %94 (50 bildirimlik altın küme)
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">DURUM</div>
            <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
              Çalışır prototip
            </div>
          </div>
        </div>

        <section style={{ marginTop: 56 }}>
          <h2 className="mono">01 · PROBLEM</h2>
          <h3>Aynı haber, iki şirkette bambaşka anlama geliyor</h3>
          <p>
            500 milyon TL&apos;lik bir sözleşme, cirosu 200 milyar TL olan bir
            holding için gürültü; cirosu 2 milyar TL olan bir taahhüt şirketi
            için şirketi yeniden fiyatlandıran bir olaydır. KAP metinleri bu
            bağlamı vermez: tutar bazen açıklanır bazen açıklanmaz, karşı taraf
            bazen isimlendirilir bazen &ldquo;ticari sır&rdquo; denir, ilk
            bildirim ile güncelleme aynı biçimde görünür.
          </p>
          <p>
            Bireysel yatırımcı bu farkı elle çıkaramaz. Sonuç: en çok bağıran
            başlık en çok ilgi görür, oranı büyük olan sessiz bildirim gözden
            kaçar.
          </p>
        </section>

        <section>
          <h2 className="mono">02 · MİMARİ</h2>
          <h3>LLM çıkarır, deterministik kod ölçer, kapı arada durur</h3>
          <p>
            Hattın tamamı deterministik değil ve bunu gizlemenin anlamı yok:
            serbest metinden tutar çıkarmayı bir dil modeli yapıyor. Kritik olan{" "}
            <strong>modelin nereye karışmadığı</strong> — aritmetiğe,
            kur çevrimine ve skora hiç dokunmuyor.
          </p>
          <div className="yigin-kutu">
            <ol style={{ paddingLeft: 20, margin: 0 }}>
              <li>
                <strong>Toplama.</strong> KAP&apos;ın &ldquo;yeni iş
                ilişkisi&rdquo; bildirimleri çekilir, ham metin değiştirilmeden
                arşivlenir.
              </li>
              <li>
                <strong>Çıkarım (LLM).</strong> Katmanlı yönlendirme: işlerin
                çoğu küçük modelde, şüpheli olanlar büyüğe yükseliyor. Modelin
                tek işi metinden tutar, para birimi ve kalem tipi okumak.
              </li>
              <li>
                <strong>Kapı A.</strong> Şemada her sayı için{" "}
                <strong>birebir alıntı zorunlu</strong>; alıntı ham metinde
                bulunamıyorsa çıkarım reddedilir. Bu, modelin bir sayıyı
                &ldquo;hatırlamasını&rdquo; imkânsız kılar.
              </li>
              <li>
                <strong>TTM eşleme.</strong> Bildirim anında kamuya açık olan
                son dört çeyreğin hasılatı bağlanır; sonraki finansallar geriye
                uygulanmaz.
              </li>
              <li>
                <strong>Kapı B.</strong> Hesaplar koştuktan sonra tutarlılık
                denetimi: oran eşiği aşarsa, kur bulunamazsa ya da aynı tutar
                iki para biriminde tekrarlanıyorsa bildirim elle incelemeye
                düşer.
              </li>
              <li>
                <strong>Skor ve dağılım.</strong> Oran logaritmik ölçeğe alınır,
                güvenilirlik çarpanıyla düzeltilir. Benzer bildirimlerin geçmiş
                tepkisi ayrı bir panelde, medyan ve çeyrekliklerle verilir.
              </li>
            </ol>
          </div>
        </section>

        <section>
          <h2 className="mono">03 · KARARLAR</h2>
          <h3>Üçü de &ldquo;daha az söyle&rdquo; yönünde</h3>
          <div className="yigin-kutu">
            <h4 style={{ marginTop: 0 }}>Emin olmadığında boş bırak</h4>
            <p style={{ marginBottom: 20 }}>
              Tahmini tutar üretmek, kullanıcıya olmayan bir kesinlik satmak
              demekti. Tutar ya da payda yoksa skor da yok — kart bunun yerine
              net bir rozet gösteriyor. Şu an arşivin{" "}
              <strong>
                {yuzdeIyelik(skorsuz / Math.max(1, ozet.toplam), 1)}
              </strong>{" "}
              ({skorsuz} bildirim) bu durumda ve bu bir eksiklik değil, ürünün
              duruşu.
            </p>
            <h4>Tek sayı yerine dağılım</h4>
            <p style={{ marginBottom: 20 }}>
              İlk 613 bildirimlik analiz örneklemi tekil getiri tahminini
              taşımıyor — ölçtük: tüm sinyaller 3 günlük tepkinin
              %6,4&apos;ünü açıklıyor.
              Bu yüzden Modül C medyan ve çeyreklik aralığını, örneklem
              boyutuyla birlikte gösteriyor.
            </p>
            <h4>Skor ile tahta kalitesi ayrı kalsın</h4>
            <p style={{ marginBottom: 0 }}>
              Spekülasyon geçmişini skora karıştırmak, iki farklı riski tek
              sayıya gömerdi. Modüller bağımsız duruyor: büyük bir iş kirli bir
              tahtada da olabilir.
            </p>
          </div>
        </section>

        <section>
          <h2 className="mono">04 · ÖLÇÜLEN SONUÇ</h2>
          <h3>Skoru kendi iddiasına karşı sınadık</h3>
          <p>
            Bir skor üretmek kolay; onun bir şey ölçtüğünü göstermek zor. Skorun
            iddiası dar olduğu için — &ldquo;bu bildirim şirketin kendi ölçeğine
            göre büyüktür&rdquo;, &ldquo;hisse yükselecek&rdquo; değil — sınav
            da getiri değil <strong>işlem hacmi</strong> üzerinden kuruldu.
          </p>
          <ul>
            <li>
              <strong>Bildirimler materyal olay.</strong> Bildirim günü işlem
              hacmi normalin %47,3 üzerine çıkıyor ve etki beş günde sönüyor.
            </li>
            <li>
              <strong>Bilgi resmî açıklamadan önce hareket ediyor.</strong> Hacim,
              bildirimden dört gün önce yükselmeye başlıyor.
            </li>
            <li>
              <strong>Skor bir getiri tahmini değil — ve gerçekten değil.</strong>{" "}
              İşaretli getiriyle ilişkisi sıfır. İddia ile ölçüm örtüşüyor.
            </li>
            <li>
              <strong>Bulguları görmediğimiz bir yılda yeniden sınadık —
              ikisi çöktü.</strong> Arşiv 2024-09&apos;a uzatılınca önceki 12
              ay (690 bildirim) gerçek bir örneklem dışı sınama oldu. Hacim
              artışı, bildirim öncesi sızıntı, skorun getiri tahmini olmadığı
              ve çok oynak ya da borsa tedbiri altındaki hisselerde tepkinin aşağı
              yönlü olduğu tekrarlandı.
              &ldquo;Sık bildirimcide tepki sönük&rdquo; ve &ldquo;skor
              spekülatif tahtada kırılıyor&rdquo; tekrarlanmadı; ikisi de
              artık iddia edilmiyor.
            </li>
            <li>
              <strong>Kendi eşiklerimizden biri çürüdü — ve düzeltildi.</strong>{" "}
              %1 tabanının altındaki bildirimlerde de hacim anlamlı biçimde
              artıyordu; yani formül bir grup gerçek olayı &ldquo;olay
              değil&rdquo; sayıyordu. Taban %0,25&apos;e indirildi, skoru
              sıfırlanan bildirim sayısı 62&apos;den 7&apos;ye düştü. Ölçek
              kaydığı için kademe eşikleri de birlikte taşındı.
            </li>
          </ul>
          <p>
            Bulguların tamamı, sağlamlık sınavları ve sınırlar{" "}
            <Link href="/metodoloji">araştırma notunda</Link>. Analiz betikleri
            repoda; veritabanının açık bir kopyası yayımlanana kadar yeniden
            üretmek için veritabanı erişimi gerekiyor.
          </p>
        </section>

        <section>
          <h2 className="mono">05 · DENETLENEBİLİRLİK</h2>
          <h3>Her sayının yanında ham cümlesi duruyor</h3>
          <p>
            Çıkarılan her tutarın kaynak cümlesi saklanıyor ve arayüzde
            gösteriliyor; tek tıkla KAP&apos;taki orijinal bildirime gidip sayıyı
            doğrulayabilirsiniz. Dil modelinin çıkarımı bir kez yapılıp
            saklanıyor; kur, oran ve skor bu saklı çıkarımdan her seferinde
            aynı sonucu veriyor.
          </p>
          <div className="olcuum">
            <div className="olcu">
              <div className="olcu-deger mono">{ozet.toplam}</div>
              <div className="olcu-alt">yayına hazır bildirim</div>
            </div>
            <div className="olcu">
              <div className="olcu-deger mono">%100</div>
              <div className="olcu-alt">skorun kaynak cümlesi izlenebilir</div>
            </div>
            <div className="olcu">
              <div className="olcu-deger mono">
                {ozet.medyanSkor === null ? "—" : sayi(ozet.medyanSkor)}
              </div>
              <div className="olcu-alt">medyan büyüklük skoru</div>
            </div>
            <div className="olcu">
              <div className="olcu-deger mono">0</div>
              <div className="olcu-alt">üretilen fiyat tahmini</div>
            </div>
          </div>
        </section>

        <section style={{ borderTop: "1px solid var(--ken)", paddingTop: 30 }}>
          <div className="ust-etiket mono">YAPANLAR</div>
          <div className="yapan-satiri">
            <Image
              src="/huseyin-dincer.jpg"
              alt="Hüseyin Dinçer"
              width={54}
              height={54}
              className="profil-foto"
            />
            <p style={{ marginBottom: 0 }}>
              <strong>
                {/* Profil sitede değil LinkedIn'de: site yalnız projeyi anlatıyor. */}
                <a
                  href="https://www.linkedin.com/in/h%C3%BCseyin-din%C3%A7er-663345247"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Hüseyin Dinçer
                </a>
              </strong>{" "}
              — proje tasarımı, kapsam ve metodoloji kararları, veri hattı
              mimarisi, arayüz tasarımı ve tüm karar onayları.
              <br />
              <strong>Claude (Opus 5)</strong> — uygulama, istatistiksel analiz
              ve yazım. Depoda ortak yazarlık <code>Co-Authored-By</code> ile
              işaretli.
            </p>
          </div>
          <p style={{ fontSize: 12.5, color: "var(--mut-2)" }}>
            Proje eğitim amaçlı kişisel bir araştırmadır. Skorlar kamuya açık
            KAP metinleri ve finansal tablolar üzerinden hesaplanır; hiçbir
            alım-satım önerisi içermez.
          </p>
        </section>
      </main>
    </>
  );
}
