"""cikti/karar-ozeti.md biçimi: avukatın okuyup onaylayacağı taslak."""
from datetime import datetime

UYARI = ("> **HUKUKİ TAVSİYE DEĞİLDİR.** Bu dosya bir yapay zeka hattının ürettiği **taslaktır**; "
         "bir avukat okuyup onaylamadan hiçbir yerde kullanılamaz.\n"
         "> Zamanaşımı ve hak düşürücü süre hesabı bu hatta **yapılmaz**: süreyi avukat hesaplar.")
ROZET = {False: "✓", True: "✗"}


def virgul(x, b=4):
    return f"{x:.{b}f}".replace(".", ",")


def _kunye(k, satir):
    url = satir.get("kaynak_url") or "-"
    return (f"### {k['daire']} · {k['karar_no']} · {k['tarih']}\n"
            f"Dosya: `veri/kararlar/{k['id']}` · Kaynak: {url}")


def karar_bolumu(ozet, denetim, dizin):
    satirlar = {s["id"]: s for s in dizin}
    alintilar = {}
    for a in denetim["alintilar"]:
        alintilar.setdefault(a["id"], []).append(a)
    numara = {n["id"]: n for n in denetim["karar_nolari"]}
    parca = ["## 2 · Okunan kararlar (Opus) ve denetçinin notu", ""]
    for k in ozet["kararlar"]:
        n = numara.get(k["id"], {})
        parca += [_kunye(k, satirlar.get(k["id"], {})),
                  f"Karar no denetimi: **{n.get('etiket', '-')}** ({n.get('aciklama', '')})", "", k["ozet"], ""]
        for ilke, a in zip(k["ilkeler"], alintilar.get(k["id"], [])):
            parca += [f"- **{ilke['ilke']}** ({ilke['etki']})",
                      f"  > \"{ilke['alinti']}\"",
                      f"  {ROZET[a['sorunlu']]} Denetçi: **{a['etiket']}** · {a['aciklama']}", ""]
    return parca


def ilke_bolumu(ozet):
    parca = ["## 3 · Davamıza uygulanabilecek ilkeler (taslak)", ""]
    for i, ilke in enumerate(ozet["uygulanabilir_ilkeler"], 1):
        parca.append(f"{i}. {ilke['ilke']} _(dayanak: {', '.join(ilke['dayanak'])})_")
    parca += ["", f"Modelin kendi güveni: **{ozet['guven']}**", "", "**Dosyada eksik bilgiler:**"]
    parca += [f"- {e}" for e in ozet["eksik_bilgi"]] or ["- (yok)"]
    return parca + [""]


def tarama_bolumu(dizin, eleme, secilen):
    ilgili = [i for i, k in eleme.items() if k["ilgili"] and not k["supheli"]]
    supheli = [i for i, k in eleme.items() if k["supheli"]]
    parca = ["## 1 · Tarama", "",
             f"- Klasörde **{len(dizin)}** belge vardı, hepsi dizinlendi (betik, 0 token).",
             f"- Haiku dizini okudu: **{len(ilgili)}** belge davamızla ilgili, **{len(supheli)}** belge şüpheli, "
             f"kalanı ilgisiz.",
             f"- Opus yalnız en benzer **{len(secilen)}** kararı tam okudu: {', '.join(secilen)}", ""]
    if supheli:
        parca += ["### Şüpheli belgeler (okunmadı, insana bırakıldı)", ""]
        parca += [f"- `{i}`: {eleme[i]['gerekce']}" for i in supheli] + [""]
    return parca


def ek_bolum(dizin, eleme, secilen):
    satir = {s["id"]: s for s in dizin}
    okunmayan = [i for i, k in eleme.items() if k["ilgili"] and not k["supheli"] and i not in secilen]
    ilgisiz = [i for i, k in eleme.items() if not k["ilgili"] and not k["supheli"]]
    parca = ["## 5 · Okunmayan ama ilgili kararlar (gerekirse avukat açar)", ""]
    parca += [f"- `{i}` · {satir[i]['karar_no']} · benzerlik {eleme[i]['benzerlik']}/5 · {eleme[i]['gerekce']}"
              for i in sorted(okunmayan, key=lambda i: -eleme[i]["benzerlik"])]
    parca += ["", "## 6 · İlgisiz bulunanlar", ""]
    parca += [f"- `{i}` · {eleme[i]['konu']} · {eleme[i]['gerekce']}" for i in ilgisiz]
    return parca + [""]


def maliyet_bolumu(maliyetler):
    parca = ["## 7 · Bu koşunun maliyeti", "", "| Basamak | Model | USD | Süre (sn) |", "|---|---|---|---|",
             "| 0 · Betik dizin | - | 0 | <1 |"]
    parca += [f"| {m['basamak']} | {m.get('model', '-')} | {virgul(m['usd'])} | {virgul(m['sure_sn'], 1)} |" for m in maliyetler]
    toplam = sum(m["usd"] for m in maliyetler)
    return parca + [f"| **Toplam** | | **{virgul(toplam)}** | |", ""]


def onay_bolumu():
    return ["## 8 · İnsan onayı", "", "**DURUM: ONAY BEKLİYOR**", "",
            "- [ ] Her alıntıyı kaynak kararda kendim gördüm (✗ işaretliler dahil)",
            "- [ ] Karar numaralarını UYAP / resmi kaynakta kontrol ettim",
            "- [ ] Süre (zamanaşımı, hak düşürücü süre) hesabını kendim yaptım",
            "- [ ] Şüpheli belgeleri ayrıca inceledim", "",
            "Onaylamak için: `python3 betik/onayla.py`"]


def rapor_yaz(yol, baslik, dizin, eleme, secilen, ozet, denetim, maliyetler):
    sorunlu = denetim["sorunlu_sayisi"]
    parca = [f"# Karar özeti · {baslik}", "", UYARI, "",
             f"Oluşturma: {datetime.now():%d.%m.%Y %H:%M} · Denetçi: "
             + ("**sorun bulunmadı**" if sorunlu == 0 else f"**{sorunlu} sorunlu atıf**, aşağıda ✗ ile işaretli"), ""]
    parca += tarama_bolumu(dizin, eleme, secilen) + karar_bolumu(ozet, denetim, dizin) + ilke_bolumu(ozet)
    parca += ["## 4 · Denetçi özeti", ""]
    if denetim.get("ilk_okuma_sorunlari"):
        parca += ["İlk okumada (effort low) denetçi şu sorunları buldu; Opus effort high ile yeniden okudu, "
                  "aşağıdaki sonuçlar ikinci okumaya aittir:", ""] + denetim["ilk_okuma_sorunlari"] + [""]
    parca += [
              f"- Alıntı: {len(denetim['alintilar'])} · sorunlu: {sum(a['sorunlu'] for a in denetim['alintilar'])}",
              f"- Karar no: {len(denetim['karar_nolari'])} · gerçek: "
              f"{sum(n['durum'] == 'gercek' for n in denetim['karar_nolari'])}", ""]
    parca += ek_bolum(dizin, eleme, secilen) + maliyet_bolumu(maliyetler) + onay_bolumu()
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(parca) + "\n")
