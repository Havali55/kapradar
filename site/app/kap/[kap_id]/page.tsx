import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import BildirimDetayi from "@/components/BildirimDetayi";
import IsSatiri from "@/components/IsSatiri";
import { anaSatirlariGetir, bildirimGetir, kapIdleriGetir } from "@/lib/veri";
import { KADEME_ADI, tamTarih, yuzdeIyelik } from "@/lib/bicim";

export const revalidate = 3600;

/** Bildirimlerin tamamı build anında üretiliyor. */
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

  // Kademe ciro oranından (kart ve filtreyle aynı kaynak).
  const buyukluk =
    b.ciro_orani !== null && b.kademe
      ? `Hasılatın ${yuzdeIyelik(b.ciro_orani, 2)} · ${KADEME_ADI[b.kademe]}`
      : "Büyüklük hesaplanamadı (tutar ya da hasılat çözülemedi)";

  return {
    title: `${b.ticker} — ${b.is_tanimi ?? "yeni iş ilişkisi"}`,
    description: `${b.sirket}, ${tamTarih(b.yayin_zamani)}. ${buyukluk}. Fiyat tahmini içermez.`,
  };
}

export default async function KapSayfasi({
  params,
}: {
  params: Promise<{ kap_id: string }>;
}) {
  const { kap_id } = await params;
  const [b, satirlar] = await Promise.all([bildirimGetir(kap_id), anaSatirlariGetir()]);
  if (!b) notFound();
  // Şirketin diğer işleri: önbellekteki ana satırlardan (yeniden eskiye).
  const digerleri = satirlar
    .filter((s) => s.ticker === b.ticker && s.kap_id !== b.kap_id)
    .slice(0, 5);

  return (
    <>
      <main className="govde govde-dar">
        <nav className="iz mono" aria-label="Konum">
          <Link href="/akis">Akış</Link>
          <span aria-hidden="true">/</span>
          <Link href={`/hisse/${b.ticker}`}>{b.ticker}</Link>
          <span aria-hidden="true">/</span>
          <span>{tamTarih(b.yayin_zamani)}</span>
        </nav>
        <Link className="hikaye-bag" href={`/hisse/${b.ticker}`}>
          <span className="mono">{b.ticker}</span> hikâyesi: son 12 ayın işleri ve
          cirosu →
        </Link>

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
            {/* Sabit "'nin" eki çoğu ticker'da yanlıştı (ASELS'in, THYAO'nun). */}
            <Link className="bag" href={`/hisse/${b.ticker}`}>
              {b.ticker} sayfası →
            </Link>
            <Link className="bag" href="/metodoloji">
              Yöntem ve sınırlar
            </Link>
          </div>
        </article>

        {digerleri.length > 0 && (
          <section className="diger-isler" aria-labelledby="diger-bas">
            <h2 id="diger-bas">Şirketin diğer işleri</h2>
            <div className="is-satirlari">
              {digerleri.map((s) => (
                <IsSatiri key={s.kap_id} s={s} />
              ))}
            </div>
            <Link className="diger-hepsi" href={`/hisse/${b.ticker}`}>
              Hepsi ve {b.ticker} hikâyesi →
            </Link>
          </section>
        )}

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
