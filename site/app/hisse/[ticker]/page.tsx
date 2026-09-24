import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { hisseFonGetir, hisseGetir, hisseleriGetir } from "@/lib/veri";
import { oranRengi, siklikRenk, tahtaRenk, yuzdelik } from "@/lib/skor";
import {
  KADEME_ADI,
  SIKLIK_ADI,
  SIKLIK_NOTU,
  TAHTA_ADI,
  TAHTA_NOTU,
  VBTS_KADEME_ADI,
  buyukTl,
  gunEtiketi,
  isaretliYuzde,
  sayi,
  yuzde,
} from "@/lib/bicim";

export const revalidate = 3600;

export async function generateStaticParams() {
  const hisseler = await hisseleriGetir();
  return hisseler.map((h) => ({ ticker: h.ticker }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ ticker: string }>;
}): Promise<Metadata> {
  const { ticker } = await params;
  const bildirimler = await hisseGetir(ticker);
  if (bildirimler.length === 0) return { title: `${ticker} bulunamadı` };

  const sirket = bildirimler[0].sirket;
  return {
    title: `${ticker} — ${sirket}`,
    description: `${sirket} (${ticker}) için ${bildirimler.length} yeni iş ilişkisi bildirimi, her biri şirketin kendi cirosuna göre boyutlandırılmış. Fiyat tahmini içermez.`,
  };
}

