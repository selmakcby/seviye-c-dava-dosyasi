"""Katmanlı hat: 0 betik dizin -> 1 Haiku eleme -> 2 Opus okuma (cascade) -> 3 denetçi -> 4 insan onayı

Kullanım: python3 betik/hat.py [karar-klasoru]   ->  cikti/karar-ozeti.md (ONAY BEKLİYOR)
"""
import os
import sys
import time

from denetle import denetle
from dizin import dizin_cikar
from ele import ele
from oku import oku, oku_bir_kez
from ortak import CIKTI, KARARLAR, json_yaz, oku_metin
from puanla import puanla
from rapor import rapor_yaz


def sorun_notu(denetim):
    """Denetçinin bulduklarını Opus'a ikinci okumada verilecek nota çevirir."""
    satirlar = [f"- {a['id']}: \"{a['alinti'][:120]}\" -> {a['etiket']}" for a in denetim["alintilar"] if a["sorunlu"]]
    satirlar += [f"- {n['id']}: karar no {n['iddia']} -> {n['etiket']}" for n in denetim["karar_nolari"]
                 if n["durum"] in ("uydurma", "karar_yok")]
    return ("DENETÇİ ÖNCEKİ ÖZETTE ŞU SORUNLARI BULDU. Alıntıları metinden birebir kopyala, "
            "karar numarasını metinde yazdığı gibi yaz:\n" + "\n".join(satirlar))


def okuma_ve_denetim(secilen, dava, dizin):
    """Opus okur, denetçi kontrol eder; sorun varsa Opus bir kez effort high ile tekrar okur."""
    print(f"[2] Opus {len(secilen)} kararı tam okuyor (effort low; gerekirse high)...")
    ozet, maliyetler = oku(secilen, dava)
    print(f"    bitti: güven {ozet['guven']} · {sum(m['usd'] for m in maliyetler):.4f} USD")
    print("[3] Denetçi her alıntıyı ve karar numarasını kaynak metne karşı kontrol ediyor...")
    denetim = denetle(ozet, dizin)
    maliyetler.append(denetim["maliyet"])
    yuksek_denendi = any(m.get("effort") == "high" for m in maliyetler)
    if denetim["sorunlu_sayisi"] and not yuksek_denendi:
        print(f"    ! {denetim['sorunlu_sayisi']} sorunlu atıf. Opus effort high ile bir kez daha okuyor...")
        ilk = [l.strip() for l in sorun_notu(denetim).splitlines()[1:]]
        ozet2, _, m2 = oku_bir_kez(secilen, dava, "high", sorun_notu(denetim))
        maliyetler.append(m2)
        if ozet2:
            ozet, denetim = ozet2, denetle(ozet2, dizin)
            maliyetler.append(denetim["maliyet"])
        denetim["ilk_okuma_sorunlari"] = ilk
    alinti = denetim["alintilar"]
    print(f"    {len(alinti)} alıntı · {sum(not a['sorunlu'] for a in alinti)} doğrulandı · "
          f"{denetim['sorunlu_sayisi']} sorunlu · karar no gerçek: "
          f"{sum(n['durum'] == 'gercek' for n in denetim['karar_nolari'])}/{len(denetim['karar_nolari'])}")
    return ozet, denetim, maliyetler


def calistir(klasor):
    bas = time.time()
    dava = oku_metin("veri/davamiz.md")
    dizin, _ = dizin_cikar(klasor)
    print(f"[0] {len(dizin)} belge dizinlendi (betik, 0 token) · şüpheli: {sum(s['supheli'] for s in dizin)}")
    print("[1] Haiku dizini okuyup eliyor (tek toplu çağrı, tam metin değil)...")
    eleme, secilen, m1 = ele(dizin, dava)
    print(f"    ilgili {sum(k['ilgili'] for k in eleme.values())} · şüpheli {sum(k['supheli'] for k in eleme.values())}"
          f" · {m1['usd']:.4f} USD, {m1['sure_sn']} sn")
    if not secilen:
        raise SystemExit("Okunacak ilgili karar bulunamadı. cikti/eleme.json dosyasına bak.")
    ozet, denetim, maliyetler = okuma_ve_denetim(secilen, dava, dizin)
    maliyetler = [m1] + maliyetler
    toplam = sum(m["usd"] for m in maliyetler)
    kayit = {"basamaklar": maliyetler, "toplam_usd": toplam, "sure_sn": round(time.time() - bas, 1),
             "belge": len(dizin), "secilen": secilen, "sorunlu_atif": denetim["sorunlu_sayisi"]}
    if os.path.abspath(klasor) == KARARLAR:
        p = puanla({i: k["ilgili"] for i, k in eleme.items()}, {i for i, k in eleme.items() if k["supheli"]}, secilen)
        kayit["dogruluk"] = {k: v for k, v in p.items() if k != "yanlislar"}
    for ad, veri in (("eleme.json", {"eleme": eleme, "secilen": secilen}), ("ozet.json", {"ozet": ozet}),
                     ("denetim.json", denetim), ("maliyet.json", kayit)):
        json_yaz(os.path.join(CIKTI, ad), veri)
    baslik = dava.splitlines()[0].lstrip("# ").strip()
    rapor_yaz(os.path.join(CIKTI, "karar-ozeti.md"), baslik, dizin, eleme, secilen, ozet, denetim, maliyetler)
    print(f"[4] İnsan onayı bekleniyor: cikti/karar-ozeti.md · toplam {toplam:.4f} USD · {kayit['sure_sn']} sn")
    if "dogruluk" in kayit:
        d = kayit["dogruluk"]
        print(f"Örnek klasörde eleme doğruluğu: {d['dogru']}/{d['toplam']} · tuzak yakalanan: "
              f"{d['tuzak_yakalanan']}/{d['tuzak_toplam']} · seçilenlerden davamızın alt konusunda: "
              f"{d['secilen_isabet']}/{d['secilen_toplam']}")


if __name__ == "__main__":
    calistir(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else KARARLAR)
