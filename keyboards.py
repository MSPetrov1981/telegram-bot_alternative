# Файл, генерирующий клавиатуры
import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Загружаем данные из JSON
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

# Маппинг кнопок услуг на callback_data
SERVICE_CALLBACK_MAP = {
    "Специалисты": "service_specialists",
    "Программы здоровья": "service_health_programs",
    "Диагностика": "service_diagnostics",
    "Чем мы лечим": "service_what_we_treat"
}


# --- Главное меню (Reply клавиатура) ---
def main_menu_keyboard():
    buttons = [KeyboardButton(text) for text in data["main_menu"]["buttons"]]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите опцию")


def initial_survey_keyboard():
    """Клавиатура первого вопроса опроса."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Да")], [KeyboardButton("Нет")], [KeyboardButton("стоп")]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Ответьте «Да», «Нет» или «стоп»"
    )


def extended_survey_keyboard():
    """Клавиатура расширенного меню (ветка «Нет»)."""
    buttons = [
        ["Наш сайт"],
        ["Специалисты"],
        ["Контакты"],
        ["Услуги"],
        ["Оставить отзыв"],
        ["Записаться"],
        ["Главное меню"],
        ["Стоимость услуг"],
        ["Лекции и курсы"],
        ["Вопросы по лечению и консультации"]
    ]
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите пункт расширенного меню"
    )


# --- Inline клавиатуры ---

# Клавиатура со списком специалистов (из главного меню)
def specialists_keyboard():
    keyboard = []
    for key, doctor in data["specialists"]["doctors"].items():
        button = InlineKeyboardButton(f"{doctor['name']} - {doctor['specialization']}",
                                     callback_data=f"doctor_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


def appointment_days_keyboard():
    keyboard = []
    for day in data["appointment"]["days"]:
        keyboard.append([InlineKeyboardButton(day, callback_data=f"day_{day}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_appointment")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для врача (Записаться и Назад) - для главного меню
def doctor_detail_keyboard(doctor_key):
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_specialists")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура с описанием врача (Записаться и Назад) - для главного меню
def doctor_description_keyboard(doctor_key):
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_specialists")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для меню "Услуги" (обновлённая)
def services_keyboard():
    keyboard = []
    for button_text in data["services"]["buttons"]:
        callback_data = SERVICE_CALLBACK_MAP.get(button_text, "service_unknown")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура со списком специализаций (из услуг)
def service_specializations_keyboard():
    keyboard = []
    for key, specialization in data["specializations"].items():
        button = InlineKeyboardButton(f"{specialization['title']}", callback_data=f"specialization_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура со списком врачей специализации (из услуг)
def service_specialists_keyboard(specialization_key):
    keyboard = []
    specialization = data["specializations"][specialization_key]
    for key, doctor in specialization["doctors"].items():
        button = InlineKeyboardButton(f"{doctor['name']}", callback_data=f"service_doctor_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_service_specializations")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для врача из услуг (Записаться, Подробнее и Назад)
def service_doctor_detail_keyboard(doctor_key, specialization_key=None):
    keyboard = [
        [
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}"),
            InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_service_doctor_{doctor_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_specialization_{specialization_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура с описанием врача из услуг (Записаться и Назад)
def service_doctor_description_keyboard(doctor_key, specialization_key):
    keyboard = [
        [
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_doctor_{doctor_key}"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_service_doctor_{doctor_key}_{specialization_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура со списком процедур (из услуг)
def service_procedures_keyboard():
    keyboard = []
    for key, procedure in data["procedures"]["procedures_list"].items():
        button = InlineKeyboardButton(f"{procedure['name']}", callback_data=f"procedure_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для процедуры (Записаться и Назад)
def procedure_detail_keyboard(procedure_key):
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_procedure_{procedure_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_procedures")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура со списком направлений
def directions_keyboard():
    keyboard = []
    for key, direction in data["directions"]["directions_list"].items():
        button = InlineKeyboardButton(f"{direction['name']}", callback_data=f"direction_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для направления (Подробнее, Записаться и Назад)
def direction_detail_keyboard(direction_key):
    keyboard = [
        [
            InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_direction_{direction_key}"),
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для описания направления (Записаться и Назад)
def direction_description_keyboard(direction_key):
    keyboard = [
        [
            InlineKeyboardButton("📖 Подробнее", callback_data=f"more_detail_direction_{direction_key}"),
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_directions")]
    ]
    return InlineKeyboardMarkup(keyboard)


def direction_detailed_description_keyboard(direction_key):
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_direction_{direction_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_direction_{direction_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Новые клавиатуры для программ здоровья ---
def health_programs_keyboard():
    """Клавиатура со списком программ здоровья"""
    keyboard = []
    for key, program in data["health_programs"]["programs_list"].items():
        button = InlineKeyboardButton(program["name"], callback_data=f"health_program_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def health_program_detail_keyboard(program_key):
    """Клавиатура для карточки программы (Подробнее, Записаться, Назад)"""
    keyboard = [
        [
            InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_health_program_{program_key}"),
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{program_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_health_programs")]
    ]
    return InlineKeyboardMarkup(keyboard)


def health_program_description_keyboard(program_key):
    """Клавиатура для подробного описания программы (Записаться, Назад к карточке)"""
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_health_program_{program_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_health_program_{program_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def diagnostics_keyboard():
    """Клавиатура со списком диагностик"""
    keyboard = []
    for key, diagnostic in data["diagnostics"]["diagnostics_list"].items():
        button = InlineKeyboardButton(diagnostic["name"], callback_data=f"diagnostic_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def diagnostic_detail_keyboard(diagnostic_key):
    """Клавиатура для карточки диагностики (Подробнее, Записаться, Назад)"""
    keyboard = [
        [
            InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_diagnostic_{diagnostic_key}"),
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diagnostic_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_diagnostics")]
    ]
    return InlineKeyboardMarkup(keyboard)


def diagnostic_description_keyboard(diagnostic_key):
    """Клавиатура для подробного описания диагностики (Записаться, Назад к карточке)"""
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_diagnostic_{diagnostic_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_diagnostic_{diagnostic_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Клавиатуры для раздела "Чем мы лечим" ---
def what_we_treat_keyboard():
    """Клавиатура со списком методов лечения"""
    keyboard = []
    for key, treatment in data["what_we_treat"]["treatments_list"].items():
        button = InlineKeyboardButton(treatment["name"], callback_data=f"treatment_{key}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_services")])
    return InlineKeyboardMarkup(keyboard)


def treatment_detail_keyboard(treatment_key):
    """Клавиатура для карточки лечения (Подробнее, Записаться, Назад)"""
    keyboard = [
        [
            InlineKeyboardButton("📖 Подробнее", callback_data=f"detail_treatment_{treatment_key}"),
            InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treatment_key}")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_service_what_we_treat")]
    ]
    return InlineKeyboardMarkup(keyboard)


def treatment_description_keyboard(treatment_key):
    """Клавиатура для подробного описания лечения (Записаться, Назад к карточке)"""
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data=f"appointment_treatment_{treatment_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_treatment_{treatment_key}")]
    ]
    return InlineKeyboardMarkup(keyboard)
