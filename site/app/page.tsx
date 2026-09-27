// GEÇİCİ (site v3, Faz 2): ana sayfa Faz 3'te yeniden yazılana kadar akışı
// gösteriyor. Dal Faz 5'ten önce yayına çıkmıyor.
export { default } from "./akis/page";

export const revalidate = 3600;
