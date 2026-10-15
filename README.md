# KINORA Cloud

Qonuniy kino va serial streaming platformasi (o'quv loyiha). Flask + SQLite.

## Imkoniyatlar
- Bosh sahifa, Kinolar, Seriallar, Batafsil, Qidiruv
- Login / Ro'yxatdan o'tish, Mening ro'yxatim, Davom ettirish
- 4 til (UZ / RU / EN / TR), dark/light tema, mobil menyu
- Admin panel: kontent qo'shish / tahrirlash / o'chirish
- Rollar:
  - **Bosh admin** — hamma narsa + yordamchi admin qo'shish/o'chirish + huquq berish
  - **Yordamchi admin** — faqat bosh admin bergan huquqlar (qo'shish, tahrirlash, o'chirish)

## Ishga tushirish (Pydroid 3 yoki kompyuter)
1. `pip install flask`
2. `python create_main_admin.py` — bosh admin login va parolini kiritasan (bir marta)
3. `python app.py`
4. Brauzerda `http://127.0.0.1:5000` → `/login`

## Xavfsizlik
- Parollar hash qilinadi (werkzeug), kodda yoki GitHub'da saqlanmaydi
- CSRF himoya, login urinishlari cheklangan
- `kinora.db` va `secret.key` `.gitignore` da — GitHub'ga chiqmaydi

## Eslatma
Faqat qonuniy, litsenziyasi bor kontent qo'shing.
