"""Basamak 3 · Denetçi: Opus'un verdiği her alıntıyı ve karar numarasını kaynak metne karşı doğrular.

1. Betik (0 token): karar no dizinde ve metinde var mı? Alıntı metinde kelimesi kelimesine geçiyor mu?
   Geçmiyorsa en benzer bölümü bulur (difflib). Hiç benzemiyorsa diğer kararlarda arar (yanlış atıf).
2. Sonnet (tek çağrı): betiğin bulduğu bölümle alıntıyı ve ilkeyi karşılaştırır. Küçük imla farkı mı,
   anlam mı değişmiş, ilke gerçekten mahkemenin görüşüne mi dayanıyor?
Kullanım: python3 betik/denetle.py [ozet.json]   ->  cikti/denetim.json
"""
import os
import re
import sys
from difflib import SequenceMatcher

from dogrula import hatalar, sema_yukle
from ortak import CIKTI, KARARLAR, json_oku, json_yaz, karar_oku, oku_metin, yalin_cagri

MODEL = "sonnet"
TAM_ESIK = 0.97     # bu benzerliğin üstü: alıntı metinde var
BELIRSIZ_ESIK = 0.70  # bununla TAM_ESIK arası: modele sorulur; altı: uydurma
NO = re.compile(r"\d{4}\s*/\s*\d+")
NO_ETIKET = {"gercek": "GERÇEK", "belirsiz": "İNSANA BIRAKILDI", "uydurma": "UYDURMA KARAR NO",
             "karar_yok": "KARAR KLASÖRDE YOK"}


def normal(metin):
    """Karşılaştırma için: Türkçe küçük harf, tırnak ve boşluk birliği."""
    metin = metin.replace("İ", "i").replace("I", "ı").lower()
    metin = re.sub(r"[’‘`´]", "'", metin)
    metin = re.sub(r"[“”«»]", '"', metin)
    return re.sub(r"\s+", " ", metin).strip()


def en_benzer(alinti, metin):
    """Alıntıya en çok benzeyen kelime penceresi. Döner: (oran, pencere_metni)."""
    a, kelimeler = normal(alinti), normal(metin).split(" ")
    n = max(1, len(a.split(" ")))
    if a in " ".join(kelimeler):
        return 1.0, alinti

    def oran(i):
        return SequenceMatcher(None, a, " ".join(kelimeler[i:i + n]), autojunk=False).ratio()

    adim = max(1, n // 4)
    kaba = max(range(0, max(1, len(kelimeler) - n + 1), adim), key=oran)
    ince = max(range(max(0, kaba - adim), min(len(kelimeler), kaba + adim + 1)), key=oran)
    return round(oran(ince), 3), " ".join(kelimeler[ince:ince + n])


def karar_no_kontrol(iddia, satir, metin):
    """Opus'un yazdığı karar no gerçek mi? satir: dizin satırı (yoksa None)."""
    if satir is None:
        return "karar_yok", "Bu kimlikte bir belge taranan klasörde yok."
    sayilar = [re.sub(r"\s", "", s) for s in NO.findall(iddia or "")]
    if not sayilar:
        metinde_yok = any("Metinde karar numarası yok" in n for n in satir["notlar"])
        return ("gercek", "Metinde numara yok, model de 'metinde yok' dedi.") if metinde_yok \
            else ("belirsiz", f"Model numara vermedi; dizin: {satir['karar_no']}.")
    ana = sayilar[0]
    if ana == (satir["karar_no"] or "").replace(" ", "") or ana in re.sub(r"\s", "", metin):
        return "gercek", f"{ana} metinde ve dizinde var."
    return "uydurma", f"{ana} bu kararda geçmiyor (dizin: {satir['karar_no']})."


def alinti_kontrol(alinti, kid, metinler):
    """Döner: {durum, oran, kaynak_bolum, bulundugu}"""
    oran, bolum = en_benzer(alinti, metinler.get(kid, ""))
    if oran >= TAM_ESIK:
        return {"durum": "metinde_var", "oran": oran, "kaynak_bolum": bolum, "bulundugu": kid}
    if oran >= BELIRSIZ_ESIK:
        return {"durum": "belirsiz", "oran": oran, "kaynak_bolum": bolum, "bulundugu": kid}
    for diger, metin in metinler.items():
        if diger != kid and en_benzer(alinti, metin)[0] >= TAM_ESIK:
            return {"durum": "baska_karardan", "oran": oran, "kaynak_bolum": bolum, "bulundugu": diger}
    return {"durum": "bulunamadi", "oran": oran, "kaynak_bolum": bolum, "bulundugu": None}


def betik_kontrolu(ozet, dizin):
    """0 token: her karar no ve her alıntı için kayıt üretir."""
    satirlar = {s["id"]: s for s in dizin}
    metinler = {kid: karar_oku(os.path.join(KARARLAR, kid))["metin"]
                for kid in {k["id"] for k in ozet["kararlar"]} if kid in satirlar}
    kayitlar, numaralar = [], []
    for k in ozet["kararlar"]:
        durum, aciklama = karar_no_kontrol(k["karar_no"], satirlar.get(k["id"]), metinler.get(k["id"], ""))
        numaralar.append({"id": k["id"], "iddia": k["karar_no"], "durum": durum, "aciklama": aciklama,
                          "etiket": NO_ETIKET[durum]})
        for ilke in k["ilkeler"]:
            kontrol = alinti_kontrol(ilke["alinti"], k["id"], metinler)
            kayitlar.append({"no": len(kayitlar) + 1, "id": k["id"], "ilke": ilke["ilke"],
                             "alinti": ilke["alinti"], **kontrol})
    return kayitlar, numaralar


def model_kontrolu(kayitlar):
    """Sonnet'e betiğin bulduğu bölümleri gösterir. 'bulunamadi' olanlar sorulmaz (zaten uydurma)."""
    sorulacak = [k for k in kayitlar if k["durum"] != "bulunamadi"]
    if not sorulacak:
        return {}, {"basamak": "3 · Sonnet denetçi", "model": "-", "usd": 0.0, "sure_sn": 0.0, "cagri": 0}
    girdi = "\n\n".join(
        f'<kontrol no="{k["no"]}">\n<ilke>{k["ilke"]}</ilke>\n<alinti>{k["alinti"]}</alinti>\n'
        f'<kaynak>{k["kaynak_bolum"]}</kaynak>\n</kontrol>' for k in sorulacak)
    sema = sema_yukle("denetim.schema.json")
    c = yalin_cagri(MODEL, oku_metin("betik/promptlar/denetci.txt"), girdi, sema=sema, butce_usd=0.3)
    gecerli = c["veri"] is not None and not hatalar(c["veri"], sema)
    if not gecerli:
        print("  ! Denetçi modeli geçerli cevap vermedi; belirsiz alıntılar insana bırakılıyor.")
    cevap = {x["no"]: x for x in c["veri"]["kontroller"]} if gecerli else {}
    return cevap, {"basamak": "3 · Sonnet denetçi", "model": c["model"], "usd": c["usd"],
                   "sure_sn": c["sure_sn"], "cagri": 1}


SONUCLAR = {  # (betik durumu, model alıntı durumu) -> karar
    "bulunamadi": ("UYDURMA ALINTI", "Alıntı kaynak kararın metninde yok."),
    "baska_karardan": ("YANLIŞ ATIF", "Alıntı gerçek ama başka bir karardan."),
}


def hukum(k, m):
    """Betik + model sonucunu tek etikete çevirir. Döner: (etiket, sorunlu_mu, aciklama)"""
    if k["durum"] in SONUCLAR:
        etiket, aciklama = SONUCLAR[k["durum"]]
        return etiket, True, aciklama
    if m is None:
        return ("DOĞRULANDI (betik)", False, "Model cevabı yok; alıntı metinde birebir var.") \
            if k["durum"] == "metinde_var" else ("İNSANA BIRAKILDI", True, "Alıntı birebir değil, model kontrol edemedi.")
    if k["durum"] == "belirsiz" and m["alinti_durumu"] == "anlam_farkli":
        return "ÇARPITILMIŞ ALINTI", True, m["aciklama"]
    if m["destek"] == "desteklemiyor":
        return "İLKEYİ DESTEKLEMİYOR", True, m["aciklama"]
    etiket = "DOĞRULANDI" if k["durum"] == "metinde_var" else "KÜÇÜK FARK"
    return (etiket + (" (kısmen destekliyor)" if m["destek"] == "kismen" else ""), False, m["aciklama"])


def denetle(ozet, dizin):
    kayitlar, numaralar = betik_kontrolu(ozet, dizin)
    cevap, maliyet = model_kontrolu(kayitlar)
    for k in kayitlar:
        k["etiket"], k["sorunlu"], k["aciklama"] = hukum(k, cevap.get(k["no"]))
    sorunlu = [k for k in kayitlar if k["sorunlu"]] + [n for n in numaralar if n["durum"] in ("uydurma", "karar_yok")]
    return {"alintilar": kayitlar, "karar_nolari": numaralar, "sorunlu_sayisi": len(sorunlu),
            "maliyet": maliyet}


if __name__ == "__main__":
    yol = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CIKTI, "ozet.json")
    d = denetle(json_oku(yol)["ozet"], json_oku(os.path.join(CIKTI, "dizin.json")))
    json_yaz(os.path.join(CIKTI, "denetim.json"), d)
    for n in d["karar_nolari"]:
        print(f"  karar no  {n['id']:<24} {n['durum']:<9} {n['aciklama']}")
    for k in d["alintilar"]:
        print(f"  alıntı {k['no']:>2} {k['id']:<24} %{k['oran'] * 100:.0f} {k['etiket']}")
    print(f"Sorunlu: {d['sorunlu_sayisi']} · {d['maliyet']['usd']:.4f} USD")
