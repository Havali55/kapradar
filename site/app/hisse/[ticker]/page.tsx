import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import DuyuruCiroGrafigi, { type GrafikIsi } from "@/components/DuyuruCiroGrafigi";
import HisseBaglam from "@/components/HisseBaglam";
import IsListesi, { type IsOgesi } from "@/components/IsListesi";
import Kiminle from "@/components/Kiminle";
import SozKarti from "@/components/SozKarti";
import { karsiTarafMetni, ozetMetni, sayilanIs } from "@/lib/anasayfa";
import {
  cirosununKati,
  gunAy,
  kalemTutari,
  tahtaGorunumu,
  uzunTl,
} from "@/lib/bicim";
import {
  ciroAn,
  gosterilenKalemler,
  gunlukSeri,
  karsiGorunen,
  kiminle,
  seriIliskisi,
  sonOnIkiAy,
  type SeriIliskisi,
} from "@/lib/hikaye";
import {
  ciroSeriGetir,
  hisseFonGetir,
  hisseGetir,
  hisseleriGetir,
  sozVerisiGetir,
} from "@/lib/veri";

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
    description: `${sirket} (${ticker}): son 12 ayda duyurduğu yeni işler şirketin kendi yıllık cirosuna göre, ve cirosu gerçekten büyüdü mü. Fiyat tahmini içermez.`,
  };
}

// Başlık veriden (tasarım §4.2): "her gününde" iddiası ancak her gün ciro
// biliniyorsa kuruluyor (`seriIliskisi`).
const BASLIK: Record<SeriIliskisi, string> = {
  ustte: "Son bir yılın her gününde, duyurulan işler yıllık cirodan büyüktü",
  altta: "Son bir yılın her gününde, duyurulan işler yıllık cironun altında kaldı",
  karisik: "Son 12 ayda duyurulan işler ve yıllık ciro",
  "ciro-yok": "Son 12 ayda duyurulan işler",
};

export default async function HisseSayfasi({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const [bildirimler, fon, ciroSeri, soz] = await Promise.all([
    hisseGetir(ticker),
    hisseFonGetir(ticker),
    ciroSeriGetir(),
    sozVerisiGetir(),
  ]);
  if (bildirimler.length === 0) notFound();

  const simdi = Date.now();
  const sirket = bildirimler[0].sirket;
  const basamaklar = ciroSeri.filter((s) => s.ticker === ticker);
  const sayilan = bildirimler.filter(sayilanIs);
  const son12 = sonOnIkiAy(sayilan, simdi);
  const tl12 = son12.reduce((t, b) => t + (b.net_tutar_tl ?? 0), 0);
  const ttm = ciroAn(basamaklar, simdi);

  const seri = gunlukSeri(sayilan, basamaklar, simdi);
  const grafikIsleri: GrafikIsi[] = sayilan
    .filter((b) => Date.parse(b.yayin_zamani) >= seri[0].t)
    .map((b) => ({
      kap_id: b.kap_id,
      t: Date.parse(b.yayin_zamani),
      tl: b.net_tutar_tl ?? 0,
      oran: b.ciro_orani as number,
      ozet: ozetMetni(b),
      karsi: karsiTarafMetni(b),
    }));
  const grafikVar = grafikIsleri.length > 0 || seri.some((n) => n.ciro !== null);

  const isler: IsOgesi[] = bildirimler.map((b) => {
    const kalemler = gosterilenKalemler(b.tutarlar);
    const karsi = karsiTarafMetni(b);
    return {
      kap_id: b.kap_id,
      zaman: b.yayin_zamani,
      ozet: ozetMetni(b),
      karsi: karsi === null ? null : karsiGorunen(karsi),
      kalem: kalemler[0] ? kalemTutari(kalemler[0].deger, kalemler[0].para_birimi) : null,
      kalemEk: Math.max(0, kalemler.length - 1),
      tl: b.net_tutar_tl,
      oran: b.ciro_orani,
      tekrar: b.onceki_tur === "ayni_is",
      guncelleme: b.guncelleme_mi || b.onceki_tur === "guncelleme",
      duzeltme: b.onceki_tur === "duzeltme",
    };
  });

  const kim = kiminle(
    son12.map((b) => {
      const karsi = karsiTarafMetni(b);
      return { net_tutar_tl: b.net_tutar_tl, karsi: karsi === null ? null : karsiGorunen(karsi) };
    }),
  );

  // Tahta hissenin özelliği, bildirimin değil: en yeni ölçüm. Liste
  // yeniden eskiye sıralı geliyor.
  const tahtali = bildirimler.find((b) => b.tahta !== null);
  const tahta = tahtali
    ? tahtaGorunumu(
        tahtali.tahta,
        tahtali.tahta_v90,
        tahtali.tahta_v5,
        tahtali.tahta_vbts_kademe,
        tahtali.tahta_piyasa_orani ?? null,
      )
    : null;
  const ilk = bildirimler[bildirimler.length - 1].yayin_zamani;

  return (
    <main className="govde">
      <nav className="iz mono" aria-label="Konum">
        <Link href="/hisse">Hisseler</Link>
        <span aria-hidden="true">/</span>
        <span>{ticker}</span>
      </nav>

      <div className="hisse-kimlik">
        <h1 className="mono">{ticker}</h1>
        <span className="ad unvan">{sirket}</span>
        <span className="meta">
          Arşivde {bildirimler.length} yeni iş bildirimi · ilki {gunAy(ilk, true)}{" "}
          {ilk.slice(0, 4)}
          {ttm !== null && ` · son 12 aylık ciro ${uzunTl(ttm)}`}
        </span>
      </div>

      <div className="tez-blok">
        <div>
          <p className="tez">
            {son12.length === 0 ? (
              <>Son 12 ayda büyüklüğü hesaplanabilen yeni iş duyurmadı.</>
            ) : (
              <>
                Son 12 ayda <b>{son12.length} iş</b> duyurdu. Toplamı{" "}
                <b>{uzunTl(tl12)}</b>
                {ttm ? (
                  <>
                    : yıllık cirosunun <em>{cirosununKati(tl12 / ttm)}</em>.
                  </>
                ) : (
                  "."
                )}
              </>
            )}
          </p>
          <p className="tez-not">
            Duyurulan tutarlar çoğu zaman birkaç yıla yayılan sözleşmeler; ciro ise
            bir yılda gerçekleşen satış. Oran bir işin şirket için büyüklüğünü
            söyler, gelecek yılın cirosunu söylemez. O yüzden yanında gerçekleşeni
            de gösteriyoruz.
          </p>
        </div>
        {soz && <SozKarti ticker={ticker} veri={soz.veri} ozet={soz.ozet} />}
      </div>

      <div className="hisse-govde">
        <div>
          {grafikVar && (
            <section className="plaka grafik-plaka" aria-labelledby="grafik-bas">
              <div className="ust-yazi">Son 12 ayın duyuruları ve ciro</div>
              <h2 id="grafik-bas">{BASLIK[seriIliskisi(seri)]}</h2>
              <p className="aciklama">
                Mavi çizgi, o güne kadarki 12 ayda duyurulan işlerin toplamı; kesikli
                çizgi aynı gün bilinen son 12 aylık ciro. Çubuklar tek tek işler. İhale
                ve sözleşme aşamasında iki kez duyurulan iş bir kez sayılır.
              </p>
              <div className="lejant" aria-hidden="true">
                <span>
                  <i style={{ borderColor: "var(--p-duyuru)" }} />
                  12 ayda duyurulan işler
                </span>
                <span>
                  <i className="kesik" style={{ borderColor: "var(--p-ciro)" }} />
                  12 aylık ciro
                </span>
                <span>
                  <i className="cubuk-lejant" style={{ background: "var(--p-mega)" }} />
                  Mega iş
                </span>
                <span>
                  <i className="cubuk-lejant" style={{ background: "var(--p-onemli)" }} />
                  Önemli iş
                </span>
                <span>
                  <i className="cubuk-lejant" style={{ background: "var(--p-rutin)" }} />
                  Rutin iş
                </span>
              </div>
              <DuyuruCiroGrafigi seri={seri} isler={grafikIsleri} baslikId="grafik-bas" />
              <p className="alt-not">
                Tutarlar duyuru günü TCMB kuruyla TL. Ciro her finansal rapor
                yayınlandığı gün güncellenir; sonradan gelen rapor geçmişe yazılmaz.
              </p>
            </section>
          )}
          <IsListesi isler={isler} />
        </div>
        <aside className="yan">
          <Kiminle satirlar={kim} />
          <HisseBaglam
            tahta={tahta}
            tahtaGunu={tahtali ? `${gunAy(tahtali.yayin_zamani, true)} ${tahtali.yayin_zamani.slice(0, 4)}` : null}
            son12Adet={sonOnIkiAy(bildirimler, simdi).length}
            toplam={bildirimler.length}
            fon={fon}
          />
        </aside>
      </div>

      <p className="dipnot">
        Sayılar kamuya açık KAP metinleri ve finansal tablolar üzerinden
        hesaplanır; her işin kaynağı satırına tıklayınca açılan kanıt sayfasında.
        Bu sayfa yatırım tavsiyesi içermez, fiyat tahmini üretmez.{" "}
        <Link href="/metodoloji">Yöntemin tamamı ve sınırları</Link>.
      </p>
    </main>
  );
}
