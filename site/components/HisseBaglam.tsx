import { buyukTl, isaretliYuzde, sayi, yuzde } from "@/lib/bicim";
import type { HisseFon } from "@/lib/veri";

type Props = {
  son12Adet: number;
  toplam: number;
  fon: HisseFon | null;
};

/**
 * Şirket bağlamı: bildirim sıklığı (yalnız sayım) ve fon sahipliği.
 * Hiçbiri büyüklüğe girmiyor; okuru yanıltmasın diye her biri neyi
 * söylemediğini de söylüyor.
 */
export default function HisseBaglam({ son12Adet, toplam, fon }: Props) {
  return (
    <>
      <section className="yan-kutu" aria-labelledby="baglam-bas">
        <span className="ust-yazi">Bağlam</span>
        <h3 id="baglam-bas">Şirket</h3>
        <dl className="baglam">
          <div>
            <dt>Bildirim sıklığı</dt>
            <dd>
              Son 12 ayda {son12Adet} duyuru; arşivin tamamında {toplam}. Bu yalnız bir
              sayım: şirketin ne sıklıkla duyuru yaptığını söyler, duyurunun önemini
              söylemez.
            </dd>
          </div>
        </dl>
      </section>
      {fon && (
        <section className="yan-kutu">
          <details>
            <summary>Fon sahipliği</summary>
            <dl className="baglam">
              <div>
                <dt>Pozisyon açıklayan fonlar</dt>
                <dd>
                  {fon.fon_sayisi} fon · {fon.portfoy_sirketi_sayisi} portföy şirketi ·{" "}
                  {buyukTl(fon.fon_tl)}
                  {fon.son_rapor_donemi ? ` · son rapor ${fon.son_rapor_donemi}` : ""}
                </dd>
              </div>
              {fon.fon_tl_3ay_once !== null && fon.fon_tl_3ay_once > 0 && (
                <div>
                  <dt>3 ay önceki fon pozisyonu</dt>
                  <dd>
                    {buyukTl(fon.fon_tl_3ay_once)} (
                    {isaretliYuzde(fon.fon_tl / fon.fon_tl_3ay_once - 1, 0)})
                  </dd>
                </div>
              )}
              {fon.en_buyuk_pay !== null && fon.portfoy_sirketi_sayisi > 1 && (
                <div>
                  <dt>En büyük portföy şirketinin payı</dt>
                  <dd>{yuzde(fon.en_buyuk_pay, 0)}</dd>
                </div>
              )}
              {fon.tasfiye_tl > 0 && (
                <div>
                  <dt>Tasfiyedeki fonların pozisyonu</dt>
                  <dd>
                    {buyukTl(fon.tasfiye_tl)} · {fon.tasfiye_fon_sayisi} fon
                    {fon.gunluk_hacim_tl
                      ? ` · ≈ ${sayi(fon.tasfiye_tl / fon.gunluk_hacim_tl, 1)} günlük işlem hacmi`
                      : ""}
                  </dd>
                </div>
              )}
            </dl>
            {fon.tasfiye_tl > 0 && (
              <p className="yan-not">
                SPK&apos;nın tasfiyeye aldığı fonların varlıkları tasfiye süresince
                satılacak. &ldquo;Günlük işlem hacmi&rdquo; oranı bu pozisyonun son 20
                seansın ortalama TL hacmine bölünmesiyle bulunur; satışın ne zaman ve
                nasıl yapılacağını söylemez.
              </p>
            )}
            {fon.muaf_fon_sayisi > 0 && (
              <p className="yan-not">
                Portföy şirketlerinin, nitelikli yatırımcı muafiyetiyle portföyünü
                açıklamayan {fon.muaf_fon_sayisi} fonu daha var; gerçek fon pozisyonu
                yukarıdakinden büyük olabilir.
              </p>
            )}
            <p className="yan-not">
              Kaynak: fonların KAP&apos;taki Portföy Dağılım Raporları, çoğunlukla aylık
              ve yaklaşık bir ay geriden. Fon pozisyonu büyüklüğe girmez.
            </p>
          </details>
        </section>
      )}
    </>
  );
}