export default async function HisseSayfasi({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const [bildirimler, fon] = await Promise.all([
    hisseGetir(ticker),
    hisseFonGetir(ticker),
  ]);
  if (bildirimler.length === 0) notFound();

  const sirket = bildirimler[0].sirket;
  // Başlıktaki büyüklük ölçüsü de kart gibi ciro oranından — S değil.
  const oranlar = bildirimler
    .map((b) => b.ciro_orani)
    .filter((r): r is number => r !== null)
    .sort((a, b) => a - b);
  const medyan = oranlar.length ? yuzdelik(oranlar, 0.5) : null;
  const enBuyuk = oranlar.length ? oranlar[oranlar.length - 1] : null;

  // Tahta ve hasılat hissenin özelliği, bildirimin değil: en yeni
  // bildirimden okunuyor. Liste yeniden eskiye sıralı geliyor.
  const sonTahta = bildirimler.find((b) => b.tahta !== null);
  const sonHasilat = bildirimler.find((b) => b.ttm_hasilat !== null);

  // Sıklık şirket başına sabit; view'dan geliyor ve 613'ün tamamını
  // sayıyor. Sayfadaki liste yalnız yayına hazır olanları gösterdiği
  // için `bildirimler.length` ondan küçük olabilir — bu yüzden ikisi
  // ayrı ayrı yazılıyor.
  const siklikAdet = bildirimler[0].bildirim_sikligi;
  const siklik = bildirimler[0].siklik;

  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo">
            <span className="logo-ad mono">
              KAP<i>·</i>RADAR
            </span>
            <span className="logo-alt mono">HİSSE</span>
          </Link>
          <div className="bas-bos" />
          <Link href="/metodoloji" className="bag">
            Metodoloji
          </Link>
          <Link href="/" className="bag bag-koyu">
            Akışa dön
          </Link>
        </div>
      </header>

      <main className="govde govde-dar">
        <nav className="iz mono" aria-label="Konum">
          <Link href="/">Akış</Link>
          <span aria-hidden="true">/</span>
          <span>{ticker}</span>
        </nav>

        <div className="baslik-blok">
          <h1 style={{ fontSize: 28 }}>
            <span className="mono">{ticker}</span>{" "}
            <span style={{ fontWeight: 400, color: "var(--mut-2)" }}>
              {sirket}
            </span>
          </h1>
          <p>
            Arşivde bu hisseye ait {bildirimler.length} &ldquo;yeni iş
            ilişkisi&rdquo; bildirimi var. Her biri şirketin{" "}
            <strong>kendi cirosuna göre</strong> boyutlandırıldı; sıralama
            yeniden eskiye.
          </p>
        </div>

        <div className="olcuum">
          <div className="olcu">
            <div className="olcu-et mono">BİLDİRİM SIKLIĞI</div>
            <div
              className="olcu-deger mono"
              style={{
                color: siklik ? `var(--${siklikRenk(siklik)})` : undefined,
              }}
            >
              {siklikAdet ?? bildirimler.length}
            </div>
            <div className="olcu-alt">
              {siklik ? `${SIKLIK_ADI[siklik].toLocaleLowerCase("tr")} · ` : ""}
              12 ayda, {oranlar.length} tanesi skorlanabildi
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">MEDYAN BÜYÜKLÜK</div>
            <div
              className="olcu-deger mono"
              style={{ color: oranRengi(medyan) }}
            >
              {medyan === null ? "—" : yuzde(medyan, 1)}
            </div>
            <div className="olcu-alt">
              {enBuyuk !== null
                ? `hasılata oranla · en büyüğü ${yuzde(enBuyuk, 1)}`
                : "büyüklüğü hesaplanan bildirim yok"}
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">TAHTA</div>
            <div
              className="olcu-deger olcu-kisa"
              style={{
                color: sonTahta?.tahta
                  ? `var(--${tahtaRenk(sonTahta.tahta)})`
                  : undefined,
              }}
            >
              {sonTahta?.tahta ? TAHTA_ADI[sonTahta.tahta] : "—"}
            </div>
            <div className="olcu-alt">
              {sonTahta?.tahta
                ? sonTahta.tahta_vbts_kademe
                  ? `VBTS: ${VBTS_KADEME_ADI[sonTahta.tahta_vbts_kademe]}`
                  : `90 seansta ${sonTahta.tahta_v90 ?? "—"} devre kesici günü`
                : "ölçülemedi"}
            </div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">SON GÖRÜLEN TTM HASILAT</div>
            <div className="olcu-deger olcu-kisa">
              {sonHasilat?.ttm_hasilat != null
                ? buyukTl(sonHasilat.ttm_hasilat)
                : "—"}
            </div>
            <div className="olcu-alt">skorun paydası</div>
          </div>
        </div>

        {sonTahta?.tahta && sonTahta.tahta !== "temiz" && (
          <p className="panel-uyari" style={{ marginBottom: 10 }}>
            {TAHTA_NOTU[sonTahta.tahta]}{" "}
            {sonTahta.tahta === "tedbirli" &&
              "Bu hissenin bildirimlerinde tepki paneli fiyat oluşumunu değil oynaklığı yansıtıyor olabilir."}
          </p>
        )}

        {siklik === "sik" && (
          <p className="panel-uyari" style={{ marginBottom: 18 }}>
            {SIKLIK_NOTU.sik}
          </p>
        )}

        {fon && (
          <section style={{ margin: "8px 0 22px" }}>
            <h3 className="bolum-bas mono">
              FON SAHİPLİĞİ · BUGÜN
              {fon.son_rapor_donemi ? ` · SON RAPOR ${fon.son_rapor_donemi}` : ""}
            </h3>
            <dl className="kutu">
              <div className="kutu-satir">
                <dt>Pozisyon açıklayan fonlar</dt>
                <dd className="mono">
                  {fon.fon_sayisi} fon · {fon.portfoy_sirketi_sayisi} portföy şirketi
                  · {buyukTl(fon.fon_tl)}
                </dd>
              </div>
              {fon.fon_tl_3ay_once !== null && fon.fon_tl_3ay_once > 0 && (
                <div className="kutu-satir">
                  <dt>3 ay önceki fon pozisyonu</dt>
                  <dd className="mono">
                    {buyukTl(fon.fon_tl_3ay_once)} (
                    {isaretliYuzde(fon.fon_tl / fon.fon_tl_3ay_once - 1, 0)})
                  </dd>
                </div>
              )}
              {fon.en_buyuk_pay !== null && fon.portfoy_sirketi_sayisi > 1 && (
                <div className="kutu-satir">
                  <dt>En büyük portföy şirketinin payı</dt>
                  <dd className="mono">{yuzde(fon.en_buyuk_pay, 0)}</dd>
                </div>
              )}
              {fon.tasfiye_tl > 0 && (
                <div className="kutu-satir">
                  <dt>Tasfiyedeki fonların pozisyonu</dt>
                  <dd className="mono">
                    {buyukTl(fon.tasfiye_tl)} · {fon.tasfiye_fon_sayisi} fon
                    {fon.gunluk_hacim_tl
                      ? ` · ≈ ${sayi(fon.tasfiye_tl / fon.gunluk_hacim_tl, 1)} günlük işlem hacmi`
                      : ""}
                  </dd>
                </div>
              )}
            </dl>
            {fon.tasfiye_tl > 0 && (
              <p className="tutar-yok-not">
                SPK&apos;nın tasfiyeye aldığı fonların varlıkları tasfiye süresince
                satılacak. &ldquo;Günlük işlem hacmi&rdquo; oranı, bu pozisyonun
                son 20 seansın ortalama TL hacmine bölünmesiyle bulunur; satışın
                ne zaman ve nasıl yapılacağını söylemez.
              </p>
            )}
            {fon.muaf_fon_sayisi > 0 && (
              <p className="tutar-yok-not">
                Bu hissede pozisyonu olan portföy şirketlerinin, nitelikli
                yatırımcı muafiyetiyle portföyünü açıklamayan{" "}
                {fon.muaf_fon_sayisi} fonu daha var. Gerçek fon pozisyonu
                yukarıdakinden büyük olabilir.
              </p>
            )}
            <p className="tutar-yok-not">
              Kaynak: fonların KAP&apos;taki Portföy Dağılım Raporları. Raporlar
              çoğunlukla aylık ve yaklaşık bir ay geriden gelir. Fon pozisyonu
              skora girmez.
            </p>
          </section>
        )}

        <div className="liste" style={{ marginTop: 6 }}>
          {bildirimler.map((b) => (
            <Link key={b.kap_id} href={`/kap/${b.kap_id}`} className="hisse-satir">
              <span
                className="kart-ray"
                style={{ background: oranRengi(b.ciro_orani) }}
                aria-hidden="true"
              />
              <span className="hisse-satir-ic">
                <span className="hisse-satir-ust">
                  <span className="mono hisse-satir-tarih">
                    {gunEtiketi(b.yayin_zamani)}
                  </span>
                  {b.guncelleme_mi && (
                    <span className="cip cip-notr mono">GÜNCELLEME</span>
                  )}
                  <span className="kart-bos" />
                  {b.ciro_orani !== null ? (
                    <span className="hisse-satir-skor mono">
                      <strong style={{ color: oranRengi(b.ciro_orani) }}>
                        {yuzde(b.ciro_orani, 2)}
                      </strong>
                      <span style={{ color: "var(--mut-3)" }}> hasılatın</span>
                      {b.kademe ? ` · ${KADEME_ADI[b.kademe]}` : ""}
                    </span>
                  ) : (
                    <span className="cip cip-notr mono">SKOR ÜRETİLMEDİ</span>
                  )}
                </span>
                <span className="hisse-satir-is">{b.is_tanimi ?? "—"}</span>
                <span className="hisse-satir-alt">
                  Karşı taraf: {b.karsi_taraf ?? "açıklanmadı"}
                  {b.etki_skoru !== null && (
                    <> · S {sayi(b.etki_skoru)}/5</>
                  )}
                  {b.car_3g !== null && (
                    <> · 3 günlük anormal getiri {isaretliYuzde(b.car_3g)}</>
                  )}
                </span>
              </span>
            </Link>
          ))}
        </div>

        <p className="dipnot">
          Skorlar kamuya açık KAP metinleri ve finansal tablolar üzerinden
          hesaplanır. Gösterilen anormal getiriler geçmiş gözlemlerdir, tahmin
          değildir; bu sayfa yatırım tavsiyesi içermez.{" "}
          <Link href="/metodoloji">Yöntemin tamamı ve sınırları</Link>.
        </p>
      </main>
    </>
  );
}
