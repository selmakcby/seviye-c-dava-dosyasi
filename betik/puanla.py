"""Doğruluk: eleme sonucunu veri/cevap-anahtari.json ile karşılaştırır.

Kullanım: python3 betik/puanla.py [cikti/eleme.json]
"""
import json
import os
import sys

from ortak import CIKTI, KOK


def anahtar_oku(yol=os.path.join(KOK, "veri", "cevap-anahtari.json")):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def puanla(ilgili_tahmin, supheli_tahmin, secilen=(), sadece=None):
    """ilgili_tahmin: id -> bool, supheli_tahmin: id kümesi. sadece: puanlanacak id'ler (naif alt küme için)."""
    anahtar = anahtar_oku()
    cevaplar = {i: c for i, c in anahtar["cevaplar"].items() if sadece is None or i in sadece}
    yanlislar = [(i, ilgili_tahmin.get(i), c["ilgili"]) for i, c in sorted(cevaplar.items())
                 if bool(ilgili_tahmin.get(i)) != c["ilgili"]]
    tuzaklar = [i for i, c in cevaplar.items() if c.get("supheli")]
    hedef = anahtar["davamiz_alt_konu"]
    return {"dogru": len(cevaplar) - len(yanlislar), "toplam": len(cevaplar), "yanlislar": yanlislar,
            "tuzak_yakalanan": sum(1 for i in tuzaklar if i in supheli_tahmin), "tuzak_toplam": len(tuzaklar),
            "secilen_isabet": sum(1 for i in secilen if cevaplar.get(i, {}).get("alt_konu") == hedef),
            "secilen_toplam": len(secilen)}


if __name__ == "__main__":
    yol = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CIKTI, "eleme.json")
    with open(yol, encoding="utf-8") as f:
        e = json.load(f)
    p = puanla({i: k["ilgili"] for i, k in e["eleme"].items()},
               {i for i, k in e["eleme"].items() if k["supheli"]}, e["secilen"])
    print(f"Eleme doğruluğu: {p['dogru']}/{p['toplam']} · tuzak yakalanan: {p['tuzak_yakalanan']}/{p['tuzak_toplam']}"
          f" · seçilenlerden davamızın alt konusunda olan: {p['secilen_isabet']}/{p['secilen_toplam']}")
    for i, t, d in p["yanlislar"]:
        print(f"  {i}: tahmin ilgili={t}, doğrusu ilgili={d}")
