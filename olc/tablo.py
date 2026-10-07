"""olc/sonuclar/*.json -> olc/SONUC.md tablosu (ortalama + her koşu)."""
import glob
import json
import os
from datetime import datetime

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADLAR = {"naif": "NAİF: Opus ajanı kararları kendisi okur", "kademe": "KADEME: betik + Haiku + Opus (3) + denetçi"}


def virgul(x, b=4):
    return f"{x:.{b}f}".replace(".", ",")


def oku():
    kayitlar = []
    for yol in sorted(glob.glob(os.path.join(KOK, "olc", "sonuclar", "*.json"))):
        if not yol.endswith(".ham.json"):
            with open(yol, encoding="utf-8") as f:
                kayitlar.append(json.load(f))
    return kayitlar


def satir(k):
    dag = ", ".join(f"{m} {virgul(u)}" for m, u in k["modeller"].items())
    return (f"| {ADLAR[k['yol']]} | {k['kos']} | {k['belge']} | {virgul(k['usd'])} | {k['sure_sn']} "
            f"| {k['dogru']}/{k['toplam']} | {k['tuzak']} | {k['alinti_dogru']}/{k['alinti_toplam']} | {dag} |")


def tablo(kayitlar):
    satirlar = ["| Yol | Koşu | Taranan belge | USD | Süre (sn) | Eleme doğruluğu | Tuzak | Alıntı birebir | Model dağılımı |",
                "|---|---|---|---|---|---|---|---|---|"]
    ozet = {}
    for yol in ("naif", "kademe"):
        grup = sorted((k for k in kayitlar if k["yol"] == yol), key=lambda k: k["kos"])
        if not grup:
            continue
        satirlar += [satir(k) for k in grup]
        ozet[yol] = {a: sum(k[a] for k in grup) / len(grup) for a in ("usd", "sure_sn")}
        satirlar.append(f"| **{ADLAR[yol]}** | **ortalama** | | **{virgul(ozet[yol]['usd'])}** "
                        f"| **{ozet[yol]['sure_sn']:.0f}** | | | | |")
    return satirlar, ozet


if __name__ == "__main__":
    satirlar, ozet = tablo(oku())
    metin = [f"# Ölçüm sonucu · {datetime.now():%d.%m.%Y}", "",
             "Maliyet: `claude -p --output-format json` çıktısındaki `total_cost_usd`. Süre: duvar saati. "
             "Eleme doğruluğu: `veri/cevap-anahtari.json` (naif yolda sadece ona verilen belgeler üzerinden). "
             "Alıntı birebir: modelin \"kelimesi kelimesine\" dediği alıntının kaynak metinde gerçekten geçip geçmediği "
             "(iki yol için de aynı betik kontrolü, 0 token).", ""] + satirlar
    if "naif" in ozet and "kademe" in ozet and ozet["kademe"]["usd"] > 0:
        oran = ozet["naif"]["usd"] / ozet["kademe"]["usd"]
        metin += ["", f"**Ortalama maliyet oranı: naif yol kademenin {virgul(oran, 1)} katı.**"]
    notlar = os.path.join(KOK, "olc", "notlar.md")
    if os.path.exists(notlar):
        with open(notlar, encoding="utf-8") as f:
            metin += ["", f.read().strip()]
    with open(os.path.join(KOK, "olc", "SONUC.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(metin) + "\n")
    print("\n".join(metin))
