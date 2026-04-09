# Файл с обработчиками команд и сообщений
import json
import logging
import os

import aiofiles
import aiofiles.os as aiofiles_os
from telegram import (
    ReplyKeyboardRemove,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import (
    appointment_days_keyboard,
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

logger = logging.getLogger(__name__)

# Состояния
NAME, PHONE, DAY = range(3)

# Загружаем данные из JSON
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

# Состояние опроса: None, 'waiting_for_response', 'completed'
SURVEY_STATE = {}


# Обработчик команды /start
async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Приветствие + фото + контакты + опрос."""
    welcome_text = data["start_message"]
    clinic_images = data["clinic_images"]
    contact_numbers = data["contact_numbers"]

    await update.message.reply_text(welcome_text)

    for img in clinic_images:
        if await aiofiles_os.path.exists(img):
            async with aiofiles.open(img, "rb") as ph:
                photo_data = await ph.read()
                await update.message.reply_photo(photo=photo_data)
        else:
            logger.warning("Фото не найдено: %s", img)

    await update.message.reply_text(contact_numbers)

    # ставим опрос
    SURVEY_STATE[update.effective_chat.id] = "waiting"
    await update.message.reply_text(
        'Чтобы отписаться, нажмите в этот чат "стоп".',
        reply_markup=initial_survey_keyboard()
    )


# Обработчик текстовых сообщений — для опроса
async def survey_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает только первый ответ пользователя после /start."""
    chat_id = update.effective_chat.id
    if SURVEY_STATE.get(chat_id) != "waiting":
        return   # опрос уже закончен – ничего не делаем

    text = update.message.text.strip().lower()
    SURVEY_STATE[chat_id] = None          # выходим из режима опроса

    if text == "стоп":
        await update.message.reply_text(
            "Вы отписались от опроса. Бот больше не будет вас беспокоить.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if text == "да":
        await update.message.reply_text(
            "Рады, что мы с вами знакомы! Выберите нужный пункт.",
            reply_markup=main_menu_keyboard()
        )
        return

    if text == "нет":
        # ставим флаг, что пользователь в расширенном меню
        context.user_data["from_extended_menu"] = True
        await update.message.reply_text(
            "Давайте знакомиться!",
            reply_markup=extended_survey_keyboard()
        )
        return

    # не распознали
    SURVEY_STATE[chat_id] = "waiting"   # оставляем в опросе
    await update.message.reply_text(
        "Пожалуйста, ответьте «Да», «Нет» или «стоп».",
        reply_markup=initial_survey_keyboard()
    )


# --- Обработчики кнопок из расширенного опроса ---
async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Наш сайт: https://alternative-clinic.ru"
    if context.user_data.get("from_extended_menu"):
        kb = extended_survey_keyboard()
    else:
        main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def specialists_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = data["specialists"]["title"]
    kb = specialists_keyboard()
    if context.user_data.get("from_extended_menu"):
        kb = specialists_keyboard()
    else:
        main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def services_main(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    text = data["services"]["title"]
    keyboard = services_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)


async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = data["contacts"]
    if context.user_data.get("from_extended_menu"):
        kb = extended_survey_keyboard()
    else:
        main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def leave_review(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо за желание оставить отзыв! Пожалуйста, напишите ваш отзыв в этом чате, и мы его обязательно прочитаем.")


async def appointment(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функция записи будет реализована позже")


async def main_menu_from_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("from_extended_menu", None)
    await update.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())


async def cost_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Прайс-лист находится на сайте в разделе «Цены»."
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def lectures_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Ближайшие курсы и лекции публикуются в нашем Telegram-канале: @alternative_clinic"
    kb = extended_survey_keyboard() if context.user_data.get("from_extended_menu") else main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=kb)


async def questions_consultation(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вопросы по лечению и консультации: напишите нам в чат — мы ответим в течение 24 часов.")


# Обработчик текстового сообщения "Направления"
async def directions_main(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    text = data["directions"]["title"]
    keyboard = directions_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard)


# Обработчик текстового сообщения "Наш сайт"
async def website_main(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Наш сайт: https://alternative-clinic.ru")


# --- Обработчики CallbackQuery (нажатия на inline-кнопки) ---

# Обработчик выбора врача из специалистов (главное меню)
async def button_doctor(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("doctor_", "")
    doctor_data = data["specialists"]["doctors"][doctor_key]
    photo_path = doctor_data.get("photo")
    text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
    keyboard = doctor_detail_keyboard(doctor_key)
    if photo_path and await aiofiles_os.path.exists(photo_path):
        async with aiofiles.open(photo_path, "rb") as photo_file:
            photo_data = await photo_file.read()
            await query.message.reply_photo(
                photo=photo_data,
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
        )
        await query.message.delete()
    else:
        await query.edit_message_text(
            text + "\n\n📷 *Фотография не найдена*",
            reply_markup=keyboard,
            parse_mode="Markdown"
    )


# Обработчик выбора "Специалисты" внутри "Услуг"
async def button_service_specialists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "Выберите специализацию:"
    keyboard = service_specializations_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)


# Обработчик выбора специализации внутри услуг
async def button_specialization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    specialization_key = query.data.replace("specialization_", "")
    specialization_data = data["specializations"][specialization_key]
    text = f"Выберите врача ({specialization_data['title']}):"
    keyboard = service_specialists_keyboard(specialization_key)
    await query.edit_message_text(text, reply_markup=keyboard)


# Обработчик выбора врача из услуг
async def button_service_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("service_doctor_", "")

    # Сохраняем текущую специализацию в контексте пользователя
    current_specialization = None
    for spec_key, specialization in data["specializations"].items():
        if doctor_key in specialization["doctors"]:
            current_specialization = spec_key
            context.user_data["current_specialization"] = spec_key
            break

    doctor_data = None
    for specialization in data["specializations"].values():
        if doctor_key in specialization["doctors"]:
            doctor_data = specialization["doctors"][doctor_key]
            break

    if doctor_data:
        photo_path = doctor_data.get("photo")
        text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
        keyboard = service_doctor_detail_keyboard(doctor_key, current_specialization)
        if photo_path and await aiofiles_os.path.exists(photo_path):
            async with aiofiles.open(photo_path, "rb") as photo_file:
                photo_data = await photo_file.read()
                await query.message.reply_photo(
                    photo=photo_data,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
        )
            await query.message.delete()
        else:
            await query.edit_message_text(
                text + "\n\n📷 *Фотография не найдена*",
                reply_markup=keyboard,
                parse_mode="Markdown"
    )
    else:
        await query.edit_message_text("Данные о враче не найдены.")


# Обработчик кнопки "Подробнее" о враче из услуг
async def button_service_doctor_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doctor_key = query.data.replace("detail_service_doctor_", "")

    # Получаем специализацию из контекста
    specialization_key = context.user_data.get("current_specialization")

    if not specialization_key:
        # Если специализация не сохранена, пытаемся найти её
        for spec_key, specialization in data["specializations"].items():
            if doctor_key in specialization["doctors"]:
                specialization_key = spec_key
                context.user_data["current_specialization"] = spec_key
                break

    doctor_data = None
    if specialization_key:
        doctor_data = data["specializations"][specialization_key]["doctors"].get(doctor_key)

    if doctor_data:
        photo_path = doctor_data.get("photo")
        text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}\n\n{doctor_data['description']}"
        keyboard = service_doctor_description_keyboard(doctor_key, specialization_key)
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            await query.message.delete()
        else:
            await query.edit_message_text(
                text + "\n\n📷 *Фотография не найдена*",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        await query.edit_message_text("Данные о враче не найдены.")


# Обработчик выбора "Процедуры" внутри "Услуг"
async def button_service_procedures(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = data["procedures"]["title"]
    keyboard = service_procedures_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)


# Обработчик выбора процедуры
async def button_procedure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    procedure_key = query.data.replace("procedure_", "")
    procedure_data = data["procedures"]["procedures_list"][procedure_key]
    text = f"Процедура: {procedure_data['name']}"
    keyboard = procedure_detail_keyboard(procedure_key)
    await query.edit_message_text(text, reply_markup=keyboard)


# Обработчик выбора направления
async def button_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction_key = query.data.replace("direction_", "")
    direction_data = data["directions"]["directions_list"][direction_key]
    text = f"Направление: {direction_data['name']}"
    keyboard = direction_detail_keyboard(direction_key)
    await query.edit_message_text(text, reply_markup=keyboard)


# Обработчик кнопки "Подробнее" у направления
async def button_direction_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction_key = query.data.replace("detail_direction_", "")
    direction_data = data["directions"]["directions_list"][direction_key]
    text = f"*{direction_data['name']}*\n\n{direction_data['description']}"
    keyboard = direction_description_keyboard(direction_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


# Обработчик для кнопки "Подробнее" в описании направления
async def button_direction_more_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction_key = query.data.replace("more_detail_direction_", "")
    direction_data = data["directions"]["directions_list"][direction_key]
    text = f"*{direction_data['name']}*\n\n{direction_data['detailed_description']}"
    keyboard = direction_detailed_description_keyboard(direction_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


# --- Обработчики для новых кнопок услуг ---
async def button_service_health_programs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список программ здоровья"""
    query = update.callback_query
    await query.answer()
    text = data["health_programs"]["title"]
    keyboard = health_programs_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)


async def button_service_diagnostics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список диагностик"""
    query = update.callback_query
    await query.answer()
    text = data["diagnostics"]["title"]
    keyboard = diagnostics_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)


async def button_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор конкретной диагностики"""
    query = update.callback_query
    await query.answer()
    diagnostic_key = query.data.replace("diagnostic_", "")
    diagnostic_data = data["diagnostics"]["diagnostics_list"][diagnostic_key]
    text = f"*{diagnostic_data['name']}*\n\n{diagnostic_data['description']}"
    keyboard = diagnostic_detail_keyboard(diagnostic_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def button_diagnostic_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробное описание диагностики"""
    query = update.callback_query
    await query.answer()
    diagnostic_key = query.data.replace("detail_diagnostic_", "")
    diagnostic_data = data["diagnostics"]["diagnostics_list"][diagnostic_key]
    text = f"*{diagnostic_data['name']}*\n\n{diagnostic_data['detailed_description']}"
    keyboard = diagnostic_description_keyboard(diagnostic_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")    


async def button_service_what_we_treat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список методов лечения"""
    query = update.callback_query
    await query.answer()
    text = data["what_we_treat"]["title"]
    keyboard = what_we_treat_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard)

    # обработчик раздела"чем мы лечим"


async def button_treatment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор конкретного метода лечения"""
    query = update.callback_query
    await query.answer()
    treatment_key = query.data.replace("treatment_", "")
    treatment_data = data["what_we_treat"]["treatments_list"][treatment_key]
    text = f"*{treatment_data['name']}*\n\n{treatment_data['description']}"
    keyboard = treatment_detail_keyboard(treatment_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def button_treatment_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробное описание метода лечения"""
    query = update.callback_query
    await query.answer()
    treatment_key = query.data.replace("detail_treatment_", "")
    treatment_data = data["what_we_treat"]["treatments_list"][treatment_key]
    text = f"*{treatment_data['name']}*\n\n{treatment_data['detailed_description']}"
    keyboard = treatment_description_keyboard(treatment_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


# --- Обработчики программ здоровья ---
async def button_health_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор конкретной программы здоровья"""
    query = update.callback_query
    await query.answer()
    program_key = query.data.replace("health_program_", "")
    program_data = data["health_programs"]["programs_list"][program_key]
    text = f"*{program_data['name']}*\n\n{program_data['description']}"
    keyboard = health_program_detail_keyboard(program_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def button_health_program_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробное описание программы здоровья"""
    query = update.callback_query
    await query.answer()
    program_key = query.data.replace("detail_health_program_", "")
    program_data = data["health_programs"]["programs_list"][program_key]
    text = f"*{program_data['name']}*\n\n{program_data['detailed_description']}"
    keyboard = health_program_description_keyboard(program_key)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


# --- Обработчик кнопки "Назад" (обновлённый) ---
async def button_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_to = query.data.replace("back_", "")

    try:
        if back_to == "main_menu":
            text = data["start_message"]
            reply_keyboard = main_menu_keyboard()
            await query.message.delete()
            await query.message.reply_text(text, reply_markup=reply_keyboard)

        elif back_to == "specialists":
            text = data["specialists"]["title"]
            keyboard = specialists_keyboard()
            await query.message.delete()
            await query.message.reply_text(text, reply_markup=keyboard)

        elif back_to == "services":
            text = data["services"]["title"]
            keyboard = services_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to == "service_health_programs":
            text = data["health_programs"]["title"]
            keyboard = health_programs_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to == "service_diagnostics":
            text = data["diagnostics"]["title"]
            keyboard = diagnostics_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to.startswith("diagnostic_"):
            diagnostic_key = back_to.replace("diagnostic_", "")
            diagnostic_data = data["diagnostics"]["diagnostics_list"].get(diagnostic_key)
            if diagnostic_data:
                text = f"*{diagnostic_data['name']}*\n\n{diagnostic_data['description']}"
                keyboard = diagnostic_detail_keyboard(diagnostic_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Диагностика не найдена")

        elif back_to.startswith("detail_diagnostic_"):
            diagnostic_key = back_to.replace("detail_diagnostic_", "")
            diagnostic_data = data["diagnostics"]["diagnostics_list"].get(diagnostic_key)
            if diagnostic_data:
                text = f"*{diagnostic_data['name']}*\n\n{diagnostic_data['detailed_description']}"
                keyboard = diagnostic_description_keyboard(diagnostic_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Диагностика не найдена")

        elif back_to.startswith("health_program_"):
            program_key = back_to.replace("health_program_", "")
            program_data = data["health_programs"]["programs_list"].get(program_key)
            if program_data:
                text = f"*{program_data['name']}*\n\n{program_data['description']}"
                keyboard = health_program_detail_keyboard(program_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Программа не найдена")

        elif back_to.startswith("detail_health_program_"):
            program_key = back_to.replace("detail_health_program_", "")
            program_data = data["health_programs"]["programs_list"].get(program_key)
            if program_data:
                text = f"*{program_data['name']}*\n\n{program_data['detailed_description']}"
                keyboard = health_program_description_keyboard(program_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Программа не найдена")

        elif back_to == "directions":
            text = data["directions"]["title"]
            keyboard = directions_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to == "service_specializations":
            text = "Выберите специализацию:"
            keyboard = service_specializations_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to == "service_procedures":
            text = data["procedures"]["title"]
            keyboard = service_procedures_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to.startswith("direction_"):
            direction_key = back_to.replace("direction_", "")
            direction_data = data["directions"]["directions_list"].get(direction_key)
            if direction_data:
                text = f"Направление: {direction_data['name']}"
                keyboard = direction_detail_keyboard(direction_key)
                await query.edit_message_text(text, reply_markup=keyboard)
            else:
                await handle_invalid_state(query, "Направление не найдено")

        elif back_to.startswith("service_specialization_"):
            specialization_key = back_to.replace("service_specialization_", "")
            if specialization_key in data["specializations"]:
                specialization_data = data["specializations"][specialization_key]
                text = f"Выберите врача ({specialization_data['title']}):"
                keyboard = service_specialists_keyboard(specialization_key)
                await query.message.delete()
                await query.message.reply_text(text, reply_markup=keyboard)
            else:
                await handle_invalid_state(query, "Специализация не найдена")
        elif back_to == "service_what_we_treat":
            text = data["what_we_treat"]["title"]
            keyboard = what_we_treat_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)

        elif back_to.startswith("treatment_"):
            treatment_key = back_to.replace("treatment_", "")
            treatment_data = data["what_we_treat"]["treatments_list"].get(treatment_key)
            if treatment_data:
                text = f"*{treatment_data['name']}*\n\n{treatment_data['description']}"
                keyboard = treatment_detail_keyboard(treatment_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Метод лечения не найден")

        elif back_to.startswith("detail_treatment_"):
            treatment_key = back_to.replace("detail_treatment_", "")
            treatment_data = data["what_we_treat"]["treatments_list"].get(treatment_key)
            if treatment_data:
                text = f"*{treatment_data['name']}*\n\n{treatment_data['detailed_description']}"
                keyboard = treatment_description_keyboard(treatment_key)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await handle_invalid_state(query, "Метод лечения не найден")

        elif back_to.startswith("service_doctor_"):
            parts = back_to.split("_")
            if len(parts) >= 3:
                doctor_key = parts[2]
                specialization_key = "_".join(parts[3:])
                doctor_data = None
                if specialization_key in data["specializations"]:
                    doctor_data = data["specializations"][specialization_key]["doctors"].get(doctor_key)
                if doctor_data:
                    photo_path = doctor_data.get("photo")
                    text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
                    keyboard = service_doctor_detail_keyboard(doctor_key, specialization_key)
                    if photo_path and os.path.exists(photo_path):
                        with open(photo_path, "rb") as photo:
                            await query.message.reply_photo(
                                photo=photo,
                                caption=text,
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )
                        await query.message.delete()
                    else:
                        await query.edit_message_text(
                            text + "\n\n📷 *Фотография не найдена*",
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                else:
                    await handle_invalid_state(query, "Врач не найден")
            else:
                await handle_invalid_state(query, "Неверный формат данных возврата")

        elif back_to == "appointment":
            await handle_back_from_appointment(update, context)

        else:
            await handle_invalid_state(query, f"Неизвестный пункт возврата: {back_to}")

    except Exception as e:
        logger.exception("Ошибка в обработчике возврата: %s", e)
        await handle_invalid_state(query, "Произошла ошибка при возврате")


# Обработчик для всех кнопок "Записаться" (обновлённый)
async def button_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    appointment_data = query.data

    parts = appointment_data.split("_")
    if len(parts) < 2 or parts[0] != "appointment":
        await query.edit_message_text("Ошибка: неверный формат данных записи")
        return None

    appointment_type = parts[1]
    appointment_id = "_".join(parts[2:])

    # Сохраняем данные для возврата
    context.user_data["appointment_type"] = appointment_type
    context.user_data["appointment_id"] = appointment_id

    # Для врачей из специализаций сохраняем контекст специализации
    if appointment_type == "doctor":
        specialization_key = None
        for spec_key, specialization in data["specializations"].items():
            if appointment_id in specialization["doctors"]:
                specialization_key = spec_key
                break
        if specialization_key:
            context.user_data["specialization_key"] = specialization_key
            context.user_data["is_from_specialization"] = True
        else:
            context.user_data["is_from_specialization"] = False
    else:
        context.user_data["is_from_specialization"] = False

    text = "Выберите удобный день для записи:"
    keyboard = appointment_days_keyboard()

    await query.edit_message_text(text, reply_markup=keyboard)
    return DAY


async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_day = query.data.replace("day_", "")
    context.user_data["selected_day"] = selected_day

    await query.edit_message_text("Отлично! Теперь введите ваше имя:")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["name"] = name

    await update.message.reply_text("Спасибо! Теперь введите ваш номер телефона:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data["phone"] = phone

    # Получаем данные для подтверждения
    context.user_data["selected_day"]
    context.user_data["name"]
    appointment_type = context.user_data.get("appointment_type")
    appointment_id = context.user_data.get("appointment_id")

    # Получаем название услуги/врача
    service_or_doctor = get_service_or_doctor_name(appointment_type, appointment_id)

    # Сохраняем данные в контексте (если нужно)
    context.user_data["service_or_doctor"] = service_or_doctor

    # Формируем подтверждение пользователю
    confirmation_message = data["appointment"]["confirmation_message"]
    await update.message.reply_text(confirmation_message)

    # Очищаем данные пользователя
    context.user_data.clear()

    # Возвращаем в главное меню
    await main_menu_handler(update, context)
    return ConversationHandler.END


def get_service_or_doctor_name(appointment_type: str, appointment_id: str) -> str:
    """Получает название услуги/врача по типу и ID"""
    try:
        if appointment_type == "doctor":
            if appointment_id in data["specialists"]["doctors"]:
                doctor_data = data["specialists"]["doctors"][appointment_id]
                return f"{doctor_data['name']} ({doctor_data['specialization']})"
            for _spec_key, specialization in data["specializations"].items():
                if appointment_id in specialization["doctors"]:
                    doctor_data = specialization["doctors"][appointment_id]
                    return f"{doctor_data['name']} ({doctor_data['specialization']})"
        elif appointment_type == "procedure":
            procedure_data = data["procedures"]["procedures_list"].get(appointment_id)
            if procedure_data:
                return procedure_data["name"]
        elif appointment_type == "direction":
            direction_data = data["directions"]["directions_list"].get(appointment_id)
            if direction_data:
                return direction_data["name"]
        elif appointment_type == "health_program":
            program_data = data["health_programs"]["programs_list"].get(appointment_id)
            if program_data:
                return program_data["name"]
        elif appointment_type == "diagnostic":
            diagnostic_data = data["diagnostics"]["diagnostics_list"].get(appointment_id)
            if diagnostic_data:
                return diagnostic_data["name"]
        elif appointment_type == "treatment":
            treatment_data = data["what_we_treat"]["treatments_list"].get(appointment_id)
            if treatment_data:
                return treatment_data["name"]

    except Exception as e:
        logger.exception("Ошибка получения названия услуги/врача: %s", e)
    return "Неизвестная услуга"


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет пользователя в главное меню"""
    welcome_text = data["start_message"]
    keyboard = main_menu_keyboard()
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=keyboard)
    else:
        query = update.callback_query
        await query.edit_message_text(welcome_text, reply_markup=keyboard)


async def handle_back_from_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает возврат из процесса записи на приём (обновлён)"""
    query = update.callback_query
    await query.answer()

    appointment_type = context.user_data.get("appointment_type")
    appointment_id = context.user_data.get("appointment_id")

    if not appointment_type or not appointment_id:
        await query.edit_message_text("Данные о записи не найдены. Возврат в главное меню.")
        await main_menu_handler(update, context)
        return

    try:
        if appointment_type == "doctor":
            specialization_key = context.user_data.get("specialization_key")
            if appointment_id in data["specialists"]["doctors"]:
                doctor_data = data["specialists"]["doctors"][appointment_id]
                photo_path = doctor_data.get("photo")
                text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
                keyboard = doctor_detail_keyboard(appointment_id)
            elif specialization_key:
                doctor_data = None
                if specialization_key in data["specializations"]:
                    doctor_data = data["specializations"][specialization_key]["doctors"].get(appointment_id)
                if not doctor_data:
                    await query.edit_message_text("Врач не найден. Возврат в главное меню.")
                    await main_menu_handler(update, context)
                    return
                photo_path = doctor_data.get("photo")
                text = f"*{doctor_data['name']}*\nСпециализация: {doctor_data['specialization']}"
                keyboard = service_doctor_detail_keyboard(appointment_id, specialization_key)
            else:
                await query.edit_message_text("Врач не найден. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return

            if photo_path and os.path.exists(photo_path):
                with open(photo_path, "rb") as photo:
                    await query.message.reply_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                await query.message.delete()
            else:
                await query.edit_message_text(
                    text + "\n\n📷 *Фотография не найдена*",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )

        elif appointment_type == "procedure":
            procedure_data = data["procedures"]["procedures_list"].get(appointment_id)
            if not procedure_data:
                await query.edit_message_text("Процедура не найдена. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return
            text = f"Процедура: {procedure_data['name']}"
            keyboard = procedure_detail_keyboard(appointment_id)
            await query.edit_message_text(text, reply_markup=keyboard)

        elif appointment_type == "direction":
            direction_data = data["directions"]["directions_list"].get(appointment_id)
            if not direction_data:
                await query.edit_message_text("Направление не найдено. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return
            text = f"Направление: {direction_data['name']}"
            keyboard = direction_detail_keyboard(appointment_id)
            await query.edit_message_text(text, reply_markup=keyboard)

        elif appointment_type == "diagnostic":
            diagnostic_data = data["diagnostics"]["diagnostics_list"].get(appointment_id)
            if not diagnostic_data:
                await query.edit_message_text("Диагностика не найдена. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return
            text = f"*{diagnostic_data['name']}*\n\n{diagnostic_data['description']}"
            keyboard = diagnostic_detail_keyboard(appointment_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

        elif appointment_type == "health_program":
            program_data = data["health_programs"]["programs_list"].get(appointment_id)
            if not program_data:
                await query.edit_message_text("Программа не найдена. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return
            text = f"*{program_data['name']}*\n\n{program_data['description']}"
            keyboard = health_program_detail_keyboard(appointment_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

        elif appointment_type == "treatment":
            treatment_data = data["what_we_treat"]["treatments_list"].get(appointment_id)
            if not treatment_data:
                await query.edit_message_text("Метод лечения не найден. Возврат в главное меню.")
                await main_menu_handler(update, context)
                return
            text = f"*{treatment_data['name']}*\n\n{treatment_data['description']}"
            keyboard = treatment_detail_keyboard(appointment_id)
           
        else:
            await query.edit_message_text("Неизвестный тип записи. Возврат в главное меню.")
            await main_menu_handler(update, context)

    except Exception as e:
        logger.exception("Ошибка при возврате из записи: %s", e)
        await query.edit_message_text(f"Ошибка: {e!s}. Возврат в главное меню.")
        await main_menu_handler(update, context)


async def handle_invalid_state(query, error_message: str):
    """Обрабатывает некорректные состояния и ошибки"""
    logger.warning("Некорректное состояние возврата: %s", error_message)
    try:
        await query.message.delete()
        await query.message.reply_text(
            f"⚠️ {error_message}\n\nВозврат в главное меню...",
            reply_markup=main_menu_keyboard()
        )
    except BadRequest as e:
        if "message to edit not found" in str(e) or "message can't be deleted" in str(e):
            await query.message.reply_text(
                f"⚠️ {error_message}\n\nВозврат в главное меню...",
                reply_markup=main_menu_keyboard()
            )
        else:
            raise


async def cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет процесс записи"""
    if update.message:
        await update.message.reply_text(
            "Запись отменена. Выберите другой раздел:",
            reply_markup=main_menu_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.answer("Запись отменена")
        await update.callback_query.edit_message_text(
            "Запись отменена. Выберите другой раздел:",
            reply_markup=main_menu_keyboard()
        )
    context.user_data.clear()
    return ConversationHandler.END
