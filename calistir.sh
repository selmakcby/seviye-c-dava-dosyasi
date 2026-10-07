#!/usr/bin/env bash
# Tek komut: ./calistir.sh                    (veri/kararlar: 40 gerçek karar + 1 sahte tuzak)
#            ./calistir.sh ~/kararlarim       (kendi .md karar klasörün)
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Python 3 bulunamadı. README > Gereksinimler"; exit 1; }
command -v claude  >/dev/null || { echo "Claude Code (claude) bulunamadı. README > Gereksinimler"; exit 1; }
python3 betik/hat.py "${1:-veri/kararlar}"
