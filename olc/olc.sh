#!/usr/bin/env bash
# Ölçüm: NAİF yol (Opus ajanı, araçlı, kararları kendisi okur) vs KADEME (betik -> Haiku -> Opus 3 karar -> denetçi).
# Kullanım: ./olc/olc.sh [N=2] [NAIF_SAYI=10]
# NAIF_SAYI: naif ajana verilen karar sayısı. Kararlar uzun (~16 bin karakter); 40'ın hepsi naif yolda
# koşu başına birkaç dolar tutar. Kademe her zaman 40 kararın hepsini tarar.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
N="${1:-2}"
NAIF_SAYI="${2:-10}"
SONUC=olc/sonuclar
mkdir -p "$SONUC"
AYAR='{"disableAllHooks":true}'
unset CLAUDE_CODE_PLUGIN_DIRS

for i in $(seq 1 "$N"); do
  echo "== NAİF $i/$N: Opus ajanına davamiz.md + ilk $NAIF_SAYI karar + tuzak (Read/Glob/Grep araçlı)"
  # Ajan cevap anahtarını göremesin diye kararlar geçici bir klasöre kopyalanır.
  GECICI=$(mktemp -d)
  mkdir "$GECICI/kararlar"
  cp veri/davamiz.md "$GECICI/"
  ls veri/kararlar/*.md | sort | head -n $((NAIF_SAYI + 1)) | xargs -I{} cp {} "$GECICI/kararlar/"
  ls "$GECICI/kararlar" > "$SONUC/naif-$i.dosyalar.txt"
  BAS=$(date +%s)
  ( cd "$GECICI" && claude -p "$(cat "$REPO/olc/naif-prompt.txt")" --model opus \
      --tools Read,Glob,Grep --allowedTools Read Glob Grep \
      --output-format json --setting-sources project --settings "$AYAR" \
      --strict-mcp-config --no-session-persistence --max-budget-usd 1.5 ) \
      > "$SONUC/naif-$i.ham.json" || true
  SON=$(date +%s)
  rm -rf "$GECICI"
  python3 olc/kaydet.py naif "$i" "$SONUC/naif-$i.ham.json" $((SON - BAS))

  echo "== KADEME $i/$N: ./calistir.sh (40 karar + tuzak)"
  BAS=$(date +%s)
  ./calistir.sh > "$SONUC/kademe-$i.log"
  SON=$(date +%s)
  python3 olc/kaydet.py kademe "$i" cikti/maliyet.json $((SON - BAS))
done
python3 olc/tablo.py
echo "Tablo: olc/SONUC.md"
