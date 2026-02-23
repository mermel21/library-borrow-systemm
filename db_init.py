import sqlite3
import hashlib   

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# 1. เชื่อมต่อ (หรือสร้างไฟล์ถ้าไม่มี)
conn = sqlite3.connect("library.db")
c = conn.cursor()
# 2. สร้างตาราง books ถ้ายังไม่มี
c.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    status TEXT DEFAULT 'available'
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS members (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    member_code  TEXT NOT NULL UNIQUE,        -- รหัสสมาชิก เช่น M001
    name         TEXT NOT NULL,              -- ชื่อ - สกุล
    gender       TEXT,                       -- เพศ (หญิง/ชาย/อื่น ๆ)
    email        TEXT UNIQUE,                -- อีเมล (ไม่จำเป็น แต่ถ้ามีให้ไม่ซ้ำ)
    phone        TEXT,                       -- เบอร์โทร
    is_active    INTEGER DEFAULT 1,          -- สถานะการใช้งาน 1=ใช้งาน, 0=ยกเลิก
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

# -------------------------
# users (NEW)   เพิ่มส่วนนี้ 
# -------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','staff')),
    is_active INTEGER NOT NULL DEFAULT 1
)
""")
# seed admin (ถ้ายังไม่มี user เลย)  เพิ่มส่วนนี้ 
c.execute("SELECT COUNT(*) FROM users")
(count,) = c.fetchone()
if count == 0:
    c.execute(
        "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)",
        ("admin", hash_password("1234"), "admin", 1)
    )
# 3. บันทึกการเปลี่ยนแปลง  ของเดิม ไม่ต้องเปลี่ยนแปลง
conn.commit()
# 4. ปิดการเชื่อมต่อ
conn.close()

# บังคับ admin ให้ active เสมอ
c.execute("""
UPDATE users
SET is_active = 1
WHERE username = 'admin'
""")

import sqlite3

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# เพิ่ม user teacher
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, role)
VALUES ('teacher', '1234', 'admin')
""")

conn.commit()
conn.close()