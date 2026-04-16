import json
import logging
import os
import re
from email.message import EmailMessage

import aiofiles
import aiofiles.os as aiofiles_os
from aiosmtplib import SMTP
from telegram import (
    InputMediaPhoto,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import ConversationHandler

from keyboards import (
    diagnostic_description_keyboard,
    diagnostic_detail_keyboard,
    diagnostics_keyboard,
    direction_description_keyboard,
    direction_detail_keyboard,
    direction_detailed_description_keyboard,
    directions_keyboard,
    doctor_detail_keyboard,
    extended_survey_keyboard,
    health_program_description_keyboard,
    health_program_detail_keyboard,
    health_programs_keyboard,
    initial_survey_keyboard,
    main_menu_keyboard,
    procedure_detail_keyboard,
    service_doctor_description_keyboard,
    service_doctor_detail_keyboard,
    service_procedures_keyboard,
    service_specialists_keyboard,
    service_specializations_keyboard,
    services_keyboard,
    specialists_keyboard,
    treatment_description_keyboard,
    treatment_detail_keyboard,
    what_we_treat_keyboard,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для формы записи
AWAITING_NAME, AWAITING_PHONE, AWAITING_SERVICE, AWAITING_COMMENT = range(100, 104)

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

SURVEY_STATE = {}


# Клавиатура с кнопкой "Отмена"
def cancel_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("Отмена записи")]], resize_keyboard=True, one_time_keyboard=True)


# ---------------------- ОСНОВНЫЕ ОБРАБОТЧИКИ ----------------------
async def start(update: Update, _context):
    logger.info(f"User {update.effective_user.id} started the bot.")
    welcome_text = data["start_message"]
    clinic_images = data["clinic_images"]
    contact_numbers = data["contact_numbers"]

    await update.message.reply_text(welcome_text)

    media_group = []
    for img in clinic_images:
        if await aiofiles_os.path.exists(img):
            async with aiofiles.open(img, "rb") as ph:
                photo_bytes = await ph.read()
                if not media_group:
                    media_group.append(InputMediaPhoto(media=photo_bytes, caption="Альтернативная клиника"))
                else:
                    media_group.append(InputMediaPhoto(media=photo_bytes))

    if media_group:
        await update.message.reply_media_group(media=media_group)

    await update.message.reply_text(contact_numbers)

    SURVEY_STATE[update.effective_chat.id] = "waiting"
    await update.message.reply_text(
        'Если вы о нас знаете, нажмите "Да".\n'
        'Если не знаете, нажмите "Нет".\n'
        'Для остановки бота нажмите "стоп".',
        reply_markup=initial_survey_keyboard()
    )


async def handle_survey_global(update: Update, context):
    chat_id = update.effective_chat.id
    if context.user_data.get("appointment_step") is not None:
        return
    if SURVEY_STATE.get(chat_id) != "waiting":
        return
    text = update.message.text.strip().lower()
    SURVEY_STATE[chat_id] = None
    logger.info("Survey response: %s", text)
    if text == "стоп":
        await update.message.reply_text("Вы отписались.", reply_markup=ReplyKeyboardRemove())
    elif text == "да":
        await update.message.reply_text("Рады знакомству! Выберите пункт.", reply_markup=main_menu_keyboard())
    elif text == "нет":
        context.user_data["from_extended_menu"] = True
        await update.message.reply_text("Давайте знакомиться!", reply_markup=extended_survey_keyboard())
    else:
        SURVEY_STATE[chat_id] = "waiting"
        await update.message.reply_text("Ответьте «Да», «Нет» или «стоп».", reply_markup=initial_survey_keyboard())


# ---------------------- КОМАНДЫ МЕНЮ ----------------------
async def website(update: Update, context):
    text = "Наш сайт: https://alternative-clinic.ru"
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def specialists_main(update: Update, context):
    text = data["specialists"]["title"]
    kb = specialists_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def services_main(update: Update, _):
    await update.message.reply_text(data["services"]["title"], reply_markup=services_keyboard())


async def contacts(update: Update, context):
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text(data["contacts"], reply_markup=kb)


async def leave_review(update: Update, _):
    await update.message.reply_text("Напишите ваш отзыв в этом чате.")


async def main_menu_from_survey(update: Update, context):
    context.user_data.pop("from_extended_menu", None)
    await update.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())


async def cost_services(update: Update, context):
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text("Прайс-лист на сайте в разделе «Цены».", reply_markup=kb)


async def lectures_courses(update: Update, context):
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text("Курсы и лекции в Telegram: @alternative_clinic", reply_markup=kb)


async def questions_consultation(update: Update, _):
    await update.message.reply_text("Вопросы по лечению: напишите нам в чат.")


