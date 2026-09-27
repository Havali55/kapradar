import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Film",
  description:
    "KAP·RADAR'ı 50 saniyede anlatan kısa film: bir KAP haberinin şirket için ne kadar büyük olduğu, bilgi ne kadar net, fiyata bakmak anlamlı mı.",
};

/**
 * Tanıtım filmi. Dosya `public/film/` altında: 720p, 49 sn, ~2,8 MB
 * (kaynak 16 MB; crf 27). Tasarım aracının dışa aktarımı sesi yazmıyor;
 * müzik ffmpeg ile sonradan eklendi (AAC 128k, 0,4 sn giriş, son 2,5 sn
 * kısılarak çıkış). Sesli olduğu için `autoPlay` yok — tarayıcılar sesli
 * otomatik oynatmayı zaten engelliyor, kullanıcı `controls` ile başlatır.
 */
export default function FilmSayfasi() {
  return (
    <>
      <main className="govde govde-dar">
        <div className="baslik-blok">
          <p className="baslik-ust mono">50 SANİYEDE KAP·RADAR</p>
          <h1>Bir KAP haberi, şirket için ne kadar büyük?</h1>
        </div>
        <video
          className="film"
          src="/film/kap-radar.mp4"
          poster="/film/kapak.jpg"
          controls
          playsInline
          preload="metadata"
          width={1280}
          height={720}
        >
          Tarayıcınız video oynatmayı desteklemiyor.{" "}
          <a href="/film/kap-radar.mp4">Filmi indirin</a>.
        </video>
        <p className="dipnot">
          Filmdeki bütün şirketler, tutarlar ve oranlar gerçek KAP
          bildirimlerinden. Yatırım tavsiyesi değildir.
        </p>
      </main>
    </>
  );
}
