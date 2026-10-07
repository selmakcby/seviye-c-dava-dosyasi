"""Denetçi testi: gerçek bir Opus özetine KASTEN uydurma atıflar ekler, denetçinin yakalayıp yakalamadığına bakar.

ozet-gercek.json : hattın gerçek bir koşusunda Opus'un yazdığı özet (değiştirilmeden saklandı)
Eklenen 4 hata (her biri gerçek hayatta görülen bir atıf hatası türü):
  1. UYDURMA ALINTI   : hiçbir kararda geçmeyen, kulağa hukuki gelen bir cümle
  2. ÇARPITILMIŞ ALINTI: gerçek bir alıntının anlamı ters çevrildi ("sınırlı olarak" -> "sınırlı olmaksızın")
  3. UYDURMA KARAR NO : gerçek bir kararın numarası başka bir numarayla değiştirildi
  4. VAR OLMAYAN KARAR: klasörde hiç olmayan bir karar, kendi alıntısıyla
Kullanım: python3 olc/uydurma-atif-testi/test.py    (Sonnet tek çağrı, ~0,03 USD)
"""
import copy
import json
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
sys.path.insert(0, os.path.join(KOK, "betik"))
from denetle import denetle  # noqa: E402
from dizin import dizin_cikar  # noqa: E402

UYDURMA = ("Alt işveren, işçinin asıl işveren nezdindeki tüm çalışma süresine ait kıdem tazminatından, "
           "kendi çalıştırdığı süreyle sınırlı olmaksızın tek başına ve tamamen sorumludur.")
ASIL, CARPIK = "dönemle sınırlı olarak sorumluluğunun bulunduğu", "dönemle sınırlı olmaksızın tamamından sorumluluğunun bulunduğu"
SAHTE_NO = "2019/8812"
SAHTE_KARAR = {"id": "41-emsal-2021-4471.md", "karar_no": "2021/4471", "daire": "Yargıtay 9. Hukuk Dairesi",
               "tarih": "12.03.2021", "ozet": "Uydurma karar.",
               "ilkeler": [{"ilke": "Hakedişten kesinti her durumda hukuka aykırıdır.", "etki": "lehe",
                            "alinti": "Asıl işverenin yükleniciye ait hakedişten kıdem tazminatı kesintisi yapması hiçbir koşulda mümkün değildir."}]}


def bozulmus_ozet(gercek):
    """Gerçek özetin kopyasına 4 hata ekler. Döner: (ozet, beklenenler)"""
    o = copy.deepcopy(gercek)
    k0, k1, k2 = o["kararlar"][0], o["kararlar"][1], o["kararlar"][2]
    k0["ilkeler"].append({"ilke": "Alt işveren kıdem tazminatının tamamından sorumludur.", "alinti": UYDURMA, "etki": "aleyhe"})
    carpik = next(i for i in k1["ilkeler"] if ASIL in i["alinti"])
    carpik["alinti"] = carpik["alinti"].replace(ASIL, CARPIK)
    carpik["ilke"] = "Yüklenici, çalıştırmadığı dönem dahil kıdem tazminatının tamamından sorumludur."
    eski_no, k2["karar_no"] = k2["karar_no"], SAHTE_NO
    o["kararlar"].append(SAHTE_KARAR)
    beklenen = [("1 · uydurma alıntı", "alinti", UYDURMA), ("2 · çarpıtılmış alıntı", "alinti", carpik["alinti"]),
                ("3 · uydurma karar no", "no", k2["id"]), ("4 · var olmayan karar", "no", SAHTE_KARAR["id"])]
    return o, beklenen, eski_no


def yakalandi_mi(d, tur, anahtar):
    if tur == "alinti":
        k = next(k for k in d["alintilar"] if k["alinti"] == anahtar)
        return k["sorunlu"], k["etiket"]
    n = next(n for n in d["karar_nolari"] if n["id"] == anahtar)
    return n["durum"] in ("uydurma", "karar_yok"), n["etiket"]


def rapor_yaz(satirlar, d, eski_no):
    yakalanan = sum(1 for s in satirlar if s[1])
    gercek_sorunsuz = sum(1 for k in d["alintilar"] if not k["sorunlu"])
    metin = ["# Uydurma atıf testi", "",
             f"Gerçek Opus özetine 4 kasıtlı hata eklendi. Denetçi **{yakalanan}/4** yakaladı.",
             f"Özetteki gerçek alıntılardan {gercek_sorunsuz} tanesi temiz geçti (yanlış alarm yok mu, aşağıda).", "",
             "| Eklenen hata | Yakalandı mı | Denetçinin etiketi |", "|---|---|---|"]
    metin += [f"| {ad} | {'evet' if ok else '**HAYIR**'} | {etiket} |" for ad, ok, etiket in satirlar]
    metin += ["", f"3 numaralı hatada gerçek numara {eski_no} idi, {SAHTE_NO} yazıldı.", "",
              "## Bütün alıntılar", "", "| # | Karar | Benzerlik | Etiket | Not |", "|---|---|---|---|---|"]
    metin += [f"| {k['no']} | {k['id']} | %{k['oran'] * 100:.0f} | {k['etiket']} | {k['aciklama']} |" for k in d["alintilar"]]
    metin += ["", f"Denetçi maliyeti: {d['maliyet']['usd']:.4f} USD ({d['maliyet']['model']})"]
    with open(os.path.join(BURASI, "SONUC.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(metin) + "\n")
    return yakalanan


if __name__ == "__main__":
    with open(os.path.join(BURASI, "ozet-gercek.json"), encoding="utf-8") as f:
        gercek = json.load(f)["ozet"]
    dizin, _ = dizin_cikar()
    ozet, beklenen, eski_no = bozulmus_ozet(gercek)
    d = denetle(ozet, dizin)
    satirlar = [(ad, *yakalandi_mi(d, tur, anahtar)) for ad, tur, anahtar in beklenen]
    for ad, ok, etiket in satirlar:
        print(f"  {ad:<24} {'YAKALANDI' if ok else 'KAÇTI':<10} {etiket}")
    yakalanan = rapor_yaz(satirlar, d, eski_no)
    print(f"Denetçi {yakalanan}/4 hatayı yakaladı · rapor: olc/uydurma-atif-testi/SONUC.md")
    sys.exit(0 if yakalanan == 4 else 1)
