import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "mandarin.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            character   TEXT NOT NULL,
            pinyin      TEXT NOT NULL,
            translation TEXT NOT NULL,
            gram_type   TEXT,
            example     TEXT,
            chapter     TEXT,
            notes       TEXT,
            difficulty  INTEGER DEFAULT 1,
            mastered    INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS srs_cards (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id         INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
            due_date        TEXT NOT NULL DEFAULT (date('now')),
            interval_days   INTEGER DEFAULT 1,
            ease_factor     REAL DEFAULT 2.5,
            repetitions     INTEGER DEFAULT 0,
            last_quality    INTEGER DEFAULT -1
        );

        CREATE TABLE IF NOT EXISTS study_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id     INTEGER REFERENCES words(id) ON DELETE SET NULL,
            session_id  TEXT,
            quality     INTEGER,
            correct     INTEGER,
            mode        TEXT,
            studied_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            body        TEXT,
            category    TEXT,
            tags        TEXT,
            chapter     TEXT,
            word_id     INTEGER REFERENCES words(id) ON DELETE SET NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );
        """)


# ─── WORDS ────────────────────────────────────────────────────────────────────

def add_word(character, pinyin, translation, gram_type="", example="",
             chapter="", notes="", difficulty=1):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO words (character,pinyin,translation,gram_type,
               example,chapter,notes,difficulty)
               VALUES (?,?,?,?,?,?,?,?)""",
            (character, pinyin, translation, gram_type, example, chapter, notes, difficulty)
        )
        word_id = cur.lastrowid
        conn.execute("INSERT INTO srs_cards (word_id) VALUES (?)", (word_id,))
        return word_id


def update_word(word_id, character, pinyin, translation, gram_type, example,
                chapter, notes, difficulty, mastered):
    with get_conn() as conn:
        conn.execute(
            """UPDATE words SET character=?,pinyin=?,translation=?,gram_type=?,
               example=?,chapter=?,notes=?,difficulty=?,mastered=?
               WHERE id=?""",
            (character, pinyin, translation, gram_type, example, chapter,
             notes, difficulty, mastered, word_id)
        )


def delete_word(word_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM words WHERE id=?", (word_id,))


def get_words(chapter=None, gram_type=None, difficulty=None, mastered=None, search=None):
    query = "SELECT * FROM words WHERE 1=1"
    params = []
    if chapter:
        query += " AND chapter=?"; params.append(chapter)
    if gram_type:
        query += " AND gram_type=?"; params.append(gram_type)
    if difficulty:
        query += " AND difficulty=?"; params.append(difficulty)
    if mastered is not None:
        query += " AND mastered=?"; params.append(mastered)
    if search:
        query += " AND (character LIKE ? OR pinyin LIKE ? OR translation LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_word(word_id):
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM words WHERE id=?", (word_id,)).fetchone()
        return dict(r) if r else None


def get_words_for_combo():
    """Retorna lista simplificada para popular comboboxes."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, character, pinyin, translation FROM words ORDER BY character"
        ).fetchall()
        return [dict(r) for r in rows]


def get_chapters():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT chapter FROM words WHERE chapter != '' ORDER BY chapter"
        ).fetchall()
        return [r[0] for r in rows]


def get_gram_types():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT gram_type FROM words WHERE gram_type != '' ORDER BY gram_type"
        ).fetchall()
        return [r[0] for r in rows]


def import_words_csv(rows):
    added = 0; skipped = 0
    with get_conn() as conn:
        for row in rows:
            char = row.get("character", "").strip()
            if not char:
                skipped += 1; continue
            cur = conn.execute(
                """INSERT INTO words (character,pinyin,translation,gram_type,
                   example,chapter,notes,difficulty) VALUES (?,?,?,?,?,?,?,?)""",
                (char, row.get("pinyin","").strip(), row.get("translation","").strip(),
                 row.get("gram_type","").strip(), row.get("example","").strip(),
                 row.get("chapter","").strip(), row.get("notes","").strip(),
                 int(row.get("difficulty",1)))
            )
            conn.execute("INSERT INTO srs_cards (word_id) VALUES (?)", (cur.lastrowid,))
            added += 1
    return added, skipped


# ─── SRS ──────────────────────────────────────────────────────────────────────

def get_due_cards(chapter=None, limit=20):
    today = date.today().isoformat()
    query = """
        SELECT w.*, s.id as card_id, s.due_date, s.interval_days,
               s.ease_factor, s.repetitions
        FROM srs_cards s JOIN words w ON w.id = s.word_id
        WHERE s.due_date <= ? AND w.mastered != 1
    """
    params = [today]
    if chapter:
        query += " AND w.chapter=?"; params.append(chapter)
    query += " ORDER BY s.due_date ASC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def update_srs(word_id, quality, session_id, mode):
    with get_conn() as conn:
        card = conn.execute(
            "SELECT * FROM srs_cards WHERE word_id=?", (word_id,)
        ).fetchone()
        if not card: return
        ef = card["ease_factor"]; reps = card["repetitions"]; interval = card["interval_days"]
        if quality < 3:
            reps = 0; interval = 1
        else:
            if reps == 0: interval = 1
            elif reps == 1: interval = 6
            else: interval = round(interval * ef)
            reps += 1
        ef = max(1.3, ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        due = (date.fromordinal(date.today().toordinal() + interval)).isoformat()
        conn.execute(
            """UPDATE srs_cards SET interval_days=?,ease_factor=?,repetitions=?,
               due_date=?,last_quality=? WHERE word_id=?""",
            (interval, ef, reps, due, quality, word_id)
        )
        conn.execute(
            """INSERT INTO study_log (word_id,session_id,quality,correct,mode)
               VALUES (?,?,?,?,?)""",
            (word_id, session_id, quality, 1 if quality >= 3 else 0, mode)
        )


# ─── NOTES ────────────────────────────────────────────────────────────────────

def add_note(title, body, category="", tags="[]", chapter="", word_id=None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO notes (title,body,category,tags,chapter,word_id)
               VALUES (?,?,?,?,?,?)""",
            (title, body, category, tags, chapter, word_id)
        )
        return cur.lastrowid


