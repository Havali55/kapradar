"""Karşı taraf alanı: gerçek bir isim mi, anonim bir tanım mı?

Bütün örnekler KAP'taki gerçek "karşı taraf" değerleri (2024-09 →
2026-09 arşivi). 2026-09-24'e kadar alan boş değilse "açık" sayılıyordu;
"." 25, "Uluslararası Müşteri" 29, "Müşteri" 16 bildirimde açık diye
skorlanmıştı.
"""

import pytest

from kap_radar.karsi_taraf import karsi_taraf_acik

ANONIM = [
    ".",
    "-",
    "Uluslararası Müşteri",
    "Müşteri",
    "Yurt Dışı Yerleşik Şirket",
    "Yurt İçi Yerleşik Şirket",
    "YURT İÇİNDE FAALİYET GÖSTEREN İŞLETME",
    "Yurtdışı Yerleşik Müşteri",
    "Muhtelif Müşteriler",
    "Türkiye'de Yerleşik Bir Banka",
    "Türkiye Genelindeki 5 Satış Noktası",
    "Almanya merkezli bir şirket",
    "Kırgızistan'da bulunan Enerji Firması",
    "Kuzay Makedonya'da Yerleşik Bir Firma",
    "ABD 'de Yerleşik Firma",
    "Porto Riko'da yerleşik firma",
    "Yurtiçi yerleşik şirket - Yurtdışında yerleşik şirket",
    "Posta ve lojistik sektörüne hizmet veren uluslararası servis sağlayıcı bir şirket",
    "Dünyanın en büyük akaryakıt dağıtım şirketi",
    "Türkiye'nin En Köklü ve Alman Ortaklı Premium Otomotiv Markası",
    "Yurt içi beyaz eşya üreticileri",
    "Aşağıda detayları açıklanmıştır.",
    "Bulunmamaktadır.",
    "Üç yeni iş ilişkisi",
    "Türkiye'de yerleşik Irak menşeli bir firma",
    "Yurtdışında Yerleşik Teknoloji Şirketi",
    "Bir Telekomünikasyon Şirketi",
    "Kamu Kurumu",
    "Bir Kamu Kurumu",
    "Yurt İçinde Faaliyet Gösteren Bir Kamu Kurumu",
]

ISIMLI = [
    "İstanbul Takas ve Saklama Bankası A.Ş.",
    "Trafigura Pte. Ltd. (Yurt Dışında Yerleşik)",
    "Volkswagen A.G.",
    "GE (General Electric)",
    "Noatum Logistics",
    "Nokia",
    "Temu",
    "Seven Eleven",
    "Qatar Energy",
    "Hitachi Energy",
    "Türkiye Futbol Federasyonu",
    "Yükseköğretim Kurulu",
    "Türkiye Elektrik Dağıtım Anonim Şirketi",
    "Bangladeş Silahlı Kuvvetleri",
    "Posta ve Telgraf Teşkilatı",
    "Emniyet Genel Müdürlüğü",
    "Aydın İl Sağlık Müdürlüğü",
    "Celikler-Fernas-Güryapı Adi Ortaklığı",
    "Pharmaget Sp. İlaç Dağıtım Şirketi ve Zeus Ecza Deposu",
    "Google ve Şirketleri (\"Google Cloud\")",
    "Costco Wholesale Korea",
    # "Kurumu" ile biten ama gerçek kurum adı olanlar: anonim "Kamu Kurumu"
    # ile karışmamalı.
    "Türkiye İş Kurumu",
    "Mesleki Yeterlilik Kurumu",
    "T.C Sosyal Güvenlik Kurumu",
]


@pytest.mark.parametrize("ad", ANONIM)
def test_anonim_tanim_acik_sayilmaz(ad):
    assert karsi_taraf_acik(ad) is False


@pytest.mark.parametrize("ad", ISIMLI)
def test_gercek_isim_acik_sayilir(ad):
    assert karsi_taraf_acik(ad) is True


@pytest.mark.parametrize("ad", [None, "", "   "])
def test_bos_alan_acik_sayilmaz(ad):
    assert karsi_taraf_acik(ad) is False
