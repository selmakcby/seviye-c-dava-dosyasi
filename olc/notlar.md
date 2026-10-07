## Notlar: bizim ölçümümüz (8 Ekim 2026, dürüst okuma)

- **Naif yol sadece 10 karar okudu, kademe 40'ın hepsini taradı.** Kararlar ortalama ~16 bin karakter. 10 kararlık naif koşu bile
  ~0,97 USD tuttu (15 tur, ~90 bin token önbelleğe yazma + ~72 bin token önbellekten okuma, ~11-12 bin token çıktı). 40 kararın
  hepsini naif yola vermek koşu başına kabaca 3-4 USD demek; bütçe için ölçmedik, tahmindir. Yani tablo naif yolu **lehine** kayırıyor:
  dörtte bir iş için yine ~2 kat pahalı.
- **Doğruluk iki yolda da tam.** Naif Opus 11/11 eleme yaptı, tuzağı yakaladı ve verdiği 9 ve 11 alıntının hepsi metinde birebir
  vardı. Bu örnekte Opus atıf uydurmadı. Kademenin farkı doğrulukta değil: **(1)** 40 belgeyi tarayıp sadece 3'ünü pahalı modele
  vermesi, **(2)** alıntıyı modele güvenerek değil betikle kontrol etmesi. Naif yolda "alıntılar doğru mu?" sorusunun cevabını
  ancak biz ayrıca kontrol ettiğimiz için biliyoruz.
- **Cascade gerçekten tetiklendi.** Kademe 2. koşuda Opus effort low ile okudu (0,08 USD, önbellek sıcak), denetçi 1 sorunlu atıf
  buldu, Opus effort high ile bir kez daha okudu ve ikinci özette 8/8 alıntı temiz çıktı. Bu yüzden o koşu 0,62 USD ve 229 sn sürdü
  (1. koşu 0,40 USD, 92 sn). İlk okumadaki sorunun ne olduğu bu koşuda kaydedilmedi; o koşudan sonra `betik/hat.py` ilk okumanın
  sorunlarını `cikti/karar-ozeti.md` > "Denetçi özeti" bölümüne yazacak şekilde güncellendi.
- **Denetçinin kendisi de test edildi:** `olc/uydurma-atif-testi/` gerçek bir Opus özetine 4 kasıtlı hata ekler (uydurma alıntı,
  anlamı ters çevrilmiş alıntı, değiştirilmiş karar no, var olmayan karar). Sonuç 4/4, yanlış alarm yok.
- **Haiku'da düşünme kapalı** (`alwaysThinkingEnabled: false`, seviye A'daki ayar). Eleme soğukta ~0,07 USD, önbellek sıcakken ~0,025 USD.
- **Opus'un okuduğu karar sayısı 3** (`betik/ele.py` > `SECIM_SAYISI`). 4 karar okutunca effort low 0,40 USD tuttu; 3 kararla ~0,31.
- **Ortam:** Claude Code 2.1.287, Ekim 2026 fiyatları. Naif koşu `--setting-sources project` ile koştu (kişisel CLAUDE.md yüklü kaldı,
  gerçek kullanımdaki gibi); kademenin çağrıları kişisel CLAUDE.md'yi dışarıda bırakır. Senin sayıların farklı çıkabilir: `./olc/olc.sh`.
