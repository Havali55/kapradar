import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { isaretliYuzde, sayi, yilda, yuzdeIyelik } from "@/lib/bicim";
import { anlamliMi, donemAdi } from "@/lib/soz";
import { anaSatirlariGetir, sozVerisiGetir } from "@/lib/veri";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Proje hakkında",
  description:
    "Vaka çalışması: KAP yeni iş bildirimlerini şirketin kendi cirosuna göre ölçen veri hattı; ölçülen doğruluğu, enflasyon muhasebesi tuzağı, bir denetimin hikâyesi, sınamalar ve bilerek yapılmayanlar.",
};

// Veritabanında olmayan sayılar, kaynağıyla. Hepsi repodaki notlarda:
// doğruluk README ("Çıkarım doğruluğu"); denetim
// docs/arastirma/2026-09-26-veri-denetimi.md; maliyet
// scripts/rejim_arsivi.py (2024-09 geri doldurma faturası) ve README.
// Metindeki sabit sayılar: TMS 29 (03) metodoloji II "Paydayı sessizce
// bozan dört şey"; sınama (06) plasebo ve K notları
// (docs/arastirma/2026-09-29-*); çekim maliyeti (09) veri envanteri.
// Hiçbir cümle o notlardan güçlü olmamalı.
const KURAL_SAYISI = 13;
const ALTIN_KUME = { dogru: 47, toplam: 50, skorAyni: 49 };
const DENETIM = { taranan: 1272, isaretli: 453, okunan: 150, kesinHata: 10, elleKarar: 23 };
const GERI_DOLDURMA = { cikarim: 690, usd: 0.487 };

