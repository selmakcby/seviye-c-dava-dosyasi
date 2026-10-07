"""Örnek veriyi toplar: UYAP Emsal Karar Arama'dan herkese açık, anonim kararlar.

Kullanım:
  python3 araclar/indir.py               # veri/kaynak-listesi.json'daki kararları indirir
  python3 araclar/indir.py --onbellek    # ağa çıkmaz, sadece .onbellek/ içinden yeniden yazar

Nezaket kuralları (kaynak bir kamu hizmeti, yükü bizim değil):
  - istekler arası 4 sn bekleme; 429 gelirse 60 sn geri çekilip bir kez daha denenir
  - en fazla ISTEK_TAVANI istek; indirilen ham cevap .onbellek/ içinde tutulur, tekrar istenmez
  - sadece arama sonucunda açık olan kararlar; giriş, CAPTCHA ya da engel aşılmaz
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONBELLEK = os.path.join(KOK, ".onbellek")
LISTE = os.path.join(KOK, "veri", "kaynak-listesi.json")
HEDEF = os.path.join(KOK, "veri", "kararlar")
DOKUMAN_URL = "https://emsal.uyap.gov.tr/getDokuman?id={}"
UA = "Mozilla/5.0 (seviye-c-dava-dosyasi; egitim amacli ornek)"
BEKLEME_SN = 4  # 1,5 sn'de 9 istekten sonra 429 (Too Many Requests) aldık
ISTEK_TAVANI = 60

# Kararlar zaten anonim ("..." ile). Yine de kalmış olabilecek kişisel veriyi kapatırız.
MASKELER = [
    (re.compile(r"\b[1-9]\d{10}\b"), "[…]"),                                   # TC kimlik no biçimi
    (re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b"), "[…]"),                # IBAN
    (re.compile(r"\b0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b"), "[…]"),     # cep telefonu
    (re.compile(r"\b(Av\.|Avukat)\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zçğıöşüÇĞİÖŞÜ]+)+"),
     r"\1 […]"),                                                               # vekil adı
    (re.compile(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+ (?:Cad\.|Caddesi|Sokak|Sok\.)(?: [A-ZÇĞİÖŞÜ][a-zçğıöşü]+ (?:Sokak|Sok\.))?"
                r"(?: ?No ?: ?\d+[/\d]*)?"), "[…]"),                                 # sokak / cadde adresi
    (re.compile(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+ (Mahallesi|Mah\.)"), r"[…] \1"),   # mahalle adı
]


def indir(karar_id, sayac):
    """Ham JSON'u önbellekten okur, yoksa ağdan bir kez indirir."""
    yol = os.path.join(ONBELLEK, f"{karar_id}.json")
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    if sayac[0] >= ISTEK_TAVANI:
        raise SystemExit(f"İstek tavanı ({ISTEK_TAVANI}) doldu, duruyorum.")
    veri = istek_at(DOKUMAN_URL.format(karar_id), sayac)
    time.sleep(BEKLEME_SN)
    os.makedirs(ONBELLEK, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False)
    return veri


def istek_at(url, sayac, deneme=2):
    """Tek GET isteği. 429 (çok istek) gelirse 60 sn bekler ve bir kez daha dener."""
    for kalan in range(deneme, 0, -1):
        sayac[0] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as c:
                return json.load(c)
        except urllib.error.HTTPError as hata:
            if hata.code != 429 or kalan == 1:
                raise SystemExit(f"İndirilemedi ({url}): {hata}")
            print("  … 429 (çok istek), 60 sn bekleniyor")
            time.sleep(60)
        except Exception as hata:  # ağ hatası: açık mesajla dur
            raise SystemExit(f"İndirilemedi ({url}): {hata}")


def metne_cevir(ham_html):
    """Karar HTML'ini düz metne çevirir; <br> ve </p> satır sonu olur."""
    t = re.sub(r"(?i)<br\s*/?>|</p>", "\n", ham_html)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    satirlar = [re.sub(r"[ \t\xa0]+", " ", s).strip() for s in t.splitlines()]
    return "\n".join(s for s in satirlar if s)


def maskele(metin):
    """Kişisel veri kalıplarını […] ile kapatır. Döner: (metin, kapatılan_sayısı)."""
    toplam = 0
    for kalip, yerine in MASKELER:
        metin, n = kalip.subn(yerine, metin)
        toplam += n
    return metin, toplam


def dosya_yaz(sira, kayit, metin, erisim):
    karar_no = kayit["kararNo"]
    ad = f"{sira:02d}-emsal-{karar_no.replace('/', '-')}.md"
    on = ["---", f"kaynak: UYAP Emsal Karar Arama (emsal.uyap.gov.tr)",
          f"kaynak_url: {DOKUMAN_URL.format(kayit['id'])}", f"daire: {kayit['daire']}",
          f"esas_no: {kayit['esasNo']}", f"karar_no: {karar_no}",
          f"karar_tarihi: {kayit['kararTarihi']}", f"erisim_tarihi: {erisim}", "---", ""]
    with open(os.path.join(HEDEF, ad), "w", encoding="utf-8") as f:
        f.write("\n".join(on) + metin + "\n")
    return ad


def calistir(sadece_onbellek=False):
    with open(LISTE, encoding="utf-8") as f:
        liste = json.load(f)
    os.makedirs(HEDEF, exist_ok=True)
    sayac, maskelenen = [0], 0
    for sira, kayit in enumerate(liste["kararlar"], start=1):
        if sadece_onbellek and not os.path.exists(os.path.join(ONBELLEK, f"{kayit['id']}.json")):
            raise SystemExit(f"Önbellekte yok: {kayit['id']}")
        ham = indir(kayit["id"], sayac)
        metin, n = maskele(metne_cevir(ham.get("data") or ""))
        if len(metin) < 200:
            print(f"  ! {kayit['id']} çok kısa ya da boş geldi, atlanmadı ama kontrol et")
        maskelenen += n
        ad = dosya_yaz(sira, kayit, metin, liste.get("erisim_tarihi", str(date.today())))
        print(f"  {ad}  ({len(metin)} karakter)")
    print(f"Bitti: {len(liste['kararlar'])} karar · {sayac[0]} yeni istek · {maskelenen} kişisel veri kalıbı kapatıldı")


if __name__ == "__main__":
    calistir("--onbellek" in sys.argv)
