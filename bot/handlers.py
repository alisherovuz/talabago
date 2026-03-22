from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import (
    main_menu_keyboard,
    paper_type_keyboard,
    language_keyboard,
    back_keyboard,
    confirm_keyboard,
    payment_keyboard,
    admin_keyboard,
    payment_confirm_keyboard,
    course_keyboard,
    skip_keyboard,
    broadcast_confirm_keyboard,
    sample_keyboard,
    doc_confirm_keyboard
)
from config.settings import settings
from services.ai_service import ai_service
from services.docx_service import docx_service
from services.db_service import db_service

router = Router()

# Narxlar
PRICES = {
    "referat": 7000,
    "kurs": 15000,
}

TYPE_NAMES = {
    "referat": "Referat",
    "kurs": "Kurs ishi",
}

# Coming soon
COMING_SOON = ["diplom", "prezentatsiya"]

LANG_NAMES = {
    "uz": "O'zbekcha",
    "ru": "Ruscha"
}


class RegistrationState(StatesGroup):
    entering_name = State()
    choosing_course = State()
    entering_university = State()


class OrderState(StatesGroup):
    choosing_type = State()
    entering_topic = State()
    choosing_language = State()
    confirming = State()
    waiting_payment = State()
    generating = State()


class BroadcastState(StatesGroup):
    entering_message = State()
    confirming = State()


class AdminState(StatesGroup):
    replacing_file = State()


# ==================== /start — REGISTRATION ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # User ni DB ga qo'shish
    user = await db_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Tekshirish — ro'yxatdan o'tganmi?
    is_registered = await db_service.is_user_registered(message.from_user.id)
    
    if not is_registered:
        # Ro'yxatdan o'tish kerak
        await state.set_state(RegistrationState.entering_name)
        await message.answer(
            "🎓 <b>TalabaGo</b> ga xush kelibsiz!\n\n"
            "Avval ro'yxatdan o'ting.\n\n"
            "👤 <b>Ism-familiyangizni kiriting:</b>\n\n"
            "<i>Misol: Aliyev Jasur</i>"
        )
    else:
        # Asosiy menyu
        await show_main_menu(message)


async def show_main_menu(message: Message):
    welcome_text = """
🎓 <b>TalabaGo</b> ga xush kelibsiz!

Men sizga ilmiy ishlar yozishda yordam beraman:
📝 Referat — 7,000 so'm
📚 Kurs ishi — 15,000 so'm
🎓 Diplom ishi — Tez kunda
📊 Prezentatsiya — Tez kunda

Tez, sifatli va arzon! 🚀
"""
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())


# ==================== REGISTRATION FLOW ====================

@router.message(RegistrationState.entering_name)
async def reg_enter_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 3:
        await message.answer("⚠️ Ism juda qisqa. Iltimos, to'liq ism-familiya kiriting.")
        return
    
    if len(name) > 100:
        await message.answer("⚠️ Ism juda uzun. 100 ta belgidan oshmasin.")
        return
    
    await state.update_data(full_name=name)
    await state.set_state(RegistrationState.choosing_course)
    
    await message.answer(
        f"✅ Rahmat, <b>{name}</b>!\n\n"
        f"📚 <b>Nechanchi kursda o'qiysiz?</b>",
        reply_markup=course_keyboard()
    )


@router.callback_query(F.data.startswith("course_"))
async def reg_choose_course(callback: CallbackQuery, state: FSMContext):
    course = int(callback.data.replace("course_", ""))
    await state.update_data(course=course)
    await state.set_state(RegistrationState.entering_university)
    
    await callback.message.edit_text(
        f"✅ {course}-kurs tanlandi!\n\n"
        f"🏫 <b>Universitet nomini kiriting:</b>\n\n"
        f"<i>Misol: TATU, O'zMU, TDYU</i>",
        reply_markup=skip_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "skip_university")
async def reg_skip_university(callback: CallbackQuery, state: FSMContext):
    await state.update_data(university="Korsatilmagan")
    await complete_registration(callback.message, state, callback.from_user.id)
    await callback.answer()


