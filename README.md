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

## Render'ga deploy
1. render.com → New → Blueprint (yoki Web Service) → shu GitHub repo'ni tanla.
2. Environment'ga ikkita o'zgaruvchi qo'sh (GitHub'ga yozma!):
   - `KINORA_ADMIN_USER` = bosh admin logini
   - `KINORA_ADMIN_PASS` = kuchli parol (kamida 8 belgi)
3. Deploy. Birinchi ishga tushganda bosh admin avtomatik yaratiladi.
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1`

## Baza: SQLite yoki PostgreSQL
- `DATABASE_URL` berilmasa — SQLite (`kinora.db`), lokal sinov uchun.
- `DATABASE_URL` berilsa — PostgreSQL (Render). Render'da Postgres yarating va uning
  **Internal Database URL** ini web servisning Environment'iga `DATABASE_URL` nomi bilan qo'shing.
- Jadvallar va yangi ustunlar ishga tushganda o'zi yaratiladi/yangilanadi.

**Diqqat:** Render'ning bepul web servisida fayl tizimi doimiy emas (SQLite o'chib ketadi),
shuning uchun Render'da PostgreSQL ishlating. Bepul Postgres 30 kundan keyin tugaydi (14 kun
imtiyozli muddat bor) — keyin pulli rejaga o'tish yoki yangi baza kerak.

## Kino ma'lumotlari va video
Admin panelda: nomi, yil, davomiyligi, davlat, janr, rejissyor, aktyorlar, yosh chegarasi,
tavsif, poster va video havola. `.mp4` / `.webm` havola bo'lsa o'z pleyerida, boshqa
`https://` embed havola bo'lsa iframe'da o'ynaydi. Faqat qonuniy kontent qo'shing.
