# Uydurma atıf testi

Gerçek Opus özetine 4 kasıtlı hata eklendi. Denetçi **4/4** yakaladı.
Özetteki gerçek alıntılardan 9 tanesi temiz geçti (yanlış alarm yok mu, aşağıda).

| Eklenen hata | Yakalandı mı | Denetçinin etiketi |
|---|---|---|
| 1 · uydurma alıntı | evet | UYDURMA ALINTI |
| 2 · çarpıtılmış alıntı | evet | ÇARPITILMIŞ ALINTI |
| 3 · uydurma karar no | evet | UYDURMA KARAR NO |
| 4 · var olmayan karar | evet | KARAR KLASÖRDE YOK |

3 numaralı hatada gerçek numara 2025/912 (Esas 2020/1455) idi, 2019/8812 yazıldı.

## Bütün alıntılar

| # | Karar | Benzerlik | Etiket | Not |
|---|---|---|---|---|
| 1 | 06-emsal-2026-970.md | %100 | DOĞRULANDI | Alıntı kaynakla birebir aynı; devreden işverenin sorumluluğunun çalıştırma süresi ve devir anındaki ücretle sınırlı olduğunu mahkeme belirtiyor. |
| 2 | 06-emsal-2026-970.md | %100 | DOĞRULANDI | Alıntı birebir aynı; yıllık izin alacağı ve fer'ilerinden son alt işverenin sorumlu olduğu mahkeme gerekçesinde belirtilmiş. |
| 3 | 06-emsal-2026-970.md | %43 | UYDURMA ALINTI | Alıntı kaynak kararın metninde yok. |
| 4 | 30-emsal-2025-1404.md | %95 | ÇARPITILMIŞ ALINTI | Kaynakta 'çalıştırdığı dönemle sınırlı olarak sorumluluğu' yazıyor; alıntı 'sınırlı olmaksızın tamamından' diyerek anlamı tersine çeviriyor. İlke de kaynağa aykırı. |
| 5 | 30-emsal-2025-1404.md | %100 | DOĞRULANDI | Alıntı aynı; tamamının hakedişten kesilmesi usul ve yasaya aykırı bulunuyor. İade kısmı sonraki bölümle uyumlu, kaynak ilkeyi büyük ölçüde karşılıyor. |
| 6 | 30-emsal-2025-1404.md | %100 | DOĞRULANDI | Alıntı aynı; hesaplanan miktar dışındaki kıdem tazminatı için rücu hakkı yok, fazla kesintiler iade edilmeli. |
| 7 | 02-emsal-2025-912.md | %100 | DOĞRULANDI | Alıntı aynı; sözleşmede işveren sorumluluğu hükmü yokluğu ve ücretin sözleşme bedeline dahilliği halinde işveren ödediğini yüklenicilerden isteyebilir. |
| 8 | 02-emsal-2025-912.md | %100 | DOĞRULANDI (kısmen destekliyor) | Alıntı aynı; dönemle orantılı sorumluluk destekleniyor. Ancak ilke 'her yüklenici' diyor, kaynak işverene karşı sorumluluğu ve giydirilmiş ücret hesabını da içeriyor. |
| 9 | 02-emsal-2025-912.md | %100 | DOĞRULANDI (kısmen destekliyor) | Alıntı aynı; yıllık izinde son yüklenici sorumlu. İhbar tazminatında kaynak 'son işveren' diyor; ilke 'son yüklenici' yazıyor, küçük terim farkı var. |
| 10 | 04-emsal-2025-330.md | %100 | DOĞRULANDI (kısmen destekliyor) | Alıntı aynı; dönemle sınırlı tam rücu destekleniyor. 'Yarı yarıya paylaşım uygulanmamıştır' kısmı alıntıda yok, kaynaktan doğrulanamıyor. |
| 11 | 04-emsal-2025-330.md | %100 | DOĞRULANDI | Alıntı aynı; ihtarla temerrüt iddia edilmediği ve ihtarname sunulmadığı için faiz dava tarihinden işletilmeli, ödeme tarihinden değil. |
| 12 | 41-emsal-2021-4471.md | %0 | UYDURMA ALINTI | Alıntı kaynak kararın metninde yok. |

Denetçi maliyeti: 0.0284 USD (claude-sonnet-5-5)
