import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Büyüklük skoru — araştırma notu",
  description:
    "Skorun nasıl kurulduğu, neyi ölçtüğü ve neyi ölçmediği: yedi yıllık hacim sınaması, olay olmayan günlerle kıyas, örneklem dışında çöken bulgular ve sınırlar.",
};

/**
 * Makale tek bir yerde duruyor: `site/content/metodoloji.html`.
 * Burada TSX'e kopyalanmıyor — iki kopya olsa biri düzeltilip diğeri
 * unutulurdu. Dosyadan yalnız `<style>` ve `<main>` alınıyor; makalenin
 * kendi başlık çubuğu ve uyarı şeridi atılıyor, çünkü onları site
 * düzeni zaten veriyor.
 *
 * Stiller `.mn` altında kapsanmış durumda, site CSS'ine sızmıyor.
 */
async function makaleyiOku(): Promise<{ stil: string; govde: string }> {
  const dosya = path.join(process.cwd(), "content", "metodoloji.html");
  const ham = await readFile(dosya, "utf8");

  const stil = /<style>([\s\S]*?)<\/style>/.exec(ham)?.[1];
  const govde = /<main class="govde">([\s\S]*?)<\/main>/.exec(ham)?.[1];

  if (!stil || !govde) {
    throw new Error(
      "content/metodoloji.html beklenen yapıda değil: <style> ve <main class=\"govde\"> bulunamadı.",
    );
  }
  return { stil, govde };
}

export default async function Metodoloji() {
  const { stil, govde } = await makaleyiOku();

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: stil }} />
      <div className="mn">
        <main className="govde" dangerouslySetInnerHTML={{ __html: govde }} />
      </div>
    </>
  );
}
