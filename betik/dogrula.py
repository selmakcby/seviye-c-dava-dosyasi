"""Küçük bir JSON Schema doğrulayıcı (standart kütüphane, ek paket yok).

Desteklenen anahtarlar: type, properties, required, additionalProperties,
items, minItems, maxItems, enum, minLength, maxLength, minimum, maximum. Bu repodaki şemalar için yeterli.
"""
import json
import os

TIPLER = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "number": (int, float)}


def sema_yukle(ad):
    yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sema", ad)
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def hatalar(veri, sema, yol="$"):
    """Şemaya uymayan her yer için bir hata cümlesi döndürür. Boş liste = geçerli."""
    tip = sema.get("type")
    if tip and not isinstance(veri, TIPLER[tip]):
        return [f"{yol}: {tip} bekleniyordu"]
    sonuc = []
    if "enum" in sema and veri not in sema["enum"]:
        sonuc.append(f"{yol}: '{veri}' izin verilen değerlerden değil")
    if isinstance(veri, str):
        if len(veri) < sema.get("minLength", 0):
            sonuc.append(f"{yol}: çok kısa")
        if len(veri) > sema.get("maxLength", 10**9):
            sonuc.append(f"{yol}: çok uzun")
    if isinstance(veri, (int, float)) and not isinstance(veri, bool):
        if veri < sema.get("minimum", -10**12) or veri > sema.get("maximum", 10**12):
            sonuc.append(f"{yol}: aralık dışında")
    if isinstance(veri, list):
        if len(veri) > sema.get("maxItems", 10**9):
            sonuc.append(f"{yol}: en fazla {sema['maxItems']} öğe")
        if len(veri) < sema.get("minItems", 0):
            sonuc.append(f"{yol}: en az {sema['minItems']} öğe gerekli")
        for i, oge in enumerate(veri):
            sonuc += hatalar(oge, sema.get("items", {}), f"{yol}[{i}]")
    if isinstance(veri, dict):
        ozellikler = sema.get("properties", {})
        sonuc += [f"{yol}.{k}: eksik" for k in sema.get("required", []) if k not in veri]
        if sema.get("additionalProperties") is False:
            sonuc += [f"{yol}.{k}: beklenmeyen alan" for k in veri if k not in ozellikler]
        for k, alt in ozellikler.items():
            if k in veri:
                sonuc += hatalar(veri[k], alt, f"{yol}.{k}")
    return sonuc
