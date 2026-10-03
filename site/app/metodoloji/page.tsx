import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Yöntem ve sınırlar",
  description:
    "Büyüklük nasıl hesaplanıyor: işin tutarı, şirketin bildirim anındaki son 12 aylık cirosu, enflasyon muhasebesi düzeltmesi, doğrulama kapısı ve sitenin söylemediği şeyler.",
};

/**
 * Ürünü kullanan okur için kısa yöntem. Mühendislik hikâyesi vaka
 * sayfasında (`/proje-hakkinda`); 2026-09 araştırma makalesi depoda,
 * `docs/arastirma/arsiv/` altında.
 */
export default function Yontem() {
  return (
    <main className="govde govde-dar yazi">
      <div className="ust-etiket mono">YÖNTEM VE SINIRLAR</div>
      <h1>Büyüklük nasıl hesaplanıyor</h1>
      <p style={{ fontSize: 16, marginBottom: 12 }}>
        Her yeni iş bildirimi için tek bir oran: işin TL tutarı, şirketin
        bildirim anındaki son 12 aylık cirosuna bölünür. Oran %5&apos;in
        altındaysa rutin, %5 ve üstüyse önemli, %15 ve üstüyse mega iş.
      </p>

      <section>
        <h2 className="mono">01 · TUTAR</h2>
        <h3>Dil modeli okur, kurallar denetler</h3>
        <p>
          Bildirimin serbest metninden işin tutarını bir dil modeli çıkarır.
          Model her tutarı, para birimini ve kalem tipini metindeki birebir
          alıntısıyla vermek zorunda; alıntı metinde yoksa çıkarım reddedilir.
          Ardından 13 kurallı bir kapı çıkarımı metne, aritmetiğe ve anlamına
          karşı sınar: muhammen bedel, tedarikçiye ödenen ya da yatırım bedeli
          şirketin geliri sayılmaz. Kapıdan geçemeyen bildirim yayınlanmaz;
          insan karar verir ve gerekçesi bildirim sayfasında görünür.
        </p>
        <p>
          Toplam sözleşme bedeli (projenin önceki işlerle birlikte kümülatif
          tutarı) hesaba girmez; yalnız yeni iş sayılır. Döviz tutarları
          bildirim gününün TCMB kuruyla TL&apos;ye çevrilir. Aynı işin ihale ve
          sözleşme aşamasındaki iki duyurusu bir kez sayılır.
        </p>
      </section>

      <section>
        <h2 className="mono">02 · PAYDA</h2>
        <h3>Bildirim anındaki son 12 aylık ciro</h3>
        <p>
          Payda, bildirim anında KAP&apos;ta yayınlanmış son finansal
          raporlardan kurulan son 12 aylık cirodur; sonradan yayınlanan rapor
          geçmişe yazılmaz. Enflasyon muhasebesi (TMS 29) her raporda geçen
          yılın rakamlarını bugünün satın alma gücüyle yeniden yazar. Bu
          yüzden farklı raporlardan gelen terimler, şirketin kendi
          raporlarından okunan katsayıyla aynı TL birimine getirilir. TMS
          29&apos;a geçiş yılında resmî TÜFE kullanılır.
        </p>
      </section>

      <section>
        <h2 className="mono">03 · DOĞRULUK</h2>
        <h3>Ölçülen, varsayılmayan</h3>
        <p>
          Çıkarım, elle etiketlenmiş 50 bildirimlik bir kümeyle ölçüldü: 47
          bildirimde bütün kalemler tam doğru. Her akşamki koşunun sonunda bir
          denetim gelir olmayan tutarları arar; karar bekleyen bildirim varsa
          koşu kırmızıya döner. Ayrıntısı ve bir denetimin hikâyesi{" "}
          <Link href="/proje-hakkinda">vaka çalışmasında</Link>.
        </p>
      </section>

      <section>
        <h2 className="mono">04 · SINIRLAR</h2>
        <h3>Sitenin söylemediği şeyler</h3>
        <ul>
          <li>
            <strong>Fiyat tahmini yok.</strong> Bir işin şirket için büyüklüğü
            hissenin ne yapacağını söylemez. Site alım-satım sinyali üretmez,
            yatırım tavsiyesi değildir.
          </li>
          <li>
            <strong>Tutar ya da ciro yoksa oran da yok.</strong> Tutarı
            açıklanmamış ya da cirosu bilinmeyen bildirimde büyüklük
            hesaplanmaz ve kart bunu açıkça söyler. Uydurma bir paydayla
            hesaplanan oran, hiç oran olmamasından kötüdür.
          </li>
          <li>
            <strong>Duyurulan tutar bir söz.</strong> Sözleşmeler çoğu zaman
            birkaç yıla yayılır, ciro ise bir yılın satışıdır. Oran işin
            şirket için ölçeğini söyler, gelecek yılın cirosunu söylemez.
          </li>
          <li>
            <strong>Karşı taraf, şirketin açıkladığı kadar.</strong> Şirket
            müşterisinin adını vermemişse site de veremez.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="mono">05 · KAYNAKLAR</h2>
        <p>
          Bildirimler ve finansal tablolar KAP&apos;tan, döviz kurları
          TCMB&apos;den, fon pozisyonları fonların KAP&apos;taki Portföy
          Dağılım Raporlarından, borsa tedbiri Borsa İstanbul&apos;un
          KAP&apos;taki kayıtlarından. Veri her iş günü 19:30&apos;da
          güncellenir.
        </p>
      </section>
    </main>
  );
}