def update_note(note_id, title, body, category, tags, chapter, word_id):
    with get_conn() as conn:
        conn.execute(
            """UPDATE notes SET title=?,body=?,category=?,tags=?,chapter=?,
               word_id=?,updated_at=datetime('now') WHERE id=?""",
            (title, body, category, tags, chapter, word_id, note_id)
        )


def delete_note(note_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))


def get_notes(search=None, category=None, chapter=None):
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR body LIKE ? OR tags LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if category:
        query += " AND category=?"; params.append(category)
    if chapter:
        query += " AND chapter=?"; params.append(chapter)
    query += " ORDER BY updated_at DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_notes_by_word(word_id):
    """Retorna todas as anotações vinculadas a uma palavra."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE word_id=? ORDER BY updated_at DESC",
            (word_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_note_categories():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM notes WHERE category != '' ORDER BY category"
        ).fetchall()
        return [r[0] for r in rows]


# ─── STATS ────────────────────────────────────────────────────────────────────

def get_daily_stats(days=30):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT DATE(studied_at) as day, COUNT(*) as total, SUM(correct) as correct
               FROM study_log WHERE studied_at >= datetime('now', ?)
               GROUP BY day ORDER BY day""",
            (f"-{days} days",)
        ).fetchall()
        return [dict(r) for r in rows]


def get_chapter_stats():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT w.chapter, COUNT(*) as total,
               SUM(w.mastered=1) as mastered, SUM(w.mastered=2) as needs_review,
               AVG(CASE WHEN sl.correct IS NOT NULL THEN sl.correct ELSE NULL END) as avg_correct
               FROM words w LEFT JOIN study_log sl ON sl.word_id = w.id
               WHERE w.chapter != '' GROUP BY w.chapter ORDER BY w.chapter"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_overall_stats():
    with get_conn() as conn:
        words        = conn.execute("SELECT COUNT(*) as c FROM words").fetchone()["c"]
        mastered     = conn.execute("SELECT COUNT(*) as c FROM words WHERE mastered=1").fetchone()["c"]
        due          = conn.execute("SELECT COUNT(*) as c FROM srs_cards WHERE due_date <= date('now')").fetchone()["c"]
        studied_today= conn.execute(
            "SELECT COUNT(DISTINCT word_id) as c FROM study_log WHERE DATE(studied_at) = date('now')"
        ).fetchone()["c"]
        return {"total_words": words, "mastered": mastered,
                "due_today": due, "studied_today": studied_today}