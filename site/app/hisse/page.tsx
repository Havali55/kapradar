import type { Metadata } from "next";
import HisseDizini, { type DizinOgesi } from "@/components/HisseDizini";
import { sayilanIs } from "@/lib/anasayfa";
import { dizinSatirlari } from "@/lib/hikaye";
import { anaSatirlariGetir, ciroSeriGetir, reelBuyumeGetir } from "@/lib/veri";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Hisseler",
  description:
    "Yeni iş ilişkisi bildirimi yapan Borsa İstanbul şirketleri: son 12 ayda duyurulan işlerin yıllık ciroya oranı ve enflasyondan arındırılmış ciro büyümesi.",
};

export default async function HisselerSayfasi() {
  const [satirlar, seri, buyumeler] = await Promise.all([
    anaSatirlariGetir(),
    ciroSeriGetir(),
    reelBuyumeGetir(),
  ]);
  const ogeler: DizinOgesi[] = dizinSatirlari(
    satirlar,
    seri,
    buyumeler,
    Date.now(),
    sayilanIs,
  );

  return (
    <main className="govde">
      <div className="baslik-blok">
        <p className="baslik-ust mono">HİSSELER</p>
        <h1>{ogeler.length} şirket</h1>
        <p>
          Arşivde yeni iş ilişkisi bildirimi olan her şirket. &ldquo;Duyurulan /
          ciro&rdquo;, son 12 ayda duyurulan işlerin toplamının şirketin son 12
          aylık cirosuna oranı; &ldquo;reel ciro büyümesi&rdquo; son raporun
          enflasyondan arındırılmış büyümesi (raporunu yeniden ifade etmeyen
          şirkette boş). Başlığa tıklayınca sıralanır.
        </p>
      </div>
      <HisseDizini satirlar={ogeler} />
    </main>
  );
}
