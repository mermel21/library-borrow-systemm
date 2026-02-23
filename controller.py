import hashlib
import model

# =========================
# Password Hash
# =========================
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# =========================
# Auth / Login
# =========================
def login(username: str, password: str):
    errors = []

    if not username.strip():
        errors.append("กรุณากรอกชื่อผู้ใช้")
    if not password.strip():
        errors.append("กรุณากรอกรหัสผ่าน")

    if errors:
        return False, errors, None

    user = model.get_user_auth_row(username)

    if not user:
        return False, ["ไม่พบบัญชีผู้ใช้"], None

    if user["is_active"] != 1:
        return False, ["บัญชีนี้ถูกปิดใช้งาน"], None

    if _hash_password(password) != user["password_hash"]:
        return False, ["รหัสผ่านไม่ถูกต้อง"], None

    return True, ["เข้าสู่ระบบสำเร็จ"], {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }


# =========================
# Book Controller
# =========================
def create_book(title: str, author: str):
    if not title.strip() or not author.strip():
        return False, ["กรุณากรอกชื่อหนังสือและผู้แต่ง"]

    model.insert_book(title.strip(), author.strip())
    return True, ["เพิ่มหนังสือเรียบร้อย"]


def update_book(book_id: int, title: str, author: str):
    model.update_book(book_id, title.strip(), author.strip())
    return True, ["แก้ไขหนังสือเรียบร้อย"]


def delete_book(book_id: int):
    model.delete_book(book_id)
    return True, ["ลบหนังสือเรียบร้อย"]


# =========================
# Member Controller
# =========================
def create_member(name: str, email: str, phone: str):
    errors = []

    if not name.strip():
        errors.append("กรุณากรอกชื่อสมาชิก")
    if not email.strip():
        errors.append("กรุณากรอกอีเมล")
    if not phone.strip():
        errors.append("กรุณากรอกเบอร์โทรศัพท์")

    if errors:
        return False, errors

    model.insert_member(name.strip(), email.strip(), phone.strip())
    return True, ["เพิ่มสมาชิกเรียบร้อย"]


def update_member(member_id: int, name: str, email: str, phone: str):
    model.update_member(
        member_id,
        name.strip(),
        email.strip(),
        phone.strip()
    )
    return True, ["แก้ไขสมาชิกเรียบร้อย"]


def delete_member(member_id: int):
    model.delete_member(member_id)
    return True, ["ลบสมาชิกเรียบร้อย"]


# =========================
# Borrow Controller
# =========================
def borrow_book(member_id: int, book_id: int):
    model.insert_borrow(member_id, book_id)
    return True, ["ยืมหนังสือเรียบร้อย"]


def return_borrow(borrow_id: int):
    model.return_book(borrow_id)
    return True, ["คืนหนังสือเรียบร้อย"]

# =========================
# Admin / User Controller
# =========================
def create_user(username: str, password: str, role: str, is_active: bool):
    errors = []

    if not username.strip():
        errors.append("กรุณากรอกชื่อผู้ใช้")
    if len(username.strip()) < 3:
        errors.append("ชื่อผู้ใช้ต้องอย่างน้อย 3 ตัวอักษร")

    if not password.strip():
        errors.append("กรุณากรอกรหัสผ่าน")
    if len(password.strip()) < 4:
        errors.append("รหัสผ่านต้องอย่างน้อย 4 ตัวอักษร")

    if role not in ("admin", "staff"):
        errors.append("Role ต้องเป็น admin หรือ staff")

    if model.is_username_exists(username):
        errors.append("ชื่อผู้ใช้นี้มีอยู่แล้ว")

    if errors:
        return False, errors

    model.add_user(
        username=username.strip(),
        password_hash=_hash_password(password),
        role=role,
        is_active=1 if is_active else 0
    )

    return True, ["เพิ่มผู้ใช้เรียบร้อยแล้ว"]

# ============================================================
# Borrow: multi-book per transaction
# ============================================================
def borrow_books(member_id: int, staff_user_id: int, due_date_iso: str | None, book_ids: list[int], note: str | None = None):
    """
    สร้างรายการยืม 1 ครั้ง (หลายเล่ม)
    - ต้องระบุ staff_user_id เพื่อบันทึกว่าใครเป็นผู้ทำรายการ
    """
    errors = []
    if not member_id:
        errors.append("กรุณาเลือกสมาชิก")
    if not staff_user_id:
        errors.append("ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)")
    if not book_ids:
        errors.append("กรุณาเลือกหนังสืออย่างน้อย 1 เล่ม")
    if errors:
        return False, errors, None

    try:
        tx_id = model.create_borrow_transaction(
            member_id=int(member_id),
            staff_user_id=int(staff_user_id),
            default_due_date=due_date_iso,
            book_ids=[int(x) for x in book_ids],
           
        )
        return True, [f"บันทึกการยืมเรียบร้อยแล้ว (TX: {tx_id})"], tx_id
    except Exception as e:
        return False, [f"ไม่สามารถบันทึกการยืมได้: {e}"], None

def return_book_item(item_id: int, return_staff_user_id: int):
    """คืนหนังสือทีละเล่ม พร้อมบันทึกผู้ทำรายการคืน"""
    if not item_id:
        return False, ["กรุณาเลือกรายการที่จะคืน"]
    if not return_staff_user_id:
        return False, ["ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)"]

    ok = model.return_borrow_item(int(item_id), int(return_staff_user_id))
    if not ok:
        return False, ["ไม่พบรายการที่ยังไม่คืน หรือรายการถูกคืนแล้ว"]
    return True, ["บันทึกการคืนเรียบร้อยแล้ว"]

def return_book_items(item_ids: list[int], return_staff_user_id: int):
    """
    คืนหนังสือหลายรายการ (ติ๊กได้หลายเล่ม) พร้อมบันทึกผู้ทำรายการคืน
    return: (ok:bool, messages:list[str])
    """
    if not item_ids:
        return False, ["กรุณาเลือกรายการที่จะคืนอย่างน้อย 1 รายการ"]
    if not return_staff_user_id:
        return False, ["ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)"]

    success = 0
    failed = []

    for item_id in item_ids:
        try:
            ok = model.return_borrow_item(int(item_id), int(return_staff_user_id))
            if ok:
                success += 1
            else:
                failed.append(int(item_id))
        except Exception:
            failed.append(int(item_id))

    msgs = [f"บันทึกการคืนสำเร็จ {success} รายการ"]
    if failed:
        msgs.append(f"รายการที่คืนไม่สำเร็จ/ถูกคืนแล้ว: {failed}")

    return True, msgs
