from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Yangi buyurtma", callback_data="new_order")],
        [InlineKeyboardButton(text="📋 Namuna ko'rish", callback_data="show_sample")],
        [InlineKeyboardButton(text="📦 Mening buyurtmalarim", callback_data="my_orders")],
        [InlineKeyboardButton(text="❓ Yordam", callback_data="help")]
    ])


def paper_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Referat — 7,000 so'm", callback_data="type_referat")],
        [InlineKeyboardButton(text="📚 Kurs ishi — 15,000 so'm", callback_data="type_kurs")],
        [InlineKeyboardButton(text="🎓 Diplom ishi — Tez kunda", callback_data="type_coming_soon")],
        [InlineKeyboardButton(text="📊 Prezentatsiya — Tez kunda", callback_data="type_coming_soon")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])


def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="lang_ru")
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])


def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])


def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")]
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])


# ==================== ADMIN KEYBOARDS ====================

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Userlar", callback_data="admin_users"),
            InlineKeyboardButton(text="📦 Buyurtmalar", callback_data="admin_orders")
        ],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_refresh")]
    ])


def payment_confirm_keyboard(order_id: int, user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_ok_{order_id}_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pay_no_{order_id}_{user_id}")
        ]
    ])


# ==================== REGISTRATION KEYBOARDS ====================

def course_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣ 1-kurs", callback_data="course_1"),
            InlineKeyboardButton(text="2️⃣ 2-kurs", callback_data="course_2")
        ],
        [
            InlineKeyboardButton(text="3️⃣ 3-kurs", callback_data="course_3"),
            InlineKeyboardButton(text="4️⃣ 4-kurs", callback_data="course_4")
        ],
        [
            InlineKeyboardButton(text="5️⃣ Magistr 1", callback_data="course_5"),
            InlineKeyboardButton(text="6️⃣ Magistr 2", callback_data="course_6")
        ]
    ])


def skip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_university")]
    ])


# ==================== BROADCAST KEYBOARDS ====================

def broadcast_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")
        ]
    ])


def sample_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Namunani yuklash", callback_data="download_sample")],
        [InlineKeyboardButton(text="📝 Buyurtma berish", callback_data="new_order")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ])


def doc_confirm_keyboard(order_id: int, user_id: int):
    """Admin approves or replaces the generated document."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Userga yuborish", callback_data=f"doc_ok_{order_id}_{user_id}"),
            InlineKeyboardButton(text="🔄 Fayl almashtirish", callback_data=f"doc_replace_{order_id}_{user_id}")
        ]
    ])
