import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { hisseGetir, hisseleriGetir } from "@/lib/veri";
import { skorRengi, tahtaRenk, yuzdelik } from "@/lib/skor";
import {
  KADEME_ADI,
  TAHTA_ADI,
  TAHTA_NOTU,
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
  const bildirimler = await hisseGetir(ticker);
  if (bildirimler.length === 0) notFound();

  const sirket = bildirimler[0].sirket;
  const skorlar = bildirimler
    .map((b) => b.etki_skoru)
    .filter((s): s is number => s !== null)
    .sort((a, b) => a - b);
  const medyan = skorlar.length ? yuzdelik(skorlar, 0.5) : null;
  const enBuyuk = bildirimler.reduce<(typeof bildirimler)[number] | null>(
    (e, b) =>
      b.etki_skoru !== null && (e === null || b.etki_skoru > (e.etki_skoru ?? 0))
        ? b
        : e,
    null,
  );

  // Tahta ve hasılat hissenin özelliği, bildirimin değil: en yeni
  // bildirimden okunuyor. Liste yeniden eskiye sıralı geliyor.
  const sonTahta = bildirimler.find((b) => b.tahta !== null);
  const sonHasilat = bildirimler.find((b) => b.ttm_hasilat !== null);

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
            <div className="olcu-et mono">BİLDİRİM</div>
            <div className="olcu-deger mono">{bildirimler.length}</div>
            <div className="olcu-alt">{skorlar.length} tanesi skorlanabildi</div>
          </div>
          <div className="olcu">
            <div className="olcu-et mono">MEDYAN BÜYÜKLÜK S</div>
            <div
              className="olcu-deger mono"
              style={{ color: skorRengi(medyan) }}
            >
              {medyan === null ? "—" : sayi(medyan)}
            </div>
            <div className="olcu-alt">
              {enBuyuk?.etki_skoru != null
                ? `en yükseği ${sayi(enBuyuk.etki_skoru)}`
                : "skorlanan bildirim yok"}
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
                ? `90 günde ${sonTahta.tahta_v90 ?? "—"} limit yakını gün`
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
          <p className="panel-uyari" style={{ marginBottom: 18 }}>
            {TAHTA_NOTU[sonTahta.tahta]}{" "}
            {sonTahta.tahta === "tedbirli" &&
              "Bu hissenin bildirimlerinde tepki paneli fiyat oluşumunu değil oynaklığı yansıtıyor olabilir."}
          </p>
        )}

        <div className="liste" style={{ marginTop: 6 }}>
          {bildirimler.map((b) => (
            <Link key={b.kap_id} href={`/kap/${b.kap_id}`} className="hisse-satir">
              <span
                className="kart-ray"
                style={{ background: skorRengi(b.etki_skoru) }}
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
                  {b.etki_skoru !== null ? (
                    <span className="hisse-satir-skor mono">
                      <strong style={{ color: skorRengi(b.etki_skoru) }}>
                        {sayi(b.etki_skoru)}
                      </strong>
                      <span style={{ color: "var(--mut-3)" }}> / 5,00</span>
                      {b.kademe ? ` · ${KADEME_ADI[b.kademe]}` : ""}
                    </span>
                  ) : (
                    <span className="cip cip-notr mono">SKOR ÜRETİLMEDİ</span>
                  )}
                </span>
                <span className="hisse-satir-is">{b.is_tanimi ?? "—"}</span>
                <span className="hisse-satir-alt">
                  Karşı taraf: {b.karsi_taraf ?? "açıklanmadı"}
                  {b.ciro_orani !== null && (
                    <> · hasılatın {yuzde(b.ciro_orani, 2)}&apos;i</>
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