async def directions_main(update: Update, _):
    await update.message.reply_text(data["directions"]["title"], reply_markup=directions_keyboard())


async def website_main(update: Update, _):
    await update.message.reply_text("Наш сайт: https://alternative-clinic.ru")


# ---------------------- ФОРМА ЗАПИСИ ----------------------
async def start_appointment_form(update: Update, context, service_info: str | None = None):
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


async def appointment_request(update: Update, context):
    await start_appointment_form(update, context)
    return AWAITING_NAME


async def button_appointment(update: Update, context):
    query = update.callback_query
    parts = query.data.split("_")
    if len(parts) < 2 or parts[0] != "appointment":
        await query.edit_message_text("Ошибка формата записи.")
        return ConversationHandler.END

    appointment_type = parts[1]
    appointment_id = "_".join(parts[2:])
    service_name = get_service_or_doctor_name(appointment_type, appointment_id)

    await start_appointment_form(update, context, service_info=service_name)
    return AWAITING_NAME


def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if not re.match(r"^\+?\d+$", cleaned):
        return False
    digits = re.sub(r"\D", "", cleaned)
    return len(digits) >= 7


async def send_email_notification(name: str, phone: str, service: str, comment: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO", "s1digital@ya.ru")

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.error("Не настроены параметры SMTP в .env")
        return

    subject = f"Новая заявка на запись от {name}"
    body = (
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Услуга/врач: {service}\n"
        f"Комментарий: {comment if comment else 'нет'}\n"
    )
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if smtp_port == 587:
            async with SMTP(hostname=smtp_host, port=smtp_port, start_tls=True) as smtp:
                await smtp.login(smtp_user, smtp_password)
                await smtp.send_message(msg)
        elif smtp_port == 465:
            async with SMTP(hostname=smtp_host, port=smtp_port, use_tls=True) as smtp:
                await smtp.login(smtp_user, smtp_password)
                await smtp.send_message(msg)
        else:
            logger.error("Неподдерживаемый порт: %s", smtp_port)
            return
        logger.info("Заявка отправлена на %s", email_to)
    except Exception as e:
        logger.exception("Ошибка отправки email: %s", e)


async def process_appointment_input(update: Update, context):
    step = context.user_data.get("appointment_step")
    text = update.message.text.strip()
    logger.info(f"process_appointment_input: step={step}, text='{text[:50]}'")

    # Проверка на отмену
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
        await update.message.reply_text("Введите ваш номер телефона (сот.) (например, +7 123 456-78-90):", reply_markup=cancel_keyboard())
        return AWAITING_PHONE

    if step == AWAITING_PHONE:
        if not is_valid_phone(text):
            await update.message.reply_text(
                "❌ Некорректный номер. Введите номер, состоящий из цифр, возможно с +, пробелами или дефисами.",
                reply_markup=cancel_keyboard()
            )
            return AWAITING_PHONE
        context.user_data["phone"] = text
        if context.user_data.get("skip_service_step"):
            context.user_data["appointment_step"] = AWAITING_COMMENT
            await update.message.reply_text(
                "Если есть дополнительные пожелания или комментарий, напишите их здесь. "
                "Если нет, просто отправьте любой символ или слово «нет»:",
                reply_markup=cancel_keyboard()
            )
            return AWAITING_COMMENT
        context.user_data["appointment_step"] = AWAITING_SERVICE
        await update.message.reply_text(
            "Укажите, к какому врачу или на какую процедуру вы хотите записаться (например: «Терапевт» или «Массаж спины»):",
            reply_markup=cancel_keyboard()
        )
        return AWAITING_SERVICE

    if step == AWAITING_SERVICE:
        if not text:
            await update.message.reply_text("Пожалуйста, укажите услугу или врача.", reply_markup=cancel_keyboard())
            return AWAITING_SERVICE
        context.user_data["service"] = text
        context.user_data["appointment_step"] = AWAITING_COMMENT
        await update.message.reply_text(
            "Если есть дополнительные пожелания или комментарий, напишите их здесь. "
            "Если нет, просто отправьте любой символ или слово «нет»:",
            reply_markup=cancel_keyboard()
        )
        return AWAITING_COMMENT

    if step == AWAITING_COMMENT:
        comment = text if text.lower() not in {"нет", "нету", "-", "—"} else ""
        name = context.user_data["full_name"]
        phone = context.user_data["phone"]
        service = context.user_data["service"]

        await send_email_notification(name, phone, service, comment)

        confirm_msg = (
            f"✅ Спасибо, {name}!\n"
            f"Ваша заявка принята.\n"
            f"Услуга/врач: {service}\n"
            f"Телефон: {phone}\n"
            f"Комментарий: {comment if comment else 'нет'}\n\n"
            "Администратор свяжется с вами для подтверждения записи."
        )
        await update.message.reply_text(confirm_msg, reply_markup=main_menu_keyboard())

        context.user_data.clear()
        return ConversationHandler.END
    return None


async def cancel_appointment_form(update: Update, context):
    """Отменяет заполнение формы и возвращает в главное меню."""
    context.user_data.clear()
    await update.message.reply_text("Заполнение формы отменено.", reply_markup=main_menu_keyboard())


# ---------------------- INLINE ОБРАБОТЧИКИ ----------------------
async def button_doctor(update: Update, _):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("doctor_", "")
    doctor_data = data["specialists"]["doctors"][doctor_key]
    text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
    keyboard = doctor_detail_keyboard(doctor_key)
    photo_path = doctor_data.get("photo")
    if photo_path and await aiofiles_os.path.exists(photo_path):
        async with aiofiles.open(photo_path, "rb") as ph:
            await query.message.reply_photo(photo=await ph.read(), caption=text, reply_markup=keyboard, parse_mode="Markdown")
        await query.message.delete()
    else:
        await query.edit_message_text(text + "\n\n📷 Фото не найдено", reply_markup=keyboard, parse_mode="Markdown")


async def button_service_specialists(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Выберите специализацию:", reply_markup=service_specializations_keyboard())


async def button_specialization(update: Update, _):
    query = update.callback_query
    await query.answer()
    spec_key = query.data.replace("specialization_", "")
    spec_data = data["specializations"][spec_key]
    await query.edit_message_text(f"Выберите врача ({spec_data['title']}):", reply_markup=service_specialists_keyboard(spec_key))


async def button_service_doctor(update: Update, context):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("service_doctor_", "")
    for spec_key, spec in data["specializations"].items():
        if doctor_key in spec["doctors"]:
            context.user_data["current_specialization"] = spec_key
            doctor_data = spec["doctors"][doctor_key]
            text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
            keyboard = service_doctor_detail_keyboard(doctor_key, spec_key)
            photo_path = doctor_data.get("photo")
            if photo_path and await aiofiles_os.path.exists(photo_path):
                async with aiofiles.open(photo_path, "rb") as ph:
                    await query.message.reply_photo(photo=await ph.read(), caption=text, reply_markup=keyboard, parse_mode="Markdown")
                await query.message.delete()
            else:
                await query.edit_message_text(text + "\n\n📷 Фото не найдено", reply_markup=keyboard, parse_mode="Markdown")
            break


async def button_service_doctor_detail(update: Update, context):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("detail_service_doctor_", "")
    spec_key = context.user_data.get("current_specialization")
    if spec_key and doctor_key in data["specializations"][spec_key]["doctors"]:
        doctor_data = data["specializations"][spec_key]["doctors"][doctor_key]
        text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}\n\n{doctor_data['description']}"
        keyboard = service_doctor_description_keyboard(doctor_key, spec_key)
        photo_path = doctor_data.get("photo")
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as ph:
                await query.message.reply_photo(photo=ph, caption=text, reply_markup=keyboard, parse_mode="Markdown")
            await query.message.delete()
        else:
            await query.edit_message_text(text + "\n\n📷 Фото не найдено", reply_markup=keyboard, parse_mode="Markdown")
    else:
        await query.edit_message_text("Врач не найден.")


async def button_service_procedures(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(data["procedures"]["title"], reply_markup=service_procedures_keyboard())


async def button_procedure(update: Update, _):
    query = update.callback_query
    await query.answer()
    proc_key = query.data.replace("procedure_", "")
    proc_data = data["procedures"]["procedures_list"][proc_key]
    await query.edit_message_text(f"Процедура: {proc_data['name']}", reply_markup=procedure_detail_keyboard(proc_key))


async def button_direction(update: Update, _):
    query = update.callback_query
    await query.answer()
    dir_key = query.data.replace("direction_", "")
    dir_data = data["directions"]["directions_list"][dir_key]
    await query.edit_message_text(f"Направление: {dir_data['name']}", reply_markup=direction_detail_keyboard(dir_key))


async def button_direction_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    dir_key = query.data.replace("detail_direction_", "")
    dir_data = data["directions"]["directions_list"][dir_key]
    await query.edit_message_text(f"*{dir_data['name']}*\n\n{dir_data['description']}",
                                  reply_markup=direction_description_keyboard(dir_key), parse_mode="Markdown")


async def button_direction_more_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    dir_key = query.data.replace("more_detail_direction_", "")
    dir_data = data["directions"]["directions_list"][dir_key]
    await query.edit_message_text(f"*{dir_data['name']}*\n\n{dir_data['detailed_description']}",
                                  reply_markup=direction_detailed_description_keyboard(dir_key), parse_mode="Markdown")


async def button_service_health_programs(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(data["health_programs"]["title"], reply_markup=health_programs_keyboard())


async def button_service_diagnostics(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(data["diagnostics"]["title"], reply_markup=diagnostics_keyboard())


async def button_diagnostic(update: Update, _):
    query = update.callback_query
    await query.answer()
    diag_key = query.data.replace("diagnostic_", "")
    diag_data = data["diagnostics"]["diagnostics_list"][diag_key]
    await query.edit_message_text(f"*{diag_data['name']}*\n\n{diag_data['description']}",
                                  reply_markup=diagnostic_detail_keyboard(diag_key), parse_mode="Markdown")


async def button_diagnostic_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    diag_key = query.data.replace("detail_diagnostic_", "")
    diag_data = data["diagnostics"]["diagnostics_list"][diag_key]
    await query.edit_message_text(f"*{diag_data['name']}*\n\n{diag_data['detailed_description']}",
                                  reply_markup=diagnostic_description_keyboard(diag_key), parse_mode="Markdown")


async def button_service_what_we_treat(update: Update, _):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(data["what_we_treat"]["title"], reply_markup=what_we_treat_keyboard())


async def button_treatment(update: Update, _):
    query = update.callback_query
    await query.answer()
    treat_key = query.data.replace("treatment_", "")
    treat_data = data["what_we_treat"]["treatments_list"][treat_key]
    await query.edit_message_text(f"*{treat_data['name']}*\n\n{treat_data['description']}",
                                  reply_markup=treatment_detail_keyboard(treat_key), parse_mode="Markdown")


async def button_treatment_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    treat_key = query.data.replace("detail_treatment_", "")
    treat_data = data["what_we_treat"]["treatments_list"][treat_key]
    await query.edit_message_text(f"*{treat_data['name']}*\n\n{treat_data['detailed_description']}",
                                  reply_markup=treatment_description_keyboard(treat_key), parse_mode="Markdown")


async def button_health_program(update: Update, _):
    query = update.callback_query
    await query.answer()
    prog_key = query.data.replace("health_program_", "")
    prog_data = data["health_programs"]["programs_list"][prog_key]
    await query.edit_message_text(f"*{prog_data['name']}*\n\n{prog_data['description']}",
                                  reply_markup=health_program_detail_keyboard(prog_key), parse_mode="Markdown")


async def button_health_program_detail(update: Update, _):
    query = update.callback_query
    await query.answer()
    prog_key = query.data.replace("detail_health_program_", "")
    prog_data = data["health_programs"]["programs_list"][prog_key]
    await query.edit_message_text(f"*{prog_data['name']}*\n\n{prog_data['detailed_description']}",
                                  reply_markup=health_program_description_keyboard(prog_key), parse_mode="Markdown")


def get_service_or_doctor_name(app_type: str, app_id: str) -> str:
    try:
        if app_type == "doctor":
            if app_id in data["specialists"]["doctors"]:
                d = data["specialists"]["doctors"][app_id]
                return f"{d['name']} ({d['specialization']})"
            for spec in data["specializations"].values():
                if app_id in spec["doctors"]:
                    d = spec["doctors"][app_id]
                    return f"{d['name']} ({d['specialization']})"
        elif app_type == "procedure":
            return data["procedures"]["procedures_list"][app_id]["name"]
        elif app_type == "direction":
            return data["directions"]["directions_list"][app_id]["name"]
        elif app_type == "health_program":
            return data["health_programs"]["programs_list"][app_id]["name"]
        elif app_type == "diagnostic":
            return data["diagnostics"]["diagnostics_list"][app_id]["name"]
        elif app_type == "treatment":
            return data["what_we_treat"]["treatments_list"][app_id]["name"]
    except:
        pass
    return "Неизвестная услуга"


async def main_menu_handler(update: Update, context):
    welcome = data["start_message"]
    kb = main_menu_keyboard()
    if update.message:
        await update.message.reply_text(welcome, reply_markup=kb)
    else:
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        await query.message.chat.send_message(welcome, reply_markup=kb)


async def button_back(update: Update, context):
    query = update.callback_query
    await query.answer()
    back_to = query.data.replace("back_", "")
    try:
        if back_to in {"dates", "to_dates"}:
            context.user_data["appointment_step"] = "awaiting_date"
            await query.edit_message_text("Выберите удобную дату:", reply_markup=dates_calendar_keyboard())
        elif back_to == "appointment":
            await query.edit_message_text("Выберите удобную дату:", reply_markup=dates_calendar_keyboard())
            context.user_data["appointment_step"] = "awaiting_date"
        elif back_to == "main_menu":
            await main_menu_handler(update, context)
        else:
            await main_menu_handler(update, context)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise
