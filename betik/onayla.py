"""Basamak 4 · İnsan onayı: karar-ozeti.md'yi avukat okuyup onaylar. Model yok, otomatik onay yok.

Kullanım: python3 betik/onayla.py      (terminalde, soruları tek tek cevaplarsın)
"""
import os
import re
import sys
from datetime import datetime

from ortak import CIKTI

YOL = os.path.join(CIKTI, "karar-ozeti.md")
SORULAR = re.compile(r"^- \[ \] (.+)$", re.M)


def sor(soru):
    try:
        return input(f"{soru}? [e/h] ").strip().lower() in ("e", "evet")
    except EOFError:
        return False


def onayla():
    if not sys.stdin.isatty():
        raise SystemExit("Onay sadece terminalde, bir insan tarafından verilir (betik ya da ajan onaylayamaz).")
    if not os.path.exists(YOL):
        raise SystemExit("cikti/karar-ozeti.md yok. Önce ./calistir.sh")
    with open(YOL, encoding="utf-8") as f:
        metin = f.read()
    if "DURUM: ONAY BEKLİYOR" not in metin:
        raise SystemExit("Bu özet zaten onaylanmış ya da biçimi değişmiş.")
    if "✗" in metin and not sor("Özette ✗ ile işaretli sorunlu atıf var. Onları düzelttin ya da çıkardın mı"):
        raise SystemExit("Onay verilmedi: önce ✗ işaretli atıfları düzelt.")
    for soru in SORULAR.findall(metin):
        if not sor(soru):
            raise SystemExit(f"Onay verilmedi: \"{soru}\" adımı eksik.")
    ad = input("Onaylayan (ad soyad): ").strip() or "imzasız"
    metin = SORULAR.sub(r"- [x] \1", metin).replace(
        "DURUM: ONAY BEKLİYOR", f"DURUM: ONAYLANDI · {ad} · {datetime.now():%d.%m.%Y %H:%M}")
    with open(YOL, "w", encoding="utf-8") as f:
        f.write(metin)
    print("Onaylandı. Not: onay, bu taslağı okuduğunu gösterir; hukuki sorumluluk avukattadır.")


if __name__ == "__main__":
    onayla()
