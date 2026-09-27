import type { Metadata } from "next";
import HisseDizini, { type DizinOgesi } from "@/components/HisseDizini";
import { sayilanIs } from "@/lib/anasayfa";
import { istanbulGunu } from "@/lib/bicim";
import { dizinSatirlari, hareketMedyani, seansDurumu } from "@/lib/hikaye";
import {
  anaSatirlariGetir,
  ciroSeriGetir,
  limitGunleriGetir,
  reelBuyumeGetir,
} from "@/lib/veri";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Hisseler",
  description:
    "Yeni iş ilişkisi bildirimi yapan Borsa İstanbul şirketleri: son 12 ayda duyurulan işlerin yıllık ciroya oranı, enflasyondan arındırılmış ciro büyümesi ve son 20 seansın taban/tavan günleri.",
};

export default async function HisselerSayfasi() {
  const [satirlar, seri, buyumeler, limitler] = await Promise.all([
    anaSatirlariGetir(),
    ciroSeriGetir(),
    reelBuyumeGetir(),
    limitGunleriGetir(),
  ]);
  const limitHaritasi = new Map(limitler.map((l) => [l.ticker, l]));
  const medyan = hareketMedyani(limitler);
  const sonKapanis = limitler.reduce<string | null>(
    (enYeni, l) => (enYeni === null || l.son_tarih > enYeni ? l.son_tarih : enYeni),
    null,
  );
  const ogeler: DizinOgesi[] = dizinSatirlari(
    satirlar,
    seri,
    buyumeler,
    Date.now(),
    sayilanIs,
  ).map((d) => {
    const l = limitHaritasi.get(d.ticker) ?? null;
    return { ...d, seans: seansDurumu(l, medyan), hareket: l?.ort_hareket ?? null };
  });

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
          şirkette boş). &ldquo;Son 20 seans&rdquo; hissenin günlük ortalama
          hareketi ve bunun listedeki hisselerin ortasına göre kademesi
          {medyan !== null ? ` (orta %${(medyan * 100).toFixed(1).replace(".", ",")})` : ""};
          süren bir taban ya da tavan serisi varsa o yazılır. Günlük
          kapanışlardan
          {sonKapanis ? `, son kapanış ${istanbulGunu(sonKapanis + "T12:00:00Z")}` : ""}.
          Başlığa tıklayınca sıralanır.
        </p>
      </div>
      <HisseDizini satirlar={ogeler} />
    </main>
  );
}
