"""Bosh adminni yaratadi (bir marta ishlatiladi).
Login va parol kodga YOZILMAYDI - ishga tushganda o'zing kiritasan,
shunda GitHub'ga parol tushib qolmaydi.

Ishlatish:  python create_main_admin.py
(DATABASE_URL berilgan bo'lsa PostgreSQL'ga, bo'lmasa kinora.db ga yozadi)
"""
import getpass

from werkzeug.security import generate_password_hash

import app as kinora  # bazani ham yaratadi

username = input("Bosh admin logini: ").strip()
password = getpass.getpass("Parol (yozganda ko'rinmaydi): ")

if not kinora.valid_username(username):
    raise SystemExit("Login 3-32 belgi: harf, raqam, _ yoki . bo'lsin.")
if len(password) < 8:
    raise SystemExit("Parol kamida 8 belgi bo'lsin.")

db = kinora.connect()
if db.execute(kinora.adapt("SELECT 1 FROM users WHERE role=?"), ("main_admin",)).fetchone():
    raise SystemExit("Bosh admin allaqachon bor.")
db.execute(
    kinora.adapt("INSERT INTO users(username,password_hash,role,perms) VALUES(?,?,?,?)"),
    (username, generate_password_hash(password), "main_admin", ""),
)
db.commit()
db.close()
print("Tayyor! Endi:  python app.py  va /login sahifasidan kir.")
