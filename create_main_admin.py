"""Bosh adminni yaratadi (bir marta ishlatiladi).
Login va parol kodga YOZILMAYDI - ishga tushganda o'zing kiritasan,
shunda GitHub'ga parol tushib qolmaydi.

Ishlatish:  python create_main_admin.py
"""
import getpass
import sqlite3

from werkzeug.security import generate_password_hash

import app as kinora  # bazani ham yaratadi

username = input("Bosh admin logini: ").strip()
password = getpass.getpass("Parol (yozganda ko'rinmaydi): ")

if not kinora.valid_username(username):
    raise SystemExit("Login 3-32 belgi: harf, raqam, _ yoki . bo'lsin.")
if len(password) < 8:
    raise SystemExit("Parol kamida 8 belgi bo'lsin.")

db = sqlite3.connect(kinora.DB_PATH)
if db.execute("SELECT 1 FROM users WHERE role='main_admin'").fetchone():
    raise SystemExit("Bosh admin allaqachon bor.")
db.execute(
    "INSERT INTO users(username,password_hash,role,perms) VALUES(?,?,?,?)",
    (username, generate_password_hash(password), "main_admin", ""),
)
db.commit()
db.close()
print("Tayyor! Endi:  python app.py  va /login sahifasidan kir.")
