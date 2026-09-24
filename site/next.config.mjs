/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Veri saatlik tazeleniyor: KAP bildirimleri gün içinde düşüyor ama
  // skor/tepki hattı toplu koşuyor, dakikalık yenilemenin karşılığı yok.
  experimental: {},
  // /profil 2026-09-24'te kaldırıldı (profil LinkedIn'de). Paylaşılmış
  // eski bağlantılar 404'e değil künyenin durduğu sayfaya düşsün.
  async redirects() {
    return [{ source: "/profil", destination: "/proje-hakkinda", permanent: true }];
  },
};

export default nextConfig;
