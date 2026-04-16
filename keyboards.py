import json
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

SERVICE_CALLBACK_MAP = {
    "Специалисты": "service_specialists",
    "Программы здоровья": "service_health_programs",
    "Диагностика": "service_diagnostics",
    "Чем мы лечим": "service_what_we_treat"
}


def main_menu_keyboard():
    buttons = [KeyboardButton(text) for text in data["main_menu"]["buttons"]]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def initial_survey_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Да")], [KeyboardButton("Нет")], [KeyboardButton("стоп")]],
        resize_keyboard=True, one_time_keyboard=True
    )


def extended_survey_keyboard():
    buttons = [
        ["Наш сайт"], ["Специалисты"], ["Контакты"], ["Услуги"],
        ["Оставить отзыв"], ["Записаться"], ["Главное меню"],
        ["Стоимость услуг"], ["Лекции и курсы"], ["Вопросы по лечению и консультации"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def specialists_keyboard():
    keyboard = [[InlineKeyboardButton(f"{doc['name']} - {doc['specialization']}", callback_data=f"doctor_{k}")]
                for k, doc in data["specialists"]["doctors"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


def doctor_detail_keyboard(doctor_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_specialists")]
    ])


def services_keyboard():
    keyboard = [[InlineKeyboardButton(btn, callback_data=SERVICE_CALLBACK_MAP.get(btn, "service_unknown"))]
                for btn in data["services"]["buttons"]]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


def service_specializations_keyboard():
    keyboard = [[InlineKeyboardButton(spec["title"], callback_data=f"specialization_{k}")]
                for k, spec in data["specializations"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def service_specialists_keyboard(specialization_key):
    spec = data["specializations"][specialization_key]
    keyboard = [[InlineKeyboardButton(doc["name"], callback_data=f"service_doctor_{k}")]
                for k, doc in spec["doctors"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_service_specializations")])
    return InlineKeyboardMarkup(keyboard)


def service_doctor_detail_keyboard(doctor_key, specialization_key=None):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}"),
         InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_service_doctor_{doctor_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_specialization_{specialization_key}")]
    ])


def service_doctor_description_keyboard(doctor_key, specialization_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_doctor_{doctor_key}_{specialization_key}")]
    ])


def service_procedures_keyboard():
    keyboard = [[InlineKeyboardButton(proc["name"], callback_data=f"procedure_{k}")]
                for k, proc in data["procedures"]["procedures_list"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def procedure_detail_keyboard(procedure_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_procedure_{procedure_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_procedures")]
    ])


def directions_keyboard():
    keyboard = [[InlineKeyboardButton(dir["name"], callback_data=f"direction_{k}")]
                for k, dir in data["directions"]["directions_list"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


def direction_detail_keyboard(direction_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_direction_{direction_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ])


def direction_description_keyboard(direction_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"more_detail_direction_{direction_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ])


def direction_detailed_description_keyboard(direction_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_direction_{direction_key}")]
    ])


def health_programs_keyboard():
    keyboard = [[InlineKeyboardButton(prog["name"], callback_data=f"health_program_{k}")]
                for k, prog in data["health_programs"]["programs_list"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def health_program_detail_keyboard(program_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_health_program_{program_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{program_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_health_programs")]
    ])


def health_program_description_keyboard(program_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{program_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_health_program_{program_key}")]
    ])


def diagnostics_keyboard():
    keyboard = [[InlineKeyboardButton(diag["name"], callback_data=f"diagnostic_{k}")]
                for k, diag in data["diagnostics"]["diagnostics_list"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def diagnostic_detail_keyboard(diagnostic_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_diagnostic_{diagnostic_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diagnostic_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_diagnostics")]
    ])


def diagnostic_description_keyboard(diagnostic_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diagnostic_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_diagnostic_{diagnostic_key}")]
    ])


def what_we_treat_keyboard():
    keyboard = [[InlineKeyboardButton(treat["name"], callback_data=f"treatment_{k}")]
                for k, treat in data["what_we_treat"]["treatments_list"].items()]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def treatment_detail_keyboard(treatment_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_treatment_{treatment_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treatment_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_what_we_treat")]
    ])


def treatment_description_keyboard(treatment_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treatment_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_treatment_{treatment_key}")]
    ])


def dates_calendar_keyboard():
    today = datetime.now().date()
    keyboard = []
    for i in range(14):
        date_obj = today + timedelta(days=i + 1)
        button_text = date_obj.strftime("%d.%m.%Y (%a)")
        callback_data = f"date_{date_obj.strftime('%Y-%m-%d')}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(keyboard)
