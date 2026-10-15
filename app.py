"""KINORA - legal movie & series streaming platform (learning project).
Stack: Flask + SQLite. Pydroid 3 da ham ishlaydi.
Ishga tushirish:  python app.py
"""
import os
import re
import secrets
import sqlite3
import time
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "kinora.db")
SECRET_PATH = os.path.join(BASE, "secret.key")

ROLE_USER = "user"
ROLE_MAIN = "main_admin"          # bosh admin
ROLE_ASSIST = "assistant_admin"   # yordamchi admin

# Yordamchi adminga berilishi mumkin bo'lgan huquqlar
PERMS = {
    "add_content": "Kontent qo'shish",
    "edit_content": "Kontentni tahrirlash",
    "delete_content": "Kontentni o'chirish",
}

LANGS = {"uz": "O'zbek", "ru": "Русский", "en": "English", "tr": "Türkçe"}

TEXT = {
    "home": {"uz": "Bosh sahifa", "ru": "Главная", "en": "Home", "tr": "Ana sayfa"},
    "movies": {"uz": "Kinolar", "ru": "Фильмы", "en": "Movies", "tr": "Filmler"},
    "series": {"uz": "Seriallar", "ru": "Сериалы", "en": "Series", "tr": "Diziler"},
    "search": {"uz": "Qidirish...", "ru": "Поиск...", "en": "Search...", "tr": "Ara..."},
    "login": {"uz": "Kirish", "ru": "Войти", "en": "Log in", "tr": "Giriş"},
    "register": {"uz": "Ro'yxatdan o'tish", "ru": "Регистрация", "en": "Sign up", "tr": "Kayıt ol"},
    "logout": {"uz": "Chiqish", "ru": "Выйти", "en": "Log out", "tr": "Çıkış"},
    "mylist": {"uz": "Mening ro'yxatim", "ru": "Мой список", "en": "My List", "tr": "Listem"},
    "continue": {"uz": "Davom ettirish", "ru": "Продолжить просмотр", "en": "Continue watching", "tr": "İzlemeye devam et"},
    "latest": {"uz": "Yangi qo'shilganlar", "ru": "Новинки", "en": "Latest", "tr": "Yeni eklenenler"},
    "add_list": {"uz": "Ro'yxatga qo'shish", "ru": "В список", "en": "Add to list", "tr": "Listeye ekle"},
    "remove_list": {"uz": "Ro'yxatdan olish", "ru": "Убрать", "en": "Remove", "tr": "Kaldır"},
    "nothing": {"uz": "Hozircha hech narsa yo'q", "ru": "Пока ничего нет", "en": "Nothing here yet", "tr": "Henüz bir şey yok"},
    "admin": {"uz": "Admin panel", "ru": "Админ-панель", "en": "Admin panel", "tr": "Yönetim paneli"},
}

app = Flask(__name__)


def _secret():
    env = os.environ.get("KINORA_SECRET")
    if env:
        return env
    if not os.path.exists(SECRET_PATH):
        with open(SECRET_PATH, "w") as f:
            f.write(secrets.token_hex(32))
    with open(SECRET_PATH) as f:
        return f.read().strip()


