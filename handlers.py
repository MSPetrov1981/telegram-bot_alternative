import json
import logging
import os
import re
from email.message import EmailMessage

import aiofiles
import aiofiles.os as aiofiles_os
from aiosmtplib import SMTP
from telegram import InputMediaPhoto, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import BadRequest
from telegram.ext import ConversationHandler, ContextTypes

from keyboards import (
    diagnostic_description_keyboard, diagnostic_detail_keyboard, diagnostics_keyboard,
    direction_description_keyboard, direction_detail_keyboard, direction_detailed_description_keyboard,
    directions_keyboard, doctor_detail_keyboard, extended_survey_keyboard,
    health_program_description_keyboard, health_program_detail_keyboard, health_programs_keyboard,
    initial_survey_keyboard, main_menu_keyboard, procedure_detail_keyboard,
    service_doctor_description_keyboard, service_doctor_detail_keyboard, service_procedures_keyboard,
    service_specialists_keyboard, service_specializations_keyboard, services_keyboard,
    specialists_keyboard, treatment_description_keyboard, treatment_detail_keyboard,
    what_we_treat_keyboard, dates_calendar_keyboard
)

# 1. Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 2. Состояния для формы записи
AWAITING_NAME, AWAITING_PHONE, AWAITING_SERVICE, AWAITING_COMMENT = range(100, 104)

# 3. Очистка JSON от мусорных пробелов (критично для вашего data.json)
def _strip_data(obj):
    if isinstance(obj, dict):
        return {k.strip(): _strip_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_strip_data(i) for i in obj]
    elif isinstance(obj, str):
        return obj.strip()
    return obj

# 4. Загрузка данных
try:
    with open("data.json", encoding="utf-8") as f:
        DATA = _strip_data(json.load(f))
except FileNotFoundError:
    raise RuntimeError("Файл data.json не найден в директории с ботом.")

# 5. Вспомогательные функции
def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Отмена записи")]],
        resize_keyboard=True, one_time_keyboard=True
    )

async def _send_inline_media_or_text(query, text: str, keyboard: ReplyKeyboardMarkup, photo_path: str | None = None) -> None:
    if photo_path and await aiofiles_os.path.exists(photo_path):
        async with aiofiles.open(photo_path, "rb") as ph:
            await query.message.reply_photo(photo=await ph.read(), caption=text, reply_markup=keyboard, parse_mode="Markdown")
        await query.message.delete()
    else:
        await query.edit_message_text(text + "\n\n📷 Фото не найдено", reply_markup=keyboard, parse_mode="Markdown")

def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if not re.match(r"^\+?\d+$", cleaned):
        return False
    return len(cleaned.replace("+", "")) >= 7

# ---------------------- ОСНОВНЫЕ ОБРАБОТЧИКИ ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot.")
    await update.message.reply_text(DATA["start_message"])

    media_group = []
    for img in DATA["clinic_images"]:
        if await aiofiles_os.path.exists(img):
            async with aiofiles.open(img, "rb") as ph:
                photo_bytes = await ph.read()
                media_group.append(
                    InputMediaPhoto(media=photo_bytes, caption="Альтернативная клиника")
                    if not media_group else InputMediaPhoto(media=photo_bytes)
                )

    if media_group:
        await update.message.reply_media_group(media=media_group)

    await update.message.reply_text(DATA["contact_numbers"])
    context.user_data["survey_state"] = "waiting"
    await update.message.reply_text(
        'Если вы о нас знаете, нажмите "Да".\n'
        'Если не знаете, нажмите "Нет".\n'
        'Для остановки бота нажмите "стоп".',
        reply_markup=initial_survey_keyboard()
    )

async def handle_survey_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("appointment_step") is not None:
        return
    if context.user_data.get("survey_state") != "waiting":
        return

    text = update.message.text.strip().lower()
    context.user_data["survey_state"] = None
    logger.info(f"Survey response: {text}")

    if text == "стоп":
        await update.message.reply_text("Вы отписались.", reply_markup=ReplyKeyboardRemove())
    elif text == "да":
        await update.message.reply_text("Рады знакомству! Выберите пункт.", reply_markup=main_menu_keyboard())
    elif text == "нет":
        context.user_data["from_extended_menu"] = True
        await update.message.reply_text("Давайте знакомиться!", reply_markup=extended_survey_keyboard())
    else:
        context.user_data["survey_state"] = "waiting"
        await update.message.reply_text('Ответьте «Да», «Нет» или «стоп».', reply_markup=initial_survey_keyboard())

