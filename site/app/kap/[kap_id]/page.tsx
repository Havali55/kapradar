import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import BildirimDetayi from "@/components/BildirimDetayi";
import { bildirimGetir, kapIdleriGetir } from "@/lib/veri";
import { KADEME_ADI, sayi, tamTarih, yuzde } from "@/lib/bicim";

export const revalidate = 3600;

/**
 * 597 bildirimin tamamı build anında üretiliyor. Akran grubu girdileri
 * `lib/veri.ts` içinde süreç ömrü boyunca önbellekte, yani 597 sayfa
 * için tek sorgu koşuyor.
 */
export async function generateStaticParams() {
  const idler = await kapIdleriGetir();
  return idler.map((kap_id) => ({ kap_id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ kap_id: string }>;
}): Promise<Metadata> {
  const { kap_id } = await params;
  const b = await bildirimGetir(kap_id);
  if (!b) return { title: "Bildirim bulunamadı" };

  const skor =
    b.etki_skoru !== null
      ? `Büyüklük skoru ${sayi(b.etki_skoru)}/5` +
        (b.kademe ? ` · ${KADEME_ADI[b.kademe]}` : "")
      : "Skor üretilmedi (tutar ya da hasılat çözülemedi)";
  const oran =
    b.ciro_orani !== null ? ` Hasılatın ${yuzde(b.ciro_orani, 2)}'i.` : "";

  return {
    title: `${b.ticker} — ${b.is_tanimi ?? "yeni iş ilişkisi"}`,
    description: `${b.sirket}, ${tamTarih(b.yayin_zamani)}. ${skor}.${oran} Fiyat tahmini içermez.`,
  };
}

export default async function KapSayfasi({
  params,
}: {
  params: Promise<{ kap_id: string }>;
}) {
  const { kap_id } = await params;
  const b = await bildirimGetir(kap_id);
  if (!b) notFound();

  return (
    <>
      <header className="bas">
        <div className="bas-ic">
          <Link href="/" className="logo">
            <span className="logo-ad mono">
              KAP<i>·</i>RADAR
            </span>
            <span className="logo-alt mono">BİLDİRİM</span>
          </Link>
          <div className="bas-bos" />
          <Link href={`/hisse/${b.ticker}`} className="bag">
            {b.ticker} sayfası
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
          <Link href={`/hisse/${b.ticker}`}>{b.ticker}</Link>
          <span aria-hidden="true">/</span>
          <span>{tamTarih(b.yayin_zamani)}</span>
        </nav>

        <article className="kalici-detay">
          <BildirimDetayi bildirim={b} baslikEtiketi="h1" />

          <div className="panel-eylem">
            {b.kaynak_url && (
              <a
                className="bag bag-koyu"
                href={b.kaynak_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                KAP&apos;taki orijinal bildirim ↗
              </a>
            )}
            <Link className="bag" href={`/hisse/${b.ticker}`}>
              {b.ticker}&apos;nin tüm bildirimleri →
            </Link>
            <Link className="bag" href="/metodoloji">
              Yöntem ve sınırlar
            </Link>
          </div>
        </article>

        <p className="dipnot">
          Bu sayfadaki sayılar kamuya açık KAP metinleri ve finansal tablolar
          üzerinden deterministik biçimde hesaplanır; her tutarın çıkarıldığı
          ham cümle yukarıda duruyor. Yatırım tavsiyesi değildir, fiyat tahmini
          içermez.
        </p>
      </main>
    </>
  );
}
