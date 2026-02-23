import sqlite3
import pandas as pd
import hashlib

DB_PATH = "library.db"

# ============================================================
# DB
# ============================================================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ============================================================
# PASSWORD
# ============================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ============================================================
# USER
# ============================================================
def get_user_auth_row(username: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, password_hash, role, is_active
        FROM users
        WHERE username=?
    """, (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": row[4]
    }


def get_all_users() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("""
        SELECT
            id,
            username,
            role,
            is_active,
            CASE WHEN is_active=1 THEN 'ใช้งาน' ELSE 'ปิดใช้งาน' END AS status
        FROM users
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


# ============================================================
# BOOK
# ============================================================
def get_all_books() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("""
        SELECT id, title, author, status
        FROM books
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def get_available_books() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("""
        SELECT id, title, author
        FROM books
        WHERE status='available'
    """, conn)
    conn.close()
    return df


def set_book_status(book_id: int, status: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE books
        SET status=?
        WHERE id=?
    """, (status, book_id))
    conn.commit()
    conn.close()

def insert_book(title: str, author: str):
    """
    เพิ่มหนังสือใหม่
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO books (title, author, status)
        VALUES (?, ?, 'available')
    """, (title, author))

    conn.commit()
    conn.close()


# ============================================================
# MEMBER
# ============================================================
def get_all_members() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("""
        SELECT *
        FROM members
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def get_active_members() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("""
        SELECT id, member_code, name
        FROM members
        WHERE is_active=1
    """, conn)
    conn.close()
    return df

def insert_member(name: str, email: str, phone: str):
    """
    เพิ่มสมาชิกใหม่
    """
    conn = get_connection()
    c = conn.cursor()

    # สร้างรหัสสมาชิกอัตโนมัติ เช่น M0001
    c.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM members")
    next_id = c.fetchone()[0]
    member_code = f"M{next_id:04d}"

    c.execute("""
        INSERT INTO members (member_code, name, email, phone, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (member_code, name, email, phone))

    conn.commit()
    conn.close()


# ============================================================
# BORROW
# ============================================================
def ensure_borrow_schema():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS borrow_tx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            staff_user_id INTEGER NOT NULL,
            borrow_date TEXT DEFAULT CURRENT_TIMESTAMP,
            default_due_date TEXT NOT NULL,
            status TEXT DEFAULT 'open'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS borrow_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT DEFAULT 'borrowed',
            return_staff_user_id INTEGER
        )
    """)

    conn.commit()
    conn.close()


def create_borrow_transaction(
    member_id: int,
    book_ids: list,
    staff_user_id: int,
    default_due_date: str
):
    """
    สร้างรายการยืมหนังสือ
    - 1 transaction ต่อการยืม
    - 1 รายการต่อ 1 หนังสือ
    """
    ensure_borrow_schema()
    conn = get_connection()
    c = conn.cursor()

    try:
        # สร้าง transaction หลัก
        c.execute("""
            INSERT INTO borrow_tx (member_id, staff_user_id, default_due_date)
            VALUES (?, ?, ?)
        """, (member_id, staff_user_id, default_due_date))

        tx_id = c.lastrowid

        # เพิ่มหนังสือที่ยืม
        for book_id in book_ids:
            c.execute("""
                INSERT INTO borrow_items (tx_id, book_id, due_date)
                VALUES (?, ?, ?)
            """, (tx_id, book_id, default_due_date))

            c.execute("""
                UPDATE books
                SET status='borrowed'
                WHERE id=?
            """, (book_id,))

        conn.commit()
        return tx_id

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()

def get_active_borrow_items_by_member(member_id: int) -> pd.DataFrame:
    """
    ดึงรายการหนังสือที่ยังไม่คืน ของสมาชิก 1 คน
    ใช้ในหน้า 'คืนหนังสือ'
    """
    ensure_borrow_schema()
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            bi.id AS item_id,
            tx.id AS tx_id,
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.id AS book_id,
            bk.title AS ชื่อหนังสือ,
            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        WHERE bi.status = 'borrowed'
          AND m.id = ?
        ORDER BY bi.id DESC
    """, conn, params=(member_id,))

    conn.close()
    return df

def get_active_borrow_items() -> pd.DataFrame:
    """
    ดึงรายการหนังสือที่กำลังถูกยืมอยู่ทั้งหมด
    ใช้ในหน้า 'รายการยืมปัจจุบัน'
    """
    ensure_borrow_schema()
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            bi.id AS item_id,
            tx.id AS tx_id,
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.id AS book_id,
            bk.title AS ชื่อหนังสือ,
            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        WHERE bi.status = 'borrowed'
        ORDER BY bi.id DESC
    """, conn)

    conn.close()
    return df

def get_borrow_history(limit: int = 200) -> pd.DataFrame:
    """
    ดึงประวัติการยืม-คืนทั้งหมด (ทั้งที่คืนแล้วและยังไม่คืน)
    ใช้ในหน้า ประวัติการยืม-คืน
    """
    ensure_borrow_schema()
    conn = get_connection()

    df = pd.read_sql_query(f"""
        SELECT
            bi.id AS item_id,
            tx.id AS tx_id,

            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,

            bk.id AS รหัสหนังสือ,
            bk.title AS ชื่อหนังสือ,

            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง,
            bi.return_date AS วันที่คืน,

            bi.status AS สถานะ,

            u1.username AS ผู้ทำรายการยืม,
            u2.username AS ผู้ทำรายการคืน
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        LEFT JOIN users u1 ON u1.id = tx.staff_user_id
        LEFT JOIN users u2 ON u2.id = bi.return_staff_user_id
        ORDER BY bi.id DESC
        LIMIT {int(limit)}
    """, conn)

    conn.close()
    return df

############ ดึงข้อมูลสรุปสถานะหนังสือทั้งหมด ##############
def get_book_status_summary() -> pd.DataFrame:
    """ดึงข้อมูลจำนวนหนังสือ แยกตามสถานะ"""

    conn = get_connection()

    query = """
        SELECT
            status AS สถานะหนังสือ,
            COUNT(*) AS จำนวน
        FROM books
        GROUP BY status
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df

############## ดึงข้อมูลสรุปจำนวนการยืมรายเดือน ##############
def get_borrow_summary_by_month(
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    สรุปจำนวนการยืมรายเดือน ตามช่วงวันที่ที่กำหนด
    """

    conn = get_connection()

    query = """
        SELECT
            strftime('%Y-%m', borrow_date) AS เดือน,
            COUNT(*) AS จำนวนการยืม
        FROM borrow_tx
        WHERE DATE(borrow_date) BETWEEN ? AND ?
        GROUP BY strftime('%Y-%m', borrow_date)
        ORDER BY เดือน
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=[start_date, end_date]
    )

    conn.close()

    return df

######### ดึงข้อมูลรายงานการยืม-คืนทั้งหมด (กรองตามช่วงเวลา) #########
def get_borrow_report(
    start_date: str,
    end_date: str,
    status: str
) -> pd.DataFrame:
    """
    รายงานการยืม-คืนทั้งหมด
    - กรองตามช่วงเวลา
    - กรองตามสถานะ borrowed / returned / all
    """

    conn = get_connection()

    base_query = """
        SELECT
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.title AS ชื่อหนังสือ,
            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง,
            bi.return_date AS วันที่คืน,
            bi.status AS สถานะ,
            u1.username AS ผู้ทำรายการยืม,
            u2.username AS ผู้ทำรายการคืน
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        JOIN users u1 ON u1.id = tx.staff_user_id
        LEFT JOIN users u2 ON u2.id = bi.return_staff_user_id
        WHERE DATE(tx.borrow_date) BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    # กรองตามสถานะ (ถ้าไม่ใช่ all)
    if status != "all":
        base_query += " AND bi.status = ?"
        params.append(status)

    # เรียงจากล่าสุดไปเก่าสุด
    base_query += " ORDER BY tx.borrow_date DESC"

    df = pd.read_sql_query(
        base_query,
        conn,
        params=params
    )

    conn.close()

    return df
