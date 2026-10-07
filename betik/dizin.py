"""Basamak 0 · Betik: her karardan dizin satırı çıkarır (0 token).

Karar no, esas no, daire, tarih, dava konusu ve ilk paragraf regex ile alınır.
Yapay zekaya hitap eden gizli talimat kalıbı varsa belge "şüpheli" işaretlenir.
Kullanım: python3 betik/dizin.py [karar-klasoru]   ->  cikti/dizin.json
"""
import os
import re
import sys

from ortak import CIKTI, ENJEKSIYON, KARARLAR, json_yaz, klasor_oku

ILK_PARAGRAF = 700  # dizine giren özet uzunluğu (karakter)
KARAR_NO = re.compile(r"(?<![-\w])KARAR\s+NO\s*:\s*(\d{4}\s*/\s*\d+)", re.I)  # "Esas-Karar No" değil
ESAS_NO = re.compile(r"(?<![-\w])(?:ESAS|DOSYA)\s+NO\s*:\s*(\d{4}\s*/\s*\d+)", re.I)
TARIH = re.compile(r"KARAR\s+TARİHİ\s*:\s*(\d{2}[./]\d{2}[./]\d{4})", re.I)
DAIRE = re.compile(r"(\w+(?: \w+)?\s+BÖLGE\s+ADLİYE\s+MAHKEMESİ\s*\n?\s*(?:BAM\s+)?\d+\.\s*HUKUK\s+DAİRESİ)", re.I)
DAVA = re.compile(r"^\s*(?:DAVA|DAVANIN\s+KONUSU)\s*:\s*(.{3,120})$", re.I | re.M)
OZET_BASI = re.compile(r"Davacı[^\n.]{0,150}?özetle|DAVACININ\s+İDDİA", re.I)
UYUSMAZLIK = re.compile(r"(Dava,?\s[^.]{0,300}?(?:istem|talep|isteğ)\w*\s+ilişkin\w*)", re.I)  # "Dava, ... istemine ilişkindir"


def _bul(kalip, metin):
    m = kalip.search(metin)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def _gecerli(deger):
    """Frontmatter değeri boş ya da 'yok' ise None."""
    return deger if deger and deger != "yok" else None


def ilk_paragraf(metin):
    """Davacının iddiasının başladığı yerden ILK_PARAGRAF karakter.

    Sıra: "Davacı ... özetle" -> ilk "Davacı" -> "İDDİA" başlığı -> metnin başı (künye).
    """
    m = OZET_BASI.search(metin)
    adaylar = [m.start() if m else -1, metin.find("Davacı"), metin.find("İDDİA")]
    bas = next((a for a in adaylar if a >= 0), 0)
    return re.sub(r"\s+", " ", metin[bas:bas + ILK_PARAGRAF]).strip()


def satir_cikar(karar):
    metin, on = karar["metin"], karar["on"]
    karar_no = _bul(KARAR_NO, metin)
    satir = {
        "id": karar["id"],
        "karar_no": karar_no or _gecerli(on.get("karar_no")),
        "esas_no": _bul(ESAS_NO, metin),
        "daire": _bul(DAIRE, metin) or on.get("daire"),
        "tarih": _gecerli(on.get("karar_tarihi")) or _bul(TARIH, metin),
        "dava": _bul(DAVA, metin),
        "uyusmazlik": _bul(UYUSMAZLIK, metin),
        "ilk_paragraf": ilk_paragraf(metin),
        "kaynak_url": on.get("kaynak_url"),
        "karakter": len(metin),
        "supheli": bool(ENJEKSIYON.search(metin)),
        "notlar": [],
    }
    if satir["supheli"]:
        satir["notlar"].append("Belgede yapay zekaya hitap eden talimat kalıbı var (kural ağı).")
    if not karar_no:
        satir["notlar"].append("Metinde karar numarası yok." + (" Kaynak sistemin numarası kullanıldı."
                                                                 if satir["karar_no"] else ""))
    elif on.get("karar_no") and on["karar_no"] != karar_no.replace(" ", ""):
        satir["notlar"].append(f"Kaynak sistemin üst verisi {on['karar_no']} diyor, metin {karar_no} diyor.")
    return satir


def dizin_cikar(klasor=KARARLAR):
    kararlar = klasor_oku(klasor)
    dizin = [satir_cikar(k) for k in kararlar]
    json_yaz(os.path.join(CIKTI, "dizin.json"), dizin)
    return dizin, kararlar


if __name__ == "__main__":
    dizin, _ = dizin_cikar(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else KARARLAR)
    tam = sum(s["karakter"] for s in dizin)
    ozet = sum(len(s["ilk_paragraf"]) + len(s["dava"] or "") + len(s["uyusmazlik"] or "") for s in dizin)
    for s in dizin:
        isaret = "  ŞÜPHELİ" if s["supheli"] else ""
        print(f"  {s['id']:<26} {s['karar_no'] or '-':<11} {s['tarih'] or '-':<11} {(s['dava'] or '')[:40]}{isaret}")
    print(f"{len(dizin)} belge dizinlendi (0 token) · şüpheli: {sum(s['supheli'] for s in dizin)}"
          f" · dizin tam metnin %{100 * ozet / tam:.0f}'i kadar")
