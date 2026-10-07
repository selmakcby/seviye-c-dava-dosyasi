"""Basamak 1 · Haiku: dizin satırlarını konu etiketiyle sınıflar, "davamızla ilgili mi" diye eler.

- Tek toplu çağrı, araç yok, düşünme kapalı; model tam metni değil, sadece dizini görür.
- Çıktı betik/sema/eleme.schema.json ile doğrulanır; bozuksa bir kez tekrar.
- Kural ağı: dizinde şüpheli işaretli belge, Haiku ne derse desin şüpheli kalır ve okunmaz.
- En yüksek benzerlikli SECIM_SAYISI karar Basamak 2'ye (Opus) gider.
Kullanım: python3 betik/ele.py   (önce betik/dizin.py)  ->  cikti/eleme.json
"""
import os
from datetime import datetime

from dogrula import hatalar, sema_yukle
from ortak import CIKTI, json_oku, json_yaz, oku_metin, veri_blogu, yalin_cagri

MODEL = "haiku"
SECIM_SAYISI = 3  # pahalı modelin okuyacağı karar sayısı (3-5 arası; her ek karar ~0,1 USD Opus)


def dizin_blogu(s):
    satirlar = [f"Karar no: {s['karar_no'] or '-'}", f"Daire: {s['daire'] or '-'}",
                f"Tarih: {s['tarih'] or '-'}", f"Dava: {s['dava'] or '-'}",
                f"Uyuşmazlık: {s['uyusmazlik'] or '-'}", f"İlk paragraf: {s['ilk_paragraf']}"]
    return veri_blogu(s["id"], "\n".join(satirlar))


def _cagir(girdi, sema):
    c = yalin_cagri(MODEL, oku_metin("betik/promptlar/eleyici.txt"), girdi, sema=sema, butce_usd=0.3)
    sorunlar = ["JSON gelmedi"] if c["veri"] is None else hatalar(c["veri"], sema)
    return c, sorunlar


def _tarih(t):
    for bicim in ("%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(t or "", bicim)
        except ValueError:
            continue
    return datetime.min


def birlestir(dizin, gelen):
    """Model cevabını dizinle birleştirir; eksik kalanı 'insana bırak' diye işaretler."""
    sonuc = {}
    for s in dizin:
        k = gelen.get(s["id"])
        if k is None:
            k = {"konu": "diger", "ilgili": False, "benzerlik": 0, "supheli": False,
                 "gerekce": "Model bu belge için cevap vermedi, insana bırakıldı.", "insan": True}
        if s["supheli"] and not k["supheli"]:
            k = {**k, "supheli": True, "ilgili": False, "benzerlik": 0,
                 "gerekce": "Kural ağı: belgede gizli talimat kalıbı var (Haiku kaçırdı)."}
        sonuc[s["id"]] = {**k, "id": s["id"]}
    return sonuc


def secim_yap(eleme, dizin, adet=SECIM_SAYISI):
    tarih = {s["id"]: _tarih(s["tarih"]) for s in dizin}
    adaylar = [k for k in eleme.values() if k["ilgili"] and not k["supheli"]]
    adaylar.sort(key=lambda k: (-k["benzerlik"], -tarih[k["id"]].toordinal()))  # eşitlikte yeni karar önce
    return [k["id"] for k in adaylar[:adet]]


def ele(dizin, dava_metni, adet=SECIM_SAYISI):
    sema = sema_yukle("eleme.schema.json")
    girdi = f"<dava>\n{dava_metni}\n</dava>\n\n" + "\n\n".join(dizin_blogu(s) for s in dizin)
    c, sorunlar = _cagir(girdi, sema)
    usd, sure, cagri = c["usd"], c["sure_sn"], 1
    if sorunlar:
        print(f"  ! Haiku çıktısı şemaya uymadı ({sorunlar[0]}), bir kez tekrar deniyorum.")
        c, sorunlar = _cagir(girdi + "\n\nÖNCEKİ ÇIKTIN GEÇERSİZDİ. Her karar için tam kayıt yaz.", sema)
        usd, sure, cagri = usd + c["usd"], sure + c["sure_sn"], 2
    gelen = {} if sorunlar else {k["id"]: k for k in c["veri"]["kararlar"]}
    eleme = birlestir(dizin, gelen)
    secilen = secim_yap(eleme, dizin, adet)
    maliyet = {"basamak": "1 · Haiku eleme", "model": c["model"], "usd": usd,
               "sure_sn": round(sure, 1), "cagri": cagri}
    return eleme, secilen, maliyet


if __name__ == "__main__":
    dizin = json_oku(os.path.join(CIKTI, "dizin.json"))
    eleme, secilen, m = ele(dizin, oku_metin("veri/davamiz.md"))
    json_yaz(os.path.join(CIKTI, "eleme.json"), {"eleme": eleme, "secilen": secilen, "maliyet": m})
    ilgili = sum(k["ilgili"] for k in eleme.values())
    print(f"{len(eleme)} belge · ilgili {ilgili} · şüpheli {sum(k['supheli'] for k in eleme.values())}"
          f" · seçilen: {', '.join(secilen)} · {m['usd']:.4f} USD, {m['sure_sn']} sn")