export default async function ProjeHakkinda() {
  // Canlı sayılar her tazelemede veritabanından: veri büyüdükçe metin
  // sessizce yanlışa dönmesin.
  const [satirlar, soz] = await Promise.all([anaSatirlariGetir(), sozVerisiGetir()]);
  const toplam = satirlar.length;
  const olculen = satirlar.filter((s) => s.ciro_orani !== null).length;
  const sirketSayisi = new Set(satirlar.map((s) => s.ticker)).size;
  const zamanlar = satirlar.map((s) => Date.parse(s.yayin_zamani));
  const aySayisi = zamanlar.length
    ? Math.round((Math.max(...zamanlar) - Math.min(...zamanlar)) / (30.44 * 86_400_000))
    : 0;
  const ozet = soz?.ozet ?? null;

  return (
    <main className="govde govde-dar yazi">
      <div className="ust-etiket mono">VAKA ÇALIŞMASI · 2026</div>
      <h1>KAP bildirimlerini yorumdan arındırmak</h1>
      <p style={{ fontSize: 16, marginBottom: 12 }}>
        Borsa İstanbul&apos;da her gün &ldquo;yeni iş ilişkisi&rdquo; bildirimleri
        düşer. Bu proje her birini şirketin kendi cirosuna göre ölçen bir veri
        hattı: tutarı metinden çıkarır, her sayıyı kaynak cümlesine bağlar,
        emin olmadığında susar. Tahmin üretmez. Aşağıda nasıl kurulduğu, neyi
        doğru ölçtüğü, nerede yanıldığı ve bunun nasıl yakalandığı var.
      </p>

      <div className="olcuum" style={{ marginTop: 32 }}>
        <div className="olcu">
          <div className="olcu-et mono">ARŞİV</div>
          <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
            {sayi(toplam, 0)} bildirim · {sirketSayisi} şirket · {aySayisi} ay
          </div>
        </div>
        <div className="olcu">
          <div className="olcu-et mono">ÖLÇÜLEN</div>
          <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
            {sayi(olculen, 0)} bildirimin büyüklüğü
          </div>
        </div>
        <div className="olcu">
          <div className="olcu-et mono">ÇIKARIM DOĞRULUĞU</div>
          <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
            {ALTIN_KUME.toplam}&apos;de {ALTIN_KUME.dogru} (altın küme)
          </div>
        </div>
        <div className="olcu">
          <div className="olcu-et mono">GÜNCELLEME</div>
          <div className="olcu-deger" style={{ fontSize: 15, fontWeight: 500 }}>
            Her iş günü 19:30
          </div>
        </div>
      </div>

      <section style={{ marginTop: 56 }}>
        <h2 className="mono">01 · SORUN</h2>
        <h3>Aynı haber, iki şirkette bambaşka anlama geliyor</h3>
        <p>
          500 milyon TL&apos;lik bir sözleşme, cirosu 200 milyar TL olan bir holding
          için gürültü; cirosu 2 milyar TL olan bir taahhüt şirketi için yılın
          olayıdır. KAP metinleri bu bağlamı vermez: tutar bazen açıklanır bazen
          açıklanmaz, karşı taraf bazen &ldquo;ticari sır&rdquo;dır, ihale ile
          sözleşme aynı işi iki kez duyurur. Bu farkı elle çıkarmak her bildirim
          için dakikalar alır; site bunu her akşam bütün bildirimler için yapıyor.
        </p>
      </section>

      <section>
        <h2 className="mono">02 · VERİ HATTI</h2>
        <h3>Dil modeli okur, kod ölçer, kapı arada durur</h3>
        <p>
          Hattın tamamı deterministik değil ve bunu gizlemenin anlamı yok: serbest
          metinden tutarı bir dil modeli çıkarıyor. Önemli olan{" "}
          <strong>modelin nereye karışmadığı</strong>: aritmetik, kur çevrimi,
          ciro ve büyüklük düz kod.
        </p>
        <div className="yigin-kutu">
          <ol style={{ paddingLeft: 20, margin: 0 }}>
            <li>
              <strong>Toplama.</strong> KAP bildirimi ham hâliyle arşivlenir. Karşı
              taraf, tarih ve güncelleme bayrağı KAP&apos;ın yapılandırılmış
              alanlarından okunur; serbest metinden yalnız tutar alınır.
            </li>
            <li>
              <strong>Çıkarım.</strong> Model her tutarı, para birimini ve kalem
              tipini <strong>birebir alıntısıyla</strong> verir. Alıntı ham metinde
              yoksa çıkarım reddedilir: model bir sayıyı &ldquo;hatırlayamaz&rdquo;.
            </li>
            <li>
              <strong>Kapı.</strong> {KURAL_SAYISI} deterministik kural çıkarımı
              metne, aritmetiğe ve anlamına karşı sınar. Geçemeyen bildirim
              yayınlanmaz; insan karar verir ve kararı gerekçesiyle kayda geçer.
            </li>
            <li>
              <strong>Payda.</strong> Bildirim anında kamuya açık son raporlardan
              son 12 aylık ciro, enflasyon düzeltmeli (TMS 29). Sonradan yayınlanan
              rapor geçmişe yazılmaz. Tutar, bildirim gününün TCMB kuruyla TL.
            </li>
            <li>
              <strong>Bağ.</strong> Aynı işin ihale ve sözleşme aşamasındaki iki
              duyurusu birbirine bağlanır, bir kez sayılır.
            </li>
          </ol>
        </div>
        <p>
          Tutar ya da ciro yoksa büyüklük de yok: arşivin{" "}
          <strong>{yuzdeIyelik((toplam - olculen) / Math.max(1, toplam), 0)}</strong>{" "}
          bu durumda ve kart bunu açıkça söylüyor. Tahmini tutar üretmek,
          kullanıcıya olmayan bir kesinlik satmak olurdu.
        </p>
      </section>

      <section>
        <h2 className="mono">03 · PAYDA</h2>
        <h3>Enflasyon muhasebesi oranı sessizce %7–25 büyütüyordu</h3>
        <p>
          Oranın paydası şirketin son 12 aylık cirosu ve tek bir ara dönem
          raporundan kuruluyor: geçen yılın cirosu, artı bu yılın ilk aylarının
          cirosu, eksi geçen yılın aynı aylarının cirosu. Yüksek enflasyon
          muhasebesinden (TMS 29) beri her rapor geçen yılın rakamlarını
          bugünün satın alma gücüyle yeniden yazıyor. DCTTR&apos;nin 2024
          hasılatı ilk raporunda 2,51, bir yıl sonraki raporda 3,28 milyar TL.
          Formülün iki terimi bugünün TL&apos;siyle, biri geçen yılın
          TL&apos;siyle geliyordu. Payda küçük, oran %7–25 büyük çıkıyordu;
          arşivdeki rapor çiftlerinin yaklaşık %91&apos;i yeniden ifade
          edilmişti.
        </p>
        <p>
          Düzeltme dış veri kullanmıyor. Eski terim, şirketin kendi
          raporlarından okunan katsayıyla bugünün birimine taşınıyor: aynı
          dönemin ilk yayını ile yeniden ifadesinin oranı. Bildirim anında
          yayınlanmamış hiçbir rapor kullanılmıyor. TMS 29&apos;a geçiş yılında
          bu katsayı enflasyonu değil muhasebe geçişini ölçtüğü için o dönemde
          resmî TÜFE kullanılıyor. İki düzeltme önce 51, sonra 13 bildirimin
          kademesini değiştirdi, hiçbir bildirimin yayın kararını değiştirmedi.
          Aynı yeniden ifade, sitedeki ciro büyümesini dış veri olmadan reel
          ölçmeyi de sağlıyor.
        </p>
      </section>

      <section>
        <h2 className="mono">04 · ÖLÇÜLEN DOĞRULUK</h2>
        <h3>Elle etiketlenmiş 50 bildirimde 47 tam doğru</h3>
        <p>
          Çıkarım, elle etiketlenmiş {ALTIN_KUME.toplam} bildirimlik bir altın
          kümeyle ölçüldü: {ALTIN_KUME.dogru} bildirimde bütün kalemler tam doğru,
          büyüklük {ALTIN_KUME.skorAyni} bildirimde elle hesaplananla aynı. Ölçüm
          betiği repoda ve yeniden koşmak için dil modeli gerekmiyor; saklı
          çıkarımlar üzerinden çalışıyor.
        </p>
      </section>

      <section>
        <h2 className="mono">05 · BİR DENETİMİN HİKÂYESİ</h2>
        <h3>Kapı sayının metinde geçtiğini denetliyordu, neyin sayısı olduğunu değil</h3>
        <p>
          Eylül 2026&apos;da bir okur ARDYZ kartını sordu: iş &ldquo;cirosunun
          %5,5&apos;i&rdquo; görünüyordu. KAP metnindeki 430 milyon TL, bir belediye
          ihalesinin <strong>muhammen bedeliydi</strong>: idarenin tahmini, gelir
          paylaşımlı 10 yıllık bir kiralama. Şirketin geliri değildi ve alıntı
          kapısı onu geçirmişti, çünkü sayı metinde gerçekten geçiyordu.
        </p>
        <p>
          Soru tek bir kartın değil, hata sınıfının ne kadar yaygın olduğuydu.
          Yayındaki {sayi(DENETIM.taranan, 0)} bildirimin tamamı kural tabanlı bir
          tarayıcıdan geçirildi, işaretlenen {DENETIM.isaretli} bildirimin
          yaklaşık {DENETIM.okunan}&apos;i elle okundu. Sonuç:{" "}
          {DENETIM.kesinHata} kesin yanlış büyüklük, büyüklüğü ölçülen
          bildirimlerin %1&apos;i. Ama hepsi sitenin öne çıkardığı &ldquo;önemli&rdquo;
          ve &ldquo;mega&rdquo; kademedeydi: bu hata tipi tutarı hep büyütüyor.
        </p>
        <p>
          Kapıya dört kural eklendi (anlam denetimi: tedarikçi, muhammen ve
          yatırım bedeli, artış ile yeni toplamın birlikte sayılması; özette
          metinde olmayan yıl). {DENETIM.elleKarar} bildirim için elle karar
          verildi, gerekçeleri sitede görünüyor. Denetim artık her akşamki
          koşunun sonunda yeniden çalışıyor; karar bekleyen bildirim varsa koşu
          kırmızıya dönüyor.
        </p>
      </section>

      <section>
        <h2 className="mono">06 · AMPİRİK SINAMA</h2>
        <h3>Yedi yılda sınandı; ikisi çöktü, biri açık soru</h3>
        <p>
          Büyüklük &ldquo;bu iş şirketin ölçeğine göre büyük&rdquo; der,
          &ldquo;hisse yükselecek&rdquo; demez. Bu yüzden asıl sınavı getiri
          değil işlem hacmi. Bulgular ilk yılda kuruldu, sonra hiç görülmemiş
          bir yılda ve 2020&apos;den bu yana üç para rejiminde (3.091
          bildirim) aynı kodla yeniden koşuldu. Ölçü aletinin kendisi de
          sınandı: aynı hesap olay olmayan rastgele günlerde çalıştırıldı ve
          orada sinyal üretmedi.
        </p>
        <ul>
          <li>
            <strong>Tuttu.</strong> Bildirim günü işlem hacmi her rejimde
            normalin üstüne çıkıyor; rastgele günlere göre net +%21 ile +%34
            arası. Büyüklük bir getiri tahmini değil: iki yılda da ilişki
            bulunamadı. %1&apos;in altındaki işlerde de ilgi var, bu yüzden
            ölçeğin tabanı %0,25&apos;e indirildi.
          </li>
          <li>
            <strong>Çöktü.</strong> &ldquo;Sık bildirimcide tepki sönük&rdquo; ve
            &ldquo;tahtaya göre ayrışma&rdquo; örneklem dışında tekrarlanmadı;
            sitede artık iddia edilmiyor.
          </li>
          <li>
            <strong>Açık kaldı.</strong> Hacmin bildirimden önce yükselmesi önce
            bir &ldquo;sızıntı&rdquo; gibi okundu, sonra &ldquo;sızıntı
            yok&rdquo;a döndü. İkisi de fazlaydı: bu ölçü o soruya cevap
            verecek hassasiyette değil. Ürün bir sızıntı iddiası taşımıyor.
          </li>
          <li>
            <strong>Yeniden konumlandı.</strong> Karşı tarafı gizli ya da
            güncelleme olan duyuruyu aşağı çeken K çarpanının ilk yıldaki
            &ldquo;sağlaması&rdquo; örneklem dışında tutmadı. K kalıyor, ama ne
            olduğu düzeltildi: bir tepki tahmini değil, dışarıdan
            doğrulanamayan bilgi için bir şeffaflık ayarı. Kartta görünen
            büyüklüğü etkilemiyor.
          </li>
        </ul>
        <p>
          Sayıların ve sağlamlık sınavlarının tamamı{" "}
          <Link href="/metodoloji">araştırma notunda</Link>.
        </p>
      </section>

      {soz && ozet && (
        <section>
          <h2 className="mono">07 · SÖZ VE GERÇEK</h2>
          <h3>Çok iş duyuranlar gerçekten büyüdü mü?</h3>
          <p>
            Sitenin ölçtüğü şey bir söz: duyurulan iş. Burada ilk kez
            gerçekleşenle yan yana konuyor. {yilda(soz.veri.sozYili)} duyurduğu
            işlerin toplamı yıllık cirosuna oranla en yüksek olan üçte birlik
            grupta, {donemAdi(soz.veri.donem)} enflasyondan arındırılmış ciro
            büyümesinin medyanı{" "}
            <strong>{isaretliYuzde(ozet.gruplar[2].medyanBuyume, 1)}</strong>; alttaki
            iki grupta {isaretliYuzde(ozet.gruplar[0].medyanBuyume, 1)} ve{" "}
            {isaretliYuzde(ozet.gruplar[1].medyanBuyume, 1)} ({ozet.n} şirket).
            Sıra korelasyonu {sayi(ozet.rho, 2)}; %5 düzeyinde{" "}
            {anlamliMi(ozet.t, ozet.n) ? "anlamlı" : "anlamlı değil"}. Tek dönem,
            bir neden-sonuç iddiası değil; sonuç zayıflarsa sitedeki cümle de
            kendiliğinden değişiyor.{" "}
            <Link href="/#soz-bas">Grafik ana sayfada</Link>.
          </p>
        </section>
      )}

      <section>
        <h2 className="mono">08 · MALİYET</h2>
        <h3>Bir yıllık geçmişin çıkarımı yarım dolar</h3>
        <p>
          Dil modeli katmanlı çalışıyor: işlerin çoğu küçük modelde, şüpheli
          olanlar büyüğe yükseliyor. 2024-09&apos;a uzanan {GERI_DOLDURMA.cikarim}{" "}
          bildirimlik geçmişin çıkarım faturası{" "}
          {sayi(GERI_DOLDURMA.usd, 3)} USD; günlük koşu ayda birkaç sent. Kur
          (TCMB), finansal tablolar (KAP) ve fiyatlar herkese açık kaynaklardan.
          Ücretli bir çağrı onaysız yapılmıyor.
        </p>
      </section>

      <section>
        <h2 className="mono">09 · NEREDE DURDUK</h2>
        <h3>Araştırmanın da bir kapsamı var</h3>
        <p>
          Ürünün iddiası dar: bir işin, şirketin kendi ölçeğine göre
          büyüklüğü. Bu iddiayı sınamak için yedi yıllık veri, örneklem dışı
          sınama ve rastgele gün kıyası yetti. Ötesindeki her soru ürünü
          değiştirmeden bilgi eklerdi; araştırma bu yüzden 30 Eylül 2026&apos;da
          kapandı. Bilerek yapılmayanlar:
        </p>
        <ul>
          <li>
            <strong>2020–24 bildirimlerinden tutar çıkarmak.</strong> Yaklaşık
            4.400 KAP isteği, KAP&apos;ın izin verdiği hızla ~17 saatlik bir
            çekim. Skora dayanan sınavları yedi yıla taşırdı; kartta görünen
            hiçbir şeyi değiştirmezdi.
          </li>
          <li>
            <strong>Yeni sınavlar.</strong> Sızıntının getiri tabanlı sınavı,
            üç günden uzun ufuk, fonların tuttuğu payların sonraki seyri.
            Araştırma notunda{" "}
            <Link href="/metodoloji#acik-sorular">açık sorular</Link> olarak,
            veri ve maliyet envanteriyle duruyor.
          </li>
          <li>
            <strong>Tahmin.</strong> Site alım-satım sinyali üretmiyor. Bu bir
            ihtiyat cümlesi değil, ölçümün sonucu: büyüklük 3 günlük tepkiyi
            bu örneklemde öngörmüyor.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="mono">10 · NASIL ÇALIŞILDI</h2>
        <h3>Kararlar insanın, kod ortak</h3>
        <p>
          Proje Hüseyin Dinçer&apos;in; kod, analiz ve yazımda Claude ile birlikte
          çalışıldı. Kapsam, yöntem ve yayın kararlarının hepsi Hüseyin&apos;in:
          doğrulama kapısının katı kalması, her sayfada yatırım tavsiyesi
          olmadığının yazılması, enflasyon düzeltmesinin hangi durumda resmî
          TÜFE&apos;ye geçeceği gibi. Her büyük değişiklik önce yazılı bir tasarım ve plan,
          sonra testli küçük adımlar, en sonda tarayıcıda doğrulama olarak
          ilerliyor. Depodaki commit&apos;lerde ortak yazarlık işaretli; tasarım
          belgeleri ve araştırma notları repoda.
        </p>
        <p>
          Projeyi 50 saniyede anlatan kısa film:{" "}
          <Link href="/film">KAP·RADAR filmi</Link>.
        </p>
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
            — proje tasarımı, kapsam ve metodoloji kararları, veri hattı mimarisi,
            arayüz tasarımı ve bütün karar onayları.
            <br />
            <strong>Claude (Anthropic)</strong> — uygulama, istatistiksel analiz ve
            yazım. Depoda ortak yazarlık <code>Co-Authored-By</code> ile işaretli.
          </p>
        </div>
        <p style={{ fontSize: 12.5, color: "var(--mut-2)" }}>
          Proje eğitim amaçlı kişisel bir araştırmadır. Büyüklükler kamuya açık KAP
          metinleri ve finansal tablolar üzerinden hesaplanır; hiçbir alım-satım
          önerisi içermez.
        </p>
      </section>
    </main>
  );
}
