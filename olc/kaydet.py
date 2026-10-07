"""Bir ölçüm koşusunu olc/sonuclar/<yol>-<n>.json olarak özetler (maliyet, süre, doğruluk, alıntı)."""
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "betik"))
from denetle import betik_kontrolu  # noqa: E402
from dizin import dizin_cikar  # noqa: E402
from ortak import json_ayikla  # noqa: E402
from puanla import puanla  # noqa: E402


def son_json(metin):
    """Metindeki son {"ilgili": ...} bloğunu bulur."""
    yer = metin.rfind('"ilgili"')
    bas = metin.rfind("{", 0, yer) if yer != -1 else -1
    try:
        return json.JSONDecoder().raw_decode(metin[bas:])[0] if bas != -1 else {}
    except json.JSONDecodeError:
        return json_ayikla(metin) or {}


def alinti_say(alintilar):
    """Alıntıları aynı betik kontrolünden geçirir (0 token). Döner: (birebir_var, toplam)."""
    ozet = {"kararlar": [{"id": a.get("dosya", ""), "karar_no": a.get("karar_no", ""),
                          "ilkeler": [{"ilke": "", "alinti": a.get("alinti", "")}]} for a in alintilar]}
    kayitlar, _ = betik_kontrolu(ozet, dizin_cikar()[0])
    return sum(k["durum"] == "metinde_var" for k in kayitlar), len(kayitlar)


def naif(ham_yol, n):
    with open(ham_yol, encoding="utf-8") as f:
        d = json.load(f)
    v = son_json(d.get("result", ""))
    with open(ham_yol.replace(".ham.json", ".dosyalar.txt"), encoding="utf-8") as f:
        dosyalar = set(f.read().split())
    p = puanla({i: bool(x) for i, x in (v.get("ilgili") or {}).items()}, set(v.get("supheli") or []),
               v.get("secilen") or [], sadece=dosyalar)
    var, toplam = alinti_say(v.get("alintilar") or [])
    return {"usd": d.get("total_cost_usd", 0.0), "tur": d.get("num_turns"), "hata": d.get("is_error", False),
            "modeller": {m: round(u.get("costUSD", 0), 4) for m, u in d.get("modelUsage", {}).items()},
            "belge": len(dosyalar), "p": p, "alinti_dogru": var, "alinti_toplam": toplam}


def kademe(maliyet_yol, n):
    with open(maliyet_yol, encoding="utf-8") as f:
        m = json.load(f)
    with open(os.path.join(KOK, "cikti", "denetim.json"), encoding="utf-8") as f:
        a = json.load(f)["alintilar"]
    modeller = {}
    for b in m["basamaklar"]:
        modeller[b.get("model", "-")] = round(modeller.get(b.get("model", "-"), 0) + b["usd"], 4)
    return {"usd": m["toplam_usd"], "tur": sum(b["cagri"] for b in m["basamaklar"]), "hata": False,
            "modeller": modeller, "belge": m["belge"], "p": m["dogruluk"],
            "alinti_dogru": sum(k["durum"] == "metinde_var" for k in a), "alinti_toplam": len(a),
            "effort": [b["effort"] for b in m["basamaklar"] if "effort" in b]}


if __name__ == "__main__":
    yol, n, kaynak, sure = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
    k = naif(kaynak, n) if yol == "naif" else kademe(kaynak, n)
    p = k.pop("p")
    k.update({"yol": yol, "kos": n, "sure_sn": sure, "dogru": p["dogru"], "toplam": p["toplam"],
              "tuzak": f"{p['tuzak_yakalanan']}/{p['tuzak_toplam']}",
              "secilen_isabet": f"{p['secilen_isabet']}/{p['secilen_toplam']}"})
    with open(os.path.join(KOK, "olc", "sonuclar", f"{yol}-{n}.json"), "w", encoding="utf-8") as f:
        json.dump(k, f, ensure_ascii=False, indent=2)
    print(f"   {yol} {n}: {k['usd']:.4f} USD · {sure} sn · eleme {k['dogru']}/{k['toplam']} · tuzak {k['tuzak']}"
          f" · alıntı birebir {k['alinti_dogru']}/{k['alinti_toplam']}")