app.config["SECRET_KEY"] = _secret()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ---------------------------------------------------------------- database

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  perms TEXT NOT NULL DEFAULT '',
  created TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS content(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  year INTEGER,
  genre TEXT,
  kind TEXT NOT NULL DEFAULT 'movie',
  poster_url TEXT,
  video_url TEXT,
  created_by INTEGER,
  created TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS mylist(
  user_id INTEGER, content_id INTEGER,
  PRIMARY KEY(user_id, content_id)
);
CREATE TABLE IF NOT EXISTS history(
  user_id INTEGER, content_id INTEGER, updated TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(user_id, content_id)
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.commit()
    db.close()


def q(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def run(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur


# ---------------------------------------------------------------- helpers

def is_admin():
    return g.user is not None and g.user["role"] in (ROLE_MAIN, ROLE_ASSIST)


def has_perm(p):
    if g.user is None:
        return False
    if g.user["role"] == ROLE_MAIN:
        return True
    return g.user["role"] == ROLE_ASSIST and p in g.user["perms"].split(",")


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if g.user is None:
            return redirect(url_for("login", next=request.path))
        return f(*a, **k)
    return w


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not is_admin():
            abort(403)
        return f(*a, **k)
    return w


def perm_required(p):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if not has_perm(p):
                abort(403)
            return f(*a, **k)
        return w
    return deco


def main_required(f):
    @wraps(f)
    def w(*a, **k):
        if g.user is None or g.user["role"] != ROLE_MAIN:
            abort(403)
        return f(*a, **k)
    return w


def safe_url(value):
    value = (value or "").strip()
    return value if re.match(r"^https?://", value, re.I) else ""


def valid_username(u):
    return bool(re.match(r"^[A-Za-z0-9_.]{3,32}$", u or ""))


# ---------------------------------------------------------------- hooks

@app.before_request
def load_user():
    g.user = None
    uid = session.get("uid")
    if uid:
        g.user = q("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if g.user is None:
            session.clear()
    if request.method == "POST":
        token = session.get("csrf")
        if not token or token != request.form.get("csrf"):
            abort(400)


@app.context_processor
def inject():
    lang = session.get("lang", "uz")

    def t(key):
        return TEXT.get(key, {}).get(lang, key)

    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return dict(t=t, lang=lang, LANGS=LANGS, csrf=session["csrf"],
                is_admin=is_admin(), has_perm=has_perm, PERMS=PERMS,
                ROLE_MAIN=ROLE_MAIN, ROLE_ASSIST=ROLE_ASSIST)


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


# ---------------------------------------------------------------- public

@app.route("/")
def home():
    latest = q("SELECT * FROM content ORDER BY id DESC LIMIT 12")
    movies = q("SELECT * FROM content WHERE kind='movie' ORDER BY id DESC LIMIT 12")
    series = q("SELECT * FROM content WHERE kind='series' ORDER BY id DESC LIMIT 12")
    cont = []
    if g.user:
        cont = q("""SELECT c.* FROM history h JOIN content c ON c.id=h.content_id
                    WHERE h.user_id=? ORDER BY h.updated DESC LIMIT 12""",
                 (g.user["id"],))
    hero = latest[0] if latest else None
    return render_template("home.html", latest=latest, movies=movies,
                           series=series, cont=cont, hero=hero)


@app.route("/browse/<kind>")
def browse(kind):
    if kind not in ("movie", "series"):
        abort(404)
    items = q("SELECT * FROM content WHERE kind=? ORDER BY id DESC", (kind,))
    return render_template("browse.html", items=items, kind=kind)


@app.route("/search")
def search():
    term = (request.args.get("q") or "").strip()[:80]
    items = []
    if term:
        like = "%" + term.replace("%", "").replace("_", "") + "%"
        items = q("""SELECT * FROM content WHERE title LIKE ? OR genre LIKE ?
                     ORDER BY id DESC""", (like, like))
    return render_template("browse.html", items=items, kind=None, term=term)


@app.route("/title/<int:cid>")
def detail(cid):
    item = q("SELECT * FROM content WHERE id=?", (cid,), one=True)
    if item is None:
        abort(404)
    saved = False
    if g.user:
        saved = q("SELECT 1 FROM mylist WHERE user_id=? AND content_id=?",
                  (g.user["id"], cid), one=True) is not None
        run("INSERT OR REPLACE INTO history(user_id,content_id,updated) "
            "VALUES(?,?,CURRENT_TIMESTAMP)", (g.user["id"], cid))
    return render_template("detail.html", item=item, saved=saved)


@app.route("/mylist")
@login_required
def mylist():
    items = q("""SELECT c.* FROM mylist m JOIN content c ON c.id=m.content_id
                 WHERE m.user_id=? ORDER BY c.id DESC""", (g.user["id"],))
    return render_template("browse.html", items=items, kind="mylist")


@app.route("/mylist/<int:cid>", methods=["POST"])
@login_required
def mylist_toggle(cid):
    exists = q("SELECT 1 FROM mylist WHERE user_id=? AND content_id=?",
               (g.user["id"], cid), one=True)
    if exists:
        run("DELETE FROM mylist WHERE user_id=? AND content_id=?", (g.user["id"], cid))
    else:
        run("INSERT INTO mylist(user_id,content_id) VALUES(?,?)", (g.user["id"], cid))
    return redirect(url_for("detail", cid=cid))


@app.route("/lang/<code>")
def set_lang(code):
    if code in LANGS:
        session["lang"] = code
    return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------------- auth

_attempts = {}  # ip -> [count, first_time]


def too_many(ip):
    c = _attempts.get(ip)
    if not c:
        return False
    if time.time() - c[1] > 300:
        _attempts.pop(ip, None)
        return False
    return c[0] >= 8


def fail(ip):
    c = _attempts.setdefault(ip, [0, time.time()])
    c[0] += 1


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr or "?"
        if too_many(ip):
            flash("Juda ko'p urinish. 5 daqiqadan keyin qayta urinib ko'ring.", "error")
            return render_template("login.html"), 429
        u = q("SELECT * FROM users WHERE username=?",
              (request.form.get("username", "").strip(),), one=True)
        if u and check_password_hash(u["password_hash"], request.form.get("password", "")):
            _attempts.pop(ip, None)
            session.clear()
            session["uid"] = u["id"]
            nxt = request.args.get("next", "")
            if not nxt.startswith("/") or nxt.startswith("//"):
                nxt = url_for("admin_home") if u["role"] != ROLE_USER else url_for("home")
            return redirect(nxt)
        fail(ip)
        flash("Login yoki parol noto'g'ri.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not valid_username(username):
            flash("Login 3-32 belgi: harf, raqam, _ yoki . bo'lsin.", "error")
        elif len(password) < 8:
            flash("Parol kamida 8 belgi bo'lsin.", "error")
        elif q("SELECT 1 FROM users WHERE username=?", (username,), one=True):
            flash("Bu login band.", "error")
        else:
            run("INSERT INTO users(username,email,password_hash,role) VALUES(?,?,?,?)",
                (username, request.form.get("email", "").strip()[:120],
                 generate_password_hash(password), ROLE_USER))
            flash("Ro'yxatdan o'tdingiz. Endi kiring.", "ok")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------------------------------------------------------- admin

@app.route("/admin")
@admin_required
def admin_home():
    stats = {
        "content": q("SELECT COUNT(*) c FROM content", one=True)["c"],
        "movies": q("SELECT COUNT(*) c FROM content WHERE kind='movie'", one=True)["c"],
        "series": q("SELECT COUNT(*) c FROM content WHERE kind='series'", one=True)["c"],
        "users": q("SELECT COUNT(*) c FROM users WHERE role='user'", one=True)["c"],
        "admins": q("SELECT COUNT(*) c FROM users WHERE role!='user'", one=True)["c"],
    }
    items = q("SELECT * FROM content ORDER BY id DESC")
    return render_template("admin/dashboard.html", stats=stats, items=items)


def read_content_form():
    f = request.form
    kind = f.get("kind", "movie")
    try:
        year = int(f.get("year") or 0) or None
    except ValueError:
        year = None
    return dict(
        title=f.get("title", "").strip()[:150],
        description=f.get("description", "").strip()[:3000],
        year=year,
        genre=f.get("genre", "").strip()[:80],
        kind=kind if kind in ("movie", "series") else "movie",
        poster_url=safe_url(f.get("poster_url")),
        video_url=safe_url(f.get("video_url")),
    )


@app.route("/admin/content/new", methods=["GET", "POST"])
@perm_required("add_content")
def content_new():
    if request.method == "POST":
        d = read_content_form()
        if not d["title"]:
            flash("Sarlavha kerak.", "error")
            return render_template("admin/content_form.html", item=d, new=True)
        run("""INSERT INTO content(title,description,year,genre,kind,poster_url,video_url,created_by)
               VALUES(:title,:description,:year,:genre,:kind,:poster_url,:video_url,:by)""",
            {**d, "by": g.user["id"]})
        flash("Kontent qo'shildi.", "ok")
        return redirect(url_for("admin_home"))
    return render_template("admin/content_form.html", item={"kind": "movie"}, new=True)


@app.route("/admin/content/<int:cid>/edit", methods=["GET", "POST"])
@perm_required("edit_content")
def content_edit(cid):
    item = q("SELECT * FROM content WHERE id=?", (cid,), one=True)
    if item is None:
        abort(404)
    if request.method == "POST":
        d = read_content_form()
        if not d["title"]:
            flash("Sarlavha kerak.", "error")
            return render_template("admin/content_form.html", item=d, new=False, cid=cid)
        run("""UPDATE content SET title=:title,description=:description,year=:year,
               genre=:genre,kind=:kind,poster_url=:poster_url,video_url=:video_url
               WHERE id=:id""", {**d, "id": cid})
        flash("Saqlandi.", "ok")
        return redirect(url_for("admin_home"))
    return render_template("admin/content_form.html", item=item, new=False, cid=cid)


@app.route("/admin/content/<int:cid>/delete", methods=["POST"])
@perm_required("delete_content")
def content_delete(cid):
    run("DELETE FROM content WHERE id=?", (cid,))
    run("DELETE FROM mylist WHERE content_id=?", (cid,))
    run("DELETE FROM history WHERE content_id=?", (cid,))
    flash("O'chirildi.", "ok")
    return redirect(url_for("admin_home"))


@app.route("/admin/admins", methods=["GET", "POST"])
@main_required
def admins():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        perms = [p for p in request.form.getlist("perms") if p in PERMS]
        if not valid_username(username):
            flash("Login 3-32 belgi: harf, raqam, _ yoki .", "error")
        elif len(password) < 8:
            flash("Parol kamida 8 belgi bo'lsin.", "error")
        elif q("SELECT 1 FROM users WHERE username=?", (username,), one=True):
            flash("Bu login band.", "error")
        else:
            run("INSERT INTO users(username,password_hash,role,perms) VALUES(?,?,?,?)",
                (username, generate_password_hash(password), ROLE_ASSIST, ",".join(perms)))
            flash("Yordamchi admin qo'shildi.", "ok")
        return redirect(url_for("admins"))
    rows = q("SELECT * FROM users WHERE role!='user' ORDER BY role, id")
    return render_template("admin/admins.html", rows=rows)


@app.route("/admin/admins/<int:uid>/perms", methods=["POST"])
@main_required
def admin_perms(uid):
    u = q("SELECT * FROM users WHERE id=? AND role=?", (uid, ROLE_ASSIST), one=True)
    if u is None:
        abort(404)
    perms = [p for p in request.form.getlist("perms") if p in PERMS]
    run("UPDATE users SET perms=? WHERE id=?", (",".join(perms), uid))
    flash("Huquqlar yangilandi.", "ok")
    return redirect(url_for("admins"))


@app.route("/admin/admins/<int:uid>/delete", methods=["POST"])
@main_required
def admin_delete(uid):
    u = q("SELECT * FROM users WHERE id=? AND role=?", (uid, ROLE_ASSIST), one=True)
    if u is None:
        abort(404)
    run("DELETE FROM users WHERE id=?", (uid,))
    flash("Admin o'chirildi.", "ok")
    return redirect(url_for("admins"))


@app.route("/admin/password", methods=["GET", "POST"])
@admin_required
def change_password():
    if request.method == "POST":
        old = request.form.get("old", "")
        new = request.form.get("new", "")
        if not check_password_hash(g.user["password_hash"], old):
            flash("Eski parol noto'g'ri.", "error")
        elif len(new) < 8:
            flash("Yangi parol kamida 8 belgi bo'lsin.", "error")
        else:
            run("UPDATE users SET password_hash=? WHERE id=?",
                (generate_password_hash(new), g.user["id"]))
            flash("Parol almashtirildi.", "ok")
            return redirect(url_for("admin_home"))
    return render_template("admin/password.html")


@app.errorhandler(403)
def e403(_e):
    return render_template("error.html", code=403, msg="Ruxsat yo'q"), 403


@app.errorhandler(404)
def e404(_e):
    return render_template("error.html", code=404, msg="Sahifa topilmadi"), 404


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
