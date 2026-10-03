import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Film",
  description:
    "KAP·RADAR'ı 34 saniyede anlatan kısa film: aynı tutar, iki şirket için bambaşka ağırlık. Yeni iş duyuruları şirketin kendi cirosuna göre.",
};

/**
 * Tanıtım filmi. Dosya `public/film/` altında: 720×720, 34 sn, ~4,2 MB.
 * Remotion ile kodla üretildi. Müziği lisanslı (Epidemic Sound), bu yüzden
 * film dosyası ve kaynağı açık depoya girmiyor (bkz. `araclar/acik_depo`).
 * Sesli olduğu için `autoPlay` yok: tarayıcılar sesli otomatik oynatmayı
 * zaten engelliyor, kullanıcı `controls` ile başlatır.
 */
export default function FilmSayfasi() {
  return (
    <>
      <main className="govde govde-dar">
        <div className="baslik-blok">
          <p className="baslik-ust mono">34 SANİYEDE KAP·RADAR</p>
          <h1>Bir KAP haberi, şirket için ne kadar büyük?</h1>
        </div>
        <video
          className="film"
          src="/film/kap-radar-film.mp4"
          poster="/film/kap-radar-film.jpg"
          controls
          playsInline
          preload="metadata"
          width={720}
          height={720}
          style={{ maxWidth: 640, marginInline: "auto" }}
        >
          Tarayıcınız video oynatmayı desteklemiyor.{" "}
          <a href="/film/kap-radar-film.mp4">Filmi indirin</a>.
        </video>
        <p className="dipnot">
          Filmdeki bütün şirketler, tutarlar ve oranlar gerçek KAP
          bildirimlerinden. Film kodla üretildi (Remotion); müzik:
          &ldquo;Riddle&rdquo;, Shiruky (Epidemic Sound). Yatırım tavsiyesi
          değildir.
        </p>
      </main>
    </>
  );
}
