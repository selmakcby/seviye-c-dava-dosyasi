"""Ortak parçalar: karar dosyası okuma, Claude'a yalın çağrı, JSON yazma.

Sadece Python standart kütüphanesi kullanılır; kurulacak paket yok.
"""
import json
import os
import re
import subprocess
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KARARLAR = os.path.join(KOK, "veri", "kararlar")
CIKTI = os.path.join(KOK, "cikti")

# Talimat enjeksiyonu kalıpları: belge içinde yapay zekaya hitap eden metin (0 token kural ağı)
ENJEKSIYON = re.compile(
    r"(talimat\w* (yok say|unut|görmezden)|önceki talimat|sistem talimat|sistem notu"
    r"|okuyan (yapay zeka|sistem|model|ajan)|yapay zeka (sistem|asistan)\w*\s*(için|:)"
    r"|diğer kararları (yok say|dikkate alma)|ignore (all |any )?(previous|prior) instructions)", re.I)


# ---------------------------------------------------------------- karar dosyaları
def karar_oku(yol):
    """Başında --- frontmatter olan .md karar dosyasını sözlüğe çevirir."""
    with open(yol, encoding="utf-8") as f:
        ham = f.read()
    on, metin = {}, ham
    eslesme = re.match(r"^---\n(.*?)\n---\n", ham, re.S)
    if eslesme:
        for satir in eslesme.group(1).splitlines():
            if ":" in satir:
                k, v = satir.split(":", 1)
                on[k.strip()] = v.strip()
        metin = ham[eslesme.end():]
    return {"id": os.path.basename(yol), "on": on, "metin": metin.strip()}


def klasor_oku(klasor=KARARLAR):
    """Klasördeki bütün .md kararlarını ada göre sıralı okur."""
    if not os.path.isdir(klasor):
        raise SystemExit(f"Klasör bulunamadı: {klasor}")
    adlar = sorted(a for a in os.listdir(klasor) if a.lower().endswith(".md"))
    if not adlar:
        raise SystemExit(f"Klasörde .md karar yok: {klasor}")
    return [karar_oku(os.path.join(klasor, a)) for a in adlar]


def veri_blogu(karar_id, icerik):
    """Belgeyi modele VERİ olarak verir: etiket içine sarılır, etiketi kıracak metin temizlenir."""
    temiz = re.sub(r"</?\s*karar[^>]*>", "[etiket silindi]", icerik, flags=re.I)
    return f'<karar id="{karar_id}">\n{temiz}\n</karar>'


# ---------------------------------------------------------------- Claude çağrısı
def _komut(model, sistem, sema, butce_usd, effort, dusunme):
    ayarlar = {"disableAllHooks": True, "alwaysThinkingEnabled": dusunme,
               "claudeMdExcludes": ["**/CLAUDE.md", "**/.claude/rules/**", "**/CLAUDE.local.md"]}
    komut = ["claude", "-p", "--model", model, "--system-prompt", sistem,
             "--tools", "", "--output-format", "json",
             "--setting-sources", "project", "--settings", json.dumps(ayarlar),
             "--strict-mcp-config", "--disable-slash-commands",
             "--no-session-persistence", "--max-budget-usd", str(butce_usd)]
    if sema:
        komut += ["--json-schema", json.dumps(sema)]
    if effort:
        komut += ["--effort", effort]
    return komut


def yalin_cagri(model, sistem, girdi, sema=None, butce_usd=0.5, effort=None, dusunme=False):
    """Araçsız, kısa system prompt'lu tek çağrı: `claude -p --model <model>`.

    - --tools ""                 : hiçbir araç yok (dosya okuyamaz, komut çalıştıramaz)
    - --system-prompt            : Claude Code'un uzun ajan prompt'u yerine bizimki
    - --json-schema              : cevap bu şemada gelir (yine de betikte ayrıca doğrularız)
    - --effort                   : Opus için düşünme bütçesi (low / high), cascade bunu değiştirir
    - alwaysThinkingEnabled=false: Haiku/Sonnet sınıflamada "düşünme" token'ı harcanmaz
    Dönüş: {"veri", "metin", "usd", "sure_sn", "model"}
    """
    ortam = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_PLUGIN_DIRS"}
    ortam["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    bas = time.time()
    try:
        sonuc = subprocess.run(_komut(model, sistem, sema, butce_usd, effort, dusunme), input=girdi,
                               capture_output=True, text=True, timeout=600, env=ortam, cwd=KOK)
    except FileNotFoundError:
        raise SystemExit("`claude` komutu bulunamadı. Claude Code kurulu mu? (README > Gereksinimler)")
    except subprocess.TimeoutExpired:
        return {"veri": None, "metin": "", "usd": 0.0, "sure_sn": round(time.time() - bas, 1), "model": model}
    sure = round(time.time() - bas, 1)
    try:
        d = json.loads(sonuc.stdout)
    except json.JSONDecodeError:
        print(f"  ! Claude çağrısı JSON dönmedi: {(sonuc.stderr or sonuc.stdout).strip()[:300]}")
        return {"veri": None, "metin": "", "usd": 0.0, "sure_sn": sure, "model": model}
    modeller = list(d.get("modelUsage", {}).keys())
    veri = d.get("structured_output") or json_ayikla(d.get("result", ""))
    return {"veri": veri, "metin": d.get("result", ""), "usd": float(d.get("total_cost_usd", 0.0)),
            "sure_sn": sure, "model": modeller[0] if modeller else model}


def json_ayikla(metin):
    """Model cevabındaki JSON nesnesini bulur (``` çitleri olsa da). Bulamazsa None."""
    if not metin:
        return None
    metin = re.sub(r"^```(?:json)?\s*|\s*```$", "", metin.strip())
    bas, son = metin.find("{"), metin.rfind("}")
    if bas == -1 or son <= bas:
        return None
    try:
        return json.loads(metin[bas:son + 1])
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- dosya yardımcıları
def oku_metin(goreli_yol):
    with open(os.path.join(KOK, goreli_yol), encoding="utf-8") as f:
        return f.read().strip()


def json_oku(yol):
    if not os.path.exists(yol):
        raise SystemExit(f"Dosya yok: {os.path.relpath(yol, KOK)} (önceki basamağı çalıştırdın mı?)")
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def json_yaz(yol, veri):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