@router.message(RegistrationState.entering_university)
async def reg_enter_university(message: Message, state: FSMContext):
    university = message.text.strip()
    
    if len(university) < 2:
        await message.answer("⚠️ Universitet nomi juda qisqa.", reply_markup=skip_keyboard())
        return
    
    await state.update_data(university=university)
    await complete_registration(message, state, message.from_user.id)


async def complete_registration(message: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    uni = data.get('university', "Korsatilmagan")
    
    # DB ga saqlash
    await db_service.complete_registration(
        telegram_id=user_id,
        full_name=data['full_name'],
        university=uni,
        course=data['course']
    )
    
    await state.clear()
    
    await message.answer(
        f"🎉 <b>Royxatdan otdingiz!</b>\n\n"
        f"👤 Ism: {data['full_name']}\n"
        f"📚 Kurs: {data['course']}\n"
        f"🏫 Universitet: {uni}\n\n"
        f"Endi xizmatlarimizdan foydalanishingiz mumkin! 🚀",
        reply_markup=main_menu_keyboard()
    )


# ==================== ADMIN PANEL ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    
    stats = await db_service.get_admin_stats()
    
    admin_text = f"""
📊 <b>Admin Panel</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {stats['total_users']}
└ Bugun: {stats['today_users']}

📦 <b>Buyurtmalar:</b>
├ Jami: {stats['total_orders']}
├ Bugun: {stats['today_orders']}
├ Kutilmoqda: {stats['pending_orders']}
└ Bajarildi: {stats['completed_orders']}

💰 <b>Daromad:</b>
├ Jami: {stats['total_revenue']:,} so'm
└ Bugun: {stats['today_revenue']:,} so'm
"""
    await message.answer(admin_text, reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_users")
async def admin_users_list(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    users = await db_service.get_recent_users(limit=20)
    
    if not users:
        await callback.message.edit_text("👥 Hali foydalanuvchilar yo'q.", reply_markup=admin_keyboard())
        return
    
    text = "👥 <b>Oxirgi 20 foydalanuvchi:</b>\n\n"
    for i, user in enumerate(users, 1):
        username = f"@{user.username}" if user.username else "—"
        name = user.full_name or "Nomsiz"
        uni = user.university or "—"
        course = f"{user.course}-kurs" if user.course else "—"
        reg = "✅" if user.is_registered else "❌"
        text += f"{i}. {reg} {name}\n    {username} | {course} | {uni}\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    orders = await db_service.get_recent_orders(limit=20)
    
    if not orders:
        await callback.message.edit_text("📦 Hali buyurtmalar yo'q.", reply_markup=admin_keyboard())
        return
    
    text = "📦 <b>Oxirgi 20 buyurtma:</b>\n\n"
    for i, order in enumerate(orders, 1):
        status_emoji = {"pending": "🟡", "paid": "🔵", "processing": "🟠", "completed": "🟢", "rejected": "🔴"}
        emoji = status_emoji.get(order.status.value, "⚪")
        date = order.created_at.strftime("%d.%m.%Y %H:%M")
        topic_short = order.topic[:40] + "..." if len(order.topic) > 40 else order.topic
        text += f"{i}. {emoji} {TYPE_NAMES.get(order.paper_type.value, '?')}\n"
        text += f"    💰 {order.price:,} so'm | 📅 {date}\n"
        text += f"    📝 {topic_short}\n\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_refresh")
async def admin_refresh(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    stats = await db_service.get_admin_stats()
    from datetime import datetime
    
    admin_text = f"""
📊 <b>Admin Panel</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {stats['total_users']}
└ Bugun: {stats['today_users']}

📦 <b>Buyurtmalar:</b>
├ Jami: {stats['total_orders']}
├ Bugun: {stats['today_orders']}
├ Kutilmoqda: {stats['pending_orders']}
└ Bajarildi: {stats['completed_orders']}

💰 <b>Daromad:</b>
├ Jami: {stats['total_revenue']:,} so'm
└ Bugun: {stats['today_revenue']:,} so'm

🔄 Yangilandi: {datetime.now().strftime('%H:%M:%S')}
"""
    await callback.message.edit_text(admin_text, reply_markup=admin_keyboard())
    await callback.answer("✅ Yangilandi!")


# ==================== BROADCAST ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    await state.set_state(BroadcastState.entering_message)
    await callback.message.edit_text(
        "📢 <b>Broadcast</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n\n"
        "<i>Rasm, video, matn — har qanday kontent yuborishingiz mumkin.</i>",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.message(BroadcastState.entering_message)
async def admin_broadcast_preview(message: Message, state: FSMContext):
    if message.from_user.id != settings.ADMIN_ID:
        return
    
    # Xabar turini aniqlash
    if message.photo:
        await state.update_data(
            msg_type="photo",
            file_id=message.photo[-1].file_id,
            caption=message.caption or ""
        )
    elif message.video:
        await state.update_data(
            msg_type="video",
            file_id=message.video.file_id,
            caption=message.caption or ""
        )
    elif message.document:
        await state.update_data(
            msg_type="document",
            file_id=message.document.file_id,
            caption=message.caption or ""
        )
    else:
        await state.update_data(
            msg_type="text",
            text=message.text
        )
    
    # User sonini olish
    user_ids = await db_service.get_all_user_ids()
    user_count = len(user_ids)
    
    await state.set_state(BroadcastState.confirming)
    
    await message.answer(
        f"📢 <b>Xabar tayyor!</b>\n\n"
        f"👥 Yuboriladi: <b>{user_count}</b> ta foydalanuvchiga\n\n"
        f"✅ Yuborishni tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast_confirm")
async def admin_broadcast_send(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    data = await state.get_data()
    user_ids = await db_service.get_all_user_ids()
    
    await callback.message.edit_text("📤 <b>Yuborilmoqda...</b>")
    
    success = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            if data['msg_type'] == "photo":
                await callback.bot.send_photo(
                    chat_id=user_id,
                    photo=data['file_id'],
                    caption=data.get('caption', '')
                )
            elif data['msg_type'] == "video":
                await callback.bot.send_video(
                    chat_id=user_id,
                    video=data['file_id'],
                    caption=data.get('caption', '')
                )
            elif data['msg_type'] == "document":
                await callback.bot.send_document(
                    chat_id=user_id,
                    document=data['file_id'],
                    caption=data.get('caption', '')
                )
            else:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=data['text']
                )
            success += 1
        except Exception:
            failed += 1
        
        # Rate limit uchun
        import asyncio
        await asyncio.sleep(0.05)
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📤 Yuborildi: {success}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.", reply_markup=admin_keyboard())
    await callback.answer()


# ==================== ORDER FLOW ====================

@router.callback_query(F.data == "new_order")
async def new_order(callback: CallbackQuery, state: FSMContext):
    # Ro'yxatdan o'tganmi tekshirish
    is_registered = await db_service.is_user_registered(callback.from_user.id)
    if not is_registered:
        await callback.message.edit_text(
            "⚠️ Avval ro'yxatdan o'ting!\n\n/start buyrug'ini bosing.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(OrderState.choosing_type)
    await callback.message.edit_text("📋 <b>Ish turini tanlang:</b>", reply_markup=paper_type_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    paper_type = callback.data.replace("type_", "")
    
    # Coming soon check
    if paper_type == "coming_soon":
        await callback.answer("🔜 Bu xizmat tez kunda ishga tushadi!", show_alert=True)
        return
    
    # Check if paper type is valid
    if paper_type not in PRICES:
        await callback.answer("⚠️ Noto'g'ri tanlov", show_alert=True)
        return
    
    await state.update_data(paper_type=paper_type)
    await state.set_state(OrderState.entering_topic)
    
    await callback.message.edit_text(
        f"📝 <b>{TYPE_NAMES[paper_type]}</b> tanlandi\n"
        f"💰 Narxi: {PRICES[paper_type]:,} so'm\n\n"
        f"Endi <b>mavzuni</b> yozing:\n\n"
        f"<i>Misol: O'zbekistonda turizm sanoatining rivojlanishi</i>",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.message(OrderState.entering_topic)
async def enter_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    
    if len(topic) < 10:
        await message.answer("⚠️ Mavzu juda qisqa. Iltimos, to'liqroq yozing.", reply_markup=back_keyboard())
        return
    
    if len(topic) > 500:
        await message.answer("⚠️ Mavzu juda uzun. 500 ta belgidan oshmasin.", reply_markup=back_keyboard())
        return
    
    await state.update_data(topic=topic)
    await state.set_state(OrderState.choosing_language)
    await message.answer(f"✅ Mavzu qabul qilindi:\n<i>{topic}</i>\n\n🌐 <b>Tilni tanlang:</b>", reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    language = callback.data.replace("lang_", "")
    await state.update_data(language=language)
    
    data = await state.get_data()
    paper_type = data['paper_type']
    
    confirm_text = f"""
📋 <b>Buyurtmangiz:</b>

📝 Tur: {TYPE_NAMES[paper_type]}
📖 Mavzu: {data['topic']}
🌐 Til: {LANG_NAMES[language]}
💰 Narx: {PRICES[paper_type]:,} so'm

✅ Tasdiqlaysizmi?
"""
    await callback.message.edit_text(confirm_text, reply_markup=confirm_keyboard())
    await state.set_state(OrderState.confirming)
    await callback.answer()


@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    paper_type = data['paper_type']
    price = PRICES[paper_type]
    
    order = await db_service.create_order(
        telegram_id=callback.from_user.id,
        topic=data['topic'],
        paper_type=paper_type,
        language=data['language'],
        price=price
    )
    
    await state.update_data(order_id=order.id)
    await state.set_state(OrderState.waiting_payment)
    
    payment_text = f"""
💳 <b>To'lov</b>

📦 Buyurtma #{order.id}
💰 Summa: {price:,} so'm

💳 Karta: <code>9860 1766 1838 6914</code>
👤 Egasi: NURBEK ALISHEROV

To'lovni amalga oshiring va <b>screenshot</b> yuboring.
"""
    await callback.message.edit_text(payment_text, reply_markup=payment_keyboard())
    await callback.answer()


@router.message(OrderState.waiting_payment)
async def receive_payment_proof(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("📸 Iltimos, to'lov <b>screenshotini</b> yuboring.", reply_markup=payment_keyboard())
        return
    
    data = await state.get_data()
    order_id = data.get('order_id')
    
    admin_text = f"""
🆕 <b>Yangi to'lov!</b>

📦 Buyurtma #{order_id}
👤 User: {message.from_user.full_name} (@{message.from_user.username or 'username_yoq'})
🆔 ID: {message.from_user.id}

📝 Tur: {TYPE_NAMES[data['paper_type']]}
📖 Mavzu: {data['topic']}
💰 Summa: {PRICES[data['paper_type']]:,} so'm
"""
    
    await message.bot.send_photo(
        chat_id=settings.ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=admin_text,
        reply_markup=payment_confirm_keyboard(order_id, message.from_user.id)
    )
    
    await message.answer(
        "✅ To'lov qabul qilindi!\n\n⏳ Admin tekshirib, ishingizni tayyorlaydi.\nTayyor bo'lgach xabar beramiz.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


# ==================== PAYMENT CONFIRMATION ====================

@router.callback_query(F.data.startswith("pay_ok_"))
async def admin_approve_payment(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    await db_service.update_order_status(order_id, "paid")
    
    # Userga xabar
    progress_msg = await callback.bot.send_message(
        chat_id=user_id,
        text="🔄 <b>Ishlanmoqda...</b>\n\n⏳ AI yozmoqda...\n⬜ DOCX tayyorlanmoqda..."
    )
    
    # Adminga xabar
    admin_progress = await callback.message.reply("⏳ AI ishlamoqda...")
    
    order = await db_service.get_order_by_id(order_id)
    await db_service.update_order_status(order_id, "processing")
    
    try:
        content = await ai_service.generate_paper(
            topic=order.topic,
            paper_type=order.paper_type.value,
            language=order.language
        )
        
        await progress_msg.edit_text("🔄 <b>Ishlanmoqda...</b>\n\n✅ AI yozdi\n⏳ DOCX tayyorlanmoqda...")
        
        file_path = await docx_service.create_document(
            content=content,
            topic=order.topic,
            paper_type=order.paper_type.value
        )
        
        word_count = len(content.split())
        page_count = word_count // 250 + 1
        
        await db_service.complete_order(order_id, word_count, page_count)
        
        await progress_msg.edit_text("🔄 <b>Ishlanmoqda...</b>\n\n✅ AI yozdi\n✅ DOCX tayyor\n⏳ Admin tekshirmoqda...")
        
        # Adminga fayl yuborish (tekshirish uchun)
        doc_file = FSInputFile(file_path)
        await admin_progress.delete()
        
        await callback.bot.send_document(
            chat_id=settings.ADMIN_ID,
            document=doc_file,
            caption=f"📄 <b>Tekshirish uchun:</b>\n\n"
                    f"🆔 Buyurtma: #{order_id}\n"
                    f"👤 User ID: {user_id}\n"
                    f"📝 {TYPE_NAMES.get(order.paper_type.value, '?')}\n"
                    f"📖 {order.topic[:50]}...\n"
                    f"📄 {page_count} bet | {word_count} so'z\n\n"
                    f"✅ Userga yuborish yoki 🔄 Yangi fayl yuklash",
            reply_markup=doc_confirm_keyboard(order_id, user_id)
        )
        
        await callback.message.edit_caption(callback.message.caption + "\n\n⏳ <b>AI tayyor, tekshirish kutilmoqda...</b>")
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ Xatolik yuz berdi. Admin hal qiladi.")
        await callback.message.edit_caption(callback.message.caption + f"\n\n❌ <b>XATOLIK:</b> {str(e)}")
    
    await callback.answer("✅ AI tayyor! Tekshiring.")


@router.callback_query(F.data.startswith("pay_no_"))
async def admin_reject_payment(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    await db_service.update_order_status(order_id, "rejected")
    
    await callback.bot.send_message(
        chat_id=user_id,
        text="❌ <b>To'lov tasdiqlanmadi</b>\n\nIltimos, to'lov ma'lumotlarini tekshiring.\nMuammo bo'lsa: @TalabaGo_support",
        reply_markup=main_menu_keyboard()
    )
    
    await callback.message.edit_caption(callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>")
    await callback.answer("❌ Rad etildi")


# ==================== DOCUMENT CONFIRMATION ====================

@router.callback_query(F.data.startswith("doc_ok_"))
async def admin_send_to_user(callback: CallbackQuery):
    """Admin approves document and sends to user."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    order = await db_service.get_order_by_id(order_id)
    
    # Get the document from this message
    document = callback.message.document
    
    if document:
        await callback.bot.send_document(
            chat_id=user_id,
            document=document.file_id,
            caption=f"🎉 <b>Tayyor!</b>\n\n"
                    f"📝 {TYPE_NAMES.get(order.paper_type.value, '?')}\n"
                    f"📖 {order.topic[:50]}...\n"
                    f"📄 {order.page_count} bet | {order.word_count} so'z\n\n"
                    f"Rahmat! TalabaGo bilan! 🚀"
        )
        
        await callback.message.edit_caption(
            callback.message.caption + "\n\n✅ <b>USERGA YUBORILDI!</b>"
        )
        await callback.answer("✅ Userga yuborildi!")
    else:
        await callback.answer("❌ Fayl topilmadi", show_alert=True)


@router.callback_query(F.data.startswith("doc_replace_"))
async def admin_replace_file(callback: CallbackQuery, state: FSMContext):
    """Admin wants to replace the document."""
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    await state.set_state(AdminState.replacing_file)
    await state.update_data(replace_order_id=order_id, replace_user_id=user_id)
    
    await callback.message.reply(
        "📤 <b>Yangi faylni yuboring</b>\n\n"
        f"🆔 Buyurtma: #{order_id}\n"
        f"👤 User ID: {user_id}\n\n"
        "⚠️ Faqat .docx fayl yuboring!"
    )
    await callback.answer()


@router.message(AdminState.replacing_file, F.document)
async def receive_replacement_file(message: Message, state: FSMContext):
    """Receive replacement file from admin."""
    if message.from_user.id != settings.ADMIN_ID:
        return
    
    data = await state.get_data()
    order_id = data.get('replace_order_id')
    user_id = data.get('replace_user_id')
    
    if not order_id or not user_id:
        await message.answer("❌ Xatolik. Qaytadan urinib ko'ring.")
        await state.clear()
        return
    
    order = await db_service.get_order_by_id(order_id)
    
    # Send to user
    await message.bot.send_document(
        chat_id=user_id,
        document=message.document.file_id,
        caption=f"🎉 <b>Tayyor!</b>\n\n"
                f"📝 {TYPE_NAMES.get(order.paper_type.value, '?')}\n"
                f"📖 {order.topic[:50]}...\n\n"
                f"Rahmat! TalabaGo bilan! 🚀"
    )
    
    await message.answer(
        f"✅ <b>Yangi fayl userga yuborildi!</b>\n\n"
        f"🆔 Buyurtma: #{order_id}\n"
        f"👤 User ID: {user_id}"
    )
    await state.clear()


# ==================== NAVIGATION ====================

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = """
🎓 <b>TalabaGo</b> ga xush kelibsiz!

Men sizga ilmiy ishlar yozishda yordam beraman:
📝 Referat — 7,000 so'm
📚 Kurs ishi — 15,000 so'm
🎓 Diplom ishi — Tez kunda
📊 Prezentatsiya — Tez kunda

Tez, sifatli va arzon! 🚀
"""
    await callback.message.edit_text(welcome_text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    orders = await db_service.get_user_orders(callback.from_user.id)
    
    if not orders:
        await callback.message.edit_text("📭 Sizda hali buyurtmalar yo'q.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    
    text = "📦 <b>Sizning buyurtmalaringiz:</b>\n\n"
    for order in orders[:10]:
        status_emoji = {"pending": "🟡", "paid": "🔵", "processing": "🟠", "completed": "🟢", "rejected": "🔴"}
        emoji = status_emoji.get(order.status.value, "⚪")
        text += f"#{order.id} | {TYPE_NAMES.get(order.paper_type.value, '?')} | {emoji}\n"
        text += f"📝 {order.topic[:35]}...\n💰 {order.price:,} so'm\n\n"
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    help_text = """
❓ <b>Yordam</b>

<b>Qanday ishlaydi?</b>
1️⃣ Ish turini tanlang
2️⃣ Mavzuni yozing
3️⃣ Tilni tanlang
4️⃣ To'lang va yuklab oling

<b>Narxlar:</b>
📝 Referat — 7,000 so'm
📚 Kurs ishi — 15,000 so'm
🎓 Diplom — Tez kunda
📊 Prezentatsiya — Tez kunda

<b>Aloqa:</b> @TalabaGo_support
"""
    await callback.message.edit_text(help_text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "show_sample")
async def show_sample(callback: CallbackQuery):
    sample_text = """
📋 <b>Namuna</b>

Quyida AI tomonidan yozilgan referat namunasini ko'rishingiz mumkin.

📝 <b>Mavzu:</b> O'zbekistonda turizm sanoatining rivojlanishi
📄 <b>Hajm:</b> 12 bet
🌐 <b>Til:</b> O'zbekcha

⬇️ Yuklash uchun pastdagi tugmani bosing.
"""
    await callback.message.edit_text(sample_text, reply_markup=sample_keyboard())
    await callback.answer()


@router.callback_query(F.data == "download_sample")
async def download_sample(callback: CallbackQuery):
    await callback.answer("⏳ Namuna yuklanmoqda...", show_alert=False)
    
    # Namuna fayl yuborish
    sample_url = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
    
    await callback.message.answer(
        "📄 <b>Namuna referat</b>\n\n"
        "Mavzu: O'zbekistonda turizm sanoatining rivojlanishi\n\n"
        "⚠️ Bu AI tomonidan yozilgan namuna. Siz ham shunday sifatli ish olishingiz mumkin!\n\n"
        "👉 Buyurtma berish uchun /start bosing",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_keyboard())
    await callback.answer()