# ---------------------- КОМАНДЫ МЕНЮ ----------------------
def _get_menu_kb(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    return extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()

async def website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Наш сайт: https://alternative-clinic.ru", reply_markup=_get_menu_kb(context))

async def specialists_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(DATA["specialists"]["title"], reply_markup=specialists_keyboard())

async def services_main(update: Update, _) -> None:
    await update.message.reply_text(DATA["services"]["title"], reply_markup=services_keyboard())

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(DATA["contacts"], reply_markup=_get_menu_kb(context))

async def leave_review(update: Update, _) -> None:
    await update.message.reply_text("Напишите ваш отзыв в этом чате.")

async def main_menu_from_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("from_extended_menu", None)
    await update.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

async def cost_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Прайс-лист на сайте в разделе «Цены».", reply_markup=_get_menu_kb(context))

async def lectures_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Курсы и лекции в Telegram: @alternative_clinic", reply_markup=_get_menu_kb(context))

async def questions_consultation(update: Update, _) -> None:
    await update.message.reply_text("Вопросы по лечению: напишите нам в чат.")

async def directions_main(update: Update, _) -> None:
    await update.message.reply_text(DATA["directions"]["title"], reply_markup=directions_keyboard())

async def website_main(update: Update, _) -> None:
    await update.message.reply_text("Наш сайт: https://alternative-clinic.ru")

# ---------------------- ФОРМА ЗАПИСИ ----------------------
async def start_appointment_form(update: Update, context: ContextTypes.DEFAULT_TYPE, service_info: str | None = None) -> int:
    logger.info("Starting appointment form, service_info=%s", service_info)
    context.user_data.clear()
    context.user_data["appointment_step"] = AWAITING_NAME
    if service_info:
        context.user_data["service"] = service_info
        context.user_data["skip_service_step"] = True
    else:
        context.user_data["skip_service_step"] = False

    text = "Пожалуйста, введите ваши ФИО (Имя и Фамилию):"
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.message.photo:
            await query.message.delete()
            await query.message.chat.send_message(text, reply_markup=cancel_keyboard())
        else:
            try:
                await query.edit_message_text(text, reply_markup=cancel_keyboard())
            except BadRequest:
                await query.message.chat.send_message(text, reply_markup=cancel_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=cancel_keyboard())
    return AWAITING_NAME

async def appointment_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start_appointment_form(update, context)

async def button_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    if len(parts) < 2 or parts[0] != "appointment":
        await query.edit_message_text("Ошибка формата записи.")
        return ConversationHandler.END

    service_name = get_service_or_doctor_name(parts[1], "_".join(parts[2:]))
    return await start_appointment_form(update, context, service_info=service_name)

async def send_email_notification(name: str, phone: str, service: str, comment: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO", "s1digital@ya.ru")

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.error("Не настроены параметры SMTP в .env")
        return

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Subject"] = f"Новая заявка на запись от {name}"
    msg.set_content(f"Имя: {name}\nТелефон: {phone}\nУслуга/врач: {service}\nКомментарий: {comment or 'нет'}\n")

    try:
        async with SMTP(
            hostname=smtp_host, port=smtp_port,
            use_tls=(smtp_port == 465), start_tls=(smtp_port == 587)
        ) as smtp:
            await smtp.login(smtp_user, smtp_password)
            await smtp.send_message(msg)
        logger.info("Заявка отправлена на %s", email_to)
    except Exception as e:
        logger.exception("Ошибка отправки email: %s", e)

async def process_appointment_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    step = context.user_data.get("appointment_step")
    text = update.message.text.strip()
    logger.info(f"process_appointment_input: step={step}, text='{text[:50]}'")

    if text.lower() == "отмена записи":
        await cancel_appointment_form(update, context)
        return ConversationHandler.END

    if step is None:
        await handle_survey_global(update, context)
        return None

    if step == AWAITING_NAME:
        if len(text.split()) < 2:
            await update.message.reply_text("Пожалуйста, введите полные ФИО (Имя и Фамилию):", reply_markup=cancel_keyboard())
            return AWAITING_NAME
        context.user_data["full_name"] = text
        context.user_data["appointment_step"] = AWAITING_PHONE
        await update.message.reply_text("Введите ваш номер телефона (например, +7 123 456-78-90):", reply_markup=cancel_keyboard())
        return AWAITING_PHONE

    if step == AWAITING_PHONE:
        if not is_valid_phone(text):
            await update.message.reply_text("❌ Некорректный номер. Введите номер, состоящий из цифр, возможно с +, пробелами или дефисами.", reply_markup=cancel_keyboard())
            return AWAITING_PHONE
        context.user_data["phone"] = text
        next_step = AWAITING_COMMENT if context.user_data.get("skip_service_step") else AWAITING_SERVICE
        context.user_data["appointment_step"] = next_step
        prompt = "Если есть дополнительные пожелания или комментарий, напишите их здесь. Если нет, просто отправьте любой символ или слово «нет»:" if next_step == AWAITING_COMMENT else "Укажите, к какому врачу или на какую процедуру вы хотите записаться (например: «Терапевт» или «Массаж спины»):"
        await update.message.reply_text(prompt, reply_markup=cancel_keyboard())
        return next_step

    if step == AWAITING_SERVICE:
        if not text:
            await update.message.reply_text("Пожалуйста, укажите услугу или врача.", reply_markup=cancel_keyboard())
            return AWAITING_SERVICE
        context.user_data["service"] = text
        context.user_data["appointment_step"] = AWAITING_COMMENT
        await update.message.reply_text("Если есть дополнительные пожелания или комментарий, напишите их здесь. Если нет, просто отправьте любой символ или слово «нет»:", reply_markup=cancel_keyboard())
        return AWAITING_COMMENT

    if step == AWAITING_COMMENT:
        comment = "" if text.lower() in {"нет", "нету", "-", "—"} else text
        name = context.user_data["full_name"]
        phone = context.user_data["phone"]
        service = context.user_data["service"]

        await send_email_notification(name, phone, service, comment)
        await update.message.reply_text(
            f"✅ Спасибо, {name}!\nВаша заявка принята.\nУслуга/врач: {service}\nТелефон: {phone}\nКомментарий: {comment or 'нет'}\n\nАдминистратор свяжется с вами для подтверждения записи.",
            reply_markup=main_menu_keyboard(),
        )
        context.user_data.clear()
        return ConversationHandler.END
    return None

async def cancel_appointment_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("Заполнение формы отменено.", reply_markup=main_menu_keyboard())

# ---------------------- INLINE ОБРАБОТЧИКИ ----------------------
async def button_doctor(update: Update, _):
    query = update.callback_query
    await query.answer()
    doc_key = query.data.removeprefix("doctor_")
    doc = DATA["specialists"]["doctors"][doc_key]
    await _send_inline_media_or_text(query, f"{doc['name']}\nСпециализация: {doc['specialization']}", doctor_detail_keyboard(doc_key), doc.get("photo"))

async def button_service_specialists(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Выберите специализацию:", reply_markup=service_specializations_keyboard())

async def button_specialization(update: Update, _):
    query = update.callback_query
    await query.answer()
    spec_key = query.data.removeprefix("specialization_")
    spec = DATA["specializations"][spec_key]
    await query.edit_message_text(f"Выберите врача ({spec['title']}):", reply_markup=service_specialists_keyboard(spec_key))

async def button_service_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doc_key = query.data.removeprefix("service_doctor_")
    for spec_key, spec in DATA["specializations"].items():
        if doc_key in spec["doctors"]:
            context.user_data["current_specialization"] = spec_key
            doc = spec["doctors"][doc_key]
            await _send_inline_media_or_text(query, f"{doc['name']}\nСпециализация: {doc['specialization']}", service_doctor_detail_keyboard(doc_key, spec_key), doc.get("photo"))
            return

async def button_service_doctor_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doc_key = query.data.removeprefix("detail_service_doctor_")
    spec_key = context.user_data.get("current_specialization")
    if spec_key and doc_key in DATA["specializations"][spec_key]["doctors"]:
        doc = DATA["specializations"][spec_key]["doctors"][doc_key]
        await _send_inline_media_or_text(query, f"{doc['name']}\nСпециализация: {doc['specialization']}\n\n{doc['description']}", service_doctor_description_keyboard(doc_key, spec_key), doc.get("photo"))
    else:
        await query.edit_message_text("Врач не найден.")

async def button_service_procedures(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(DATA["procedures"]["title"], reply_markup=service_procedures_keyboard())

async def button_procedure(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("procedure_")
    await query.edit_message_text(f"Процедура: {DATA['procedures']['procedures_list'][key]['name']}", reply_markup=procedure_detail_keyboard(key))

async def button_direction(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("direction_")
    await query.edit_message_text(f"Направление: {DATA['directions']['directions_list'][key]['name']}", reply_markup=direction_detail_keyboard(key))

async def button_direction_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("detail_direction_")
    d = DATA["directions"]["directions_list"][key]
    await query.edit_message_text(f"{d['name']}\n\n{d['description']}", reply_markup=direction_description_keyboard(key), parse_mode="Markdown")

async def button_direction_more_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("more_detail_direction_")
    d = DATA["directions"]["directions_list"][key]
    await query.edit_message_text(f"{d['name']}\n\n{d['detailed_description']}", reply_markup=direction_detailed_description_keyboard(key), parse_mode="Markdown")

async def button_service_health_programs(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(DATA["health_programs"]["title"], reply_markup=health_programs_keyboard())

async def button_service_diagnostics(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(DATA["diagnostics"]["title"], reply_markup=diagnostics_keyboard())

async def button_diagnostic(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("diagnostic_")
    d = DATA["diagnostics"]["diagnostics_list"][key]
    await query.edit_message_text(f"{d['name']}\n\n{d['description']}", reply_markup=diagnostic_detail_keyboard(key), parse_mode="Markdown")

async def button_diagnostic_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("detail_diagnostic_")
    d = DATA["diagnostics"]["diagnostics_list"][key]
    await query.edit_message_text(f"{d['name']}\n\n{d['detailed_description']}", reply_markup=diagnostic_description_keyboard(key), parse_mode="Markdown")

async def button_service_what_we_treat(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(DATA["what_we_treat"]["title"], reply_markup=what_we_treat_keyboard())

async def button_treatment(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("treatment_")
    t = DATA["what_we_treat"]["treatments_list"][key]
    await query.edit_message_text(f"{t['name']}\n\n{t['description']}", reply_markup=treatment_detail_keyboard(key), parse_mode="Markdown")

async def button_treatment_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("detail_treatment_")
    t = DATA["what_we_treat"]["treatments_list"][key]
    await query.edit_message_text(f"{t['name']}\n\n{t['detailed_description']}", reply_markup=treatment_description_keyboard(key), parse_mode="Markdown")

async def button_health_program(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("health_program_")
    p = DATA["health_programs"]["programs_list"][key]
    await query.edit_message_text(f"{p['name']}\n\n{p['description']}", reply_markup=health_program_detail_keyboard(key), parse_mode="Markdown")

async def button_health_program_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    key = query.data.removeprefix("detail_health_program_")
    p = DATA["health_programs"]["programs_list"][key]
    await query.edit_message_text(f"{p['name']}\n\n{p['detailed_description']}", reply_markup=health_program_description_keyboard(key), parse_mode="Markdown")

# ---------------------- УТИЛИТЫ И НАВИГАЦИЯ ----------------------
def get_service_or_doctor_name(app_type: str, app_id: str) -> str:
    try:
        if app_type == "doctor":
            if app_id in DATA["specialists"]["doctors"]:
                d = DATA["specialists"]["doctors"][app_id]
                return f"{d['name']} ({d['specialization']})"
            for spec in DATA["specializations"].values():
                if app_id in spec["doctors"]:
                    d = spec["doctors"][app_id]
                    return f"{d['name']} ({d['specialization']})"
        elif app_type == "procedure":
            return DATA["procedures"]["procedures_list"][app_id]["name"]
        elif app_type == "direction":
            return DATA["directions"]["directions_list"][app_id]["name"]
        elif app_type == "health_program":
            return DATA["health_programs"]["programs_list"][app_id]["name"]
        elif app_type == "diagnostic":
            return DATA["diagnostics"]["diagnostics_list"][app_id]["name"]
        elif app_type == "treatment":
            return DATA["what_we_treat"]["treatments_list"][app_id]["name"]
    except KeyError:
        pass
    return "Неизвестная услуга"

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = main_menu_keyboard()
    if update.message:
        await update.message.reply_text(DATA["start_message"], reply_markup=kb)
    else:
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        await query.message.chat.send_message(DATA["start_message"], reply_markup=kb)

async def button_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    back_to = query.data.removeprefix("back_")

    if back_to in {"dates", "to_dates", "appointment"}:
        context.user_data["appointment_step"] = "awaiting_date"
        try:
            await query.edit_message_text("Выберите удобную дату:", reply_markup=dates_calendar_keyboard())
        except Exception:
            await main_menu_handler(update, context)
    else:
        await main_menu_handler(update, context)