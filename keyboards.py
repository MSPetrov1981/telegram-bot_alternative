import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

# Очищаем пробелы в маппинге колбэков
SERVICE_CALLBACK_MAP = {
    "Специалисты": "service_specialists",
    "Программы здоровья": "service_health_programs",
    "Диагностика": "service_diagnostics",
    "Чем мы лечим": "service_what_we_treat",
}

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text) for text in data["main_menu"]["buttons"]]
    return ReplyKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)], resize_keyboard=True)

def initial_survey_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("Да")], [KeyboardButton("Нет")], [KeyboardButton("стоп")]], resize_keyboard=True, one_time_keyboard=True)

def extended_survey_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("Наш сайт")], [KeyboardButton("Специалисты")], [KeyboardButton("Контакты")],
        [KeyboardButton("Услуги")], [KeyboardButton("Оставить отзыв")], [KeyboardButton("Записаться")],
        [KeyboardButton("Главное меню")], [KeyboardButton("Стоимость услуг")], [KeyboardButton("Лекции и курсы")],
        [KeyboardButton("Вопросы по лечению и консультации")]
    ], resize_keyboard=True)

def specialists_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{d['name']} - {d['specialization']}", callback_data=f"doctor_{k}")]
        for k, d in data["specialists"]["doctors"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")]])

def doctor_detail_keyboard(doc_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doc_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_specialists")]
    ])

def services_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn, callback_data=SERVICE_CALLBACK_MAP.get(btn, "service_unknown"))]
        for btn in data["services"]["buttons"]
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")]])

def service_specializations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s["title"], callback_data=f"specialization_{k}")]
        for k, s in data["specializations"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_services")]])

def service_specialists_keyboard(spec_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(d["name"], callback_data=f"service_doctor_{k}")]
        for k, d in data["specializations"][spec_key]["doctors"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_service_specializations")]])

def service_doctor_detail_keyboard(doc_key: str, spec_key: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doc_key}"),
         InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_service_doctor_{doc_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_specialization_{spec_key}")]
    ])

def service_doctor_description_keyboard(doc_key: str, spec_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doc_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_doctor_{doc_key}_{spec_key}")]
    ])

def service_procedures_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(p["name"], callback_data=f"procedure_{k}")]
        for k, p in data["procedures"]["procedures_list"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_services")]])

def procedure_detail_keyboard(proc_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_procedure_{proc_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_procedures")]
    ])

def directions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(d["name"], callback_data=f"direction_{k}")]
        for k, d in data["directions"]["directions_list"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")]])

def direction_detail_keyboard(dir_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_direction_{dir_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{dir_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ])

def direction_description_keyboard(dir_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"more_detail_direction_{dir_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{dir_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ])

def direction_detailed_description_keyboard(dir_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{dir_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_direction_{dir_key}")]
    ])

def health_programs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(p["name"], callback_data=f"health_program_{k}")]
        for k, p in data["health_programs"]["programs_list"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_services")]])

def health_program_detail_keyboard(prog_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_health_program_{prog_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{prog_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_health_programs")]
    ])

def health_program_description_keyboard(prog_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{prog_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_health_program_{prog_key}")]
    ])

def diagnostics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(d["name"], callback_data=f"diagnostic_{k}")]
        for k, d in data["diagnostics"]["diagnostics_list"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_services")]])

def diagnostic_detail_keyboard(diag_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_diagnostic_{diag_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diag_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_diagnostics")]
    ])

def diagnostic_description_keyboard(diag_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diag_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_diagnostic_{diag_key}")]
    ])

def what_we_treat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["name"], callback_data=f"treatment_{k}")]
        for k, t in data["what_we_treat"]["treatments_list"].items()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data="back_services")]])

def treatment_detail_keyboard(treat_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_treatment_{treat_key}"),
         InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treat_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_what_we_treat")]
    ])

def treatment_description_keyboard(treat_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treat_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_treatment_{treat_key}")]
    ])

def dates_calendar_keyboard() -> InlineKeyboardMarkup:
    today = datetime.now().date()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i + 1)).strftime("%d.%m.%Y (%a)"), callback_data=f"date_{(today + timedelta(days=i + 1)).strftime('%Y-%m-%d')}")]
        for i in range(14)
    ]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(keyboard)