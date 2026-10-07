"""Basamak 2 · Opus: sadece seçilen 3-5 kararı tam okur, özet + davamıza uygulanabilir ilkeler çıkarır.

Cascade (kademeli düşünme):
  1. önce --effort low (ucuz, hızlı)
  2. şu durumlarda bir kez --effort high: çıktı şemaya uymadı, model kendi güvenini "dusuk" verdi,
     ya da denetçi (Basamak 3) uydurma / yanlış atıf buldu (bu son tetiği betik/hat.py yönetir).
Kullanım: python3 betik/oku.py [low|high]   (önce betik/ele.py)  ->  cikti/ozet.json
"""
import os
import sys

from dogrula import hatalar, sema_yukle
from ortak import CIKTI, KARARLAR, json_oku, json_yaz, karar_oku, oku_metin, veri_blogu, yalin_cagri

MODEL = "opus"
METIN_SINIRI = 24000  # karar başına modele giden en fazla karakter (en uzun karar ~38 bin)


def girdi_hazirla(secilen, dava_metni, ek_not=""):
    bloklar = []
    for kid in secilen:
        k = karar_oku(os.path.join(KARARLAR, kid))
        metin = k["metin"]
        if len(metin) > METIN_SINIRI:
            metin = metin[:METIN_SINIRI] + "\n[METİN BURADA KESİLDİ: devamı modele gönderilmedi]"
        bloklar.append(veri_blogu(kid, metin))
    girdi = f"<dava>\n{dava_metni}\n</dava>\n\n" + "\n\n".join(bloklar)
    return girdi + (f"\n\n{ek_not}" if ek_not else "")


def oku_bir_kez(secilen, dava_metni, effort, ek_not=""):
    """Tek Opus çağrısı. Döner: (ozet | None, sorunlar, maliyet_kaydi)"""
    sema = sema_yukle("ozet.schema.json")
    c = yalin_cagri(MODEL, oku_metin("betik/promptlar/okuyucu.txt"), girdi_hazirla(secilen, dava_metni, ek_not),
                    sema=sema, butce_usd=1.0, effort=effort, dusunme=True)
    sorunlar = ["JSON gelmedi"] if c["veri"] is None else hatalar(c["veri"], sema)
    if not sorunlar:
        eksik = set(secilen) - {k["id"] for k in c["veri"]["kararlar"]}
        sorunlar = [f"özetlenmeyen karar: {', '.join(sorted(eksik))}"] if eksik else []
    maliyet = {"basamak": f"2 · Opus okuma (effort {effort})", "model": c["model"], "usd": c["usd"],
               "sure_sn": c["sure_sn"], "cagri": 1, "effort": effort}
    return (None if sorunlar else c["veri"]), sorunlar, maliyet


def oku(secilen, dava_metni):
    """low ile başlar; şema bozuksa ya da güven düşükse bir kez high. Döner: (ozet, maliyetler)"""
    ozet, sorunlar, m = oku_bir_kez(secilen, dava_metni, "low")
    maliyetler = [m]
    sebep = sorunlar[0] if sorunlar else ("model güveni düşük" if ozet["guven"] == "dusuk" else None)
    if sebep:
        print(f"  ! effort low yetmedi ({sebep}), effort high ile bir kez daha okunuyor.")
        ozet2, sorunlar2, m2 = oku_bir_kez(secilen, dava_metni, "high")
        maliyetler.append(m2)
        ozet = ozet2 or ozet
        if ozet is None:
            raise SystemExit(f"Opus iki denemede de geçerli özet vermedi: {sorunlar2[:2]}")
    return ozet, maliyetler


if __name__ == "__main__":
    secilen = json_oku(os.path.join(CIKTI, "eleme.json"))["secilen"]
    dava = oku_metin("veri/davamiz.md")
    if len(sys.argv) > 1 and sys.argv[1] in ("low", "high"):
        ozet, _, m = oku_bir_kez(secilen, dava, sys.argv[1])
        maliyetler = [m]
    else:
        ozet, maliyetler = oku(secilen, dava)
    json_yaz(os.path.join(CIKTI, "ozet.json"), {"ozet": ozet, "maliyet": maliyetler})
    toplam = sum(m["usd"] for m in maliyetler)
    print(f"{len(secilen)} karar okundu · güven: {ozet['guven'] if ozet else '-'} · {toplam:.4f} USD")
