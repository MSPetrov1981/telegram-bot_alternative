# Основной файл для запуска тг-бота
import logging
import os
import traceback

from dotenv import load_dotenv
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from handlers import (
    DAY,
    NAME,
    PHONE,
    appointment,
    button_appointment,
    button_back,
    button_diagnostic,
    button_diagnostic_detail,
    button_direction,
    button_direction_detail,
    button_direction_more_detail,
    button_doctor,
    button_health_program,
    button_health_program_detail,
    button_procedure,
    button_service_diagnostics,
    button_service_doctor,
    button_service_doctor_detail,
    button_service_health_programs,
    button_service_procedures,
    button_service_specialists,
    button_service_what_we_treat,
    button_specialization,
    button_treatment,
    button_treatment_detail,
    cancel_appointment,
    contacts,
    cost_services,
    directions_main,
    get_name,
    get_phone,
    handle_back_from_appointment,
    leave_review,
    lectures_courses,
    main_menu_from_survey,
    questions_consultation,
    select_day,
    services_main,
    specialists_main,
    start,
    survey_response,
    website,
    website_main,
)

load_dotenv()
BOT_TOKEN1 = os.getenv("BOT_TOKEN1")

# Включим логирование, чтобы видеть ошибки
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок."""
    # Используем %-форматирование вместо f-строки для ленивого логирования
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    "".join(tb_list)
    logger.error("Exception while handling update: %s", context.error)

    if isinstance(context.error, BadRequest):
        if "Inline keyboard expected" in str(context.error):
            logger.warning("Ignored: Inline keyboard expected error")
        elif "Can't parse entities" in str(context.error):
            logger.warning("Ignored: Markdown parsing error")
        return

    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте еще раз.")


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN1).build()
     # Создаём кастомный request с большими таймаутами (connect=20 сек, read=60 сек)
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0, write_timeout=20.0)
    application = Application.builder().token(BOT_TOKEN1).request(request).build()

    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))

    # Обработчики текстовых сообщений из главного меню
    application.add_handler(MessageHandler(filters.Regex("^Специалисты$"), specialists_main))
    application.add_handler(MessageHandler(filters.Regex("^Услуги$"), services_main))
    application.add_handler(MessageHandler(filters.Regex("^Направления$"), directions_main))
    application.add_handler(MessageHandler(filters.Regex("^Наш сайт$"), website_main))

    # Обработчики нажатий на inline-кнопки
    application.add_handler(CallbackQueryHandler(button_doctor, pattern="^doctor_"))
    application.add_handler(CallbackQueryHandler(button_service_specialists, pattern="^service_specialists$"))
    application.add_handler(CallbackQueryHandler(button_specialization, pattern="^specialization_"))
    application.add_handler(CallbackQueryHandler(button_service_doctor, pattern="^service_doctor_"))
    application.add_handler(CallbackQueryHandler(button_service_doctor_detail, pattern="^detail_service_doctor_"))
    application.add_handler(CallbackQueryHandler(button_service_procedures, pattern="^service_procedures$"))
    application.add_handler(CallbackQueryHandler(button_procedure, pattern="^procedure_"))
    application.add_handler(CallbackQueryHandler(button_direction, pattern="^direction_"))
    application.add_handler(CallbackQueryHandler(button_direction_detail, pattern="^detail_direction_"))
    application.add_handler(CallbackQueryHandler(button_direction_more_detail, pattern="^more_detail_direction_"))
    application.add_handler(CallbackQueryHandler(button_appointment, pattern="^appointment_"))
    application.add_handler(CallbackQueryHandler(button_back, pattern="^back_"))

    # Обработчики для новых кнопок услуг
    application.add_handler(CallbackQueryHandler(button_service_health_programs, pattern="^service_health_programs$"))
    application.add_handler(CallbackQueryHandler(button_service_diagnostics, pattern="^service_diagnostics$"))
    application.add_handler(CallbackQueryHandler(button_service_what_we_treat, pattern="^service_what_we_treat$"))

    # Обработчики для диагностики
    application.add_handler(CallbackQueryHandler(button_diagnostic, pattern="^diagnostic_"))
    application.add_handler(CallbackQueryHandler(button_diagnostic_detail, pattern="^detail_diagnostic_"))

    # Обработчики для программ здоровья
    application.add_handler(CallbackQueryHandler(button_health_program, pattern="^health_program_"))
    application.add_handler(CallbackQueryHandler(button_health_program_detail, pattern="^detail_health_program_"))

    # Обработчики для раздела "Чем мы лечим"
    application.add_handler(CallbackQueryHandler(button_treatment, pattern="^treatment_"))
    application.add_handler(CallbackQueryHandler(button_treatment_detail, pattern="^detail_treatment_"))

    # Обработчики текстовых сообщений из опроса
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, survey_response))

    # Обработчики для кнопок расширенного опроса
    application.add_handler(MessageHandler(filters.Regex("^Наш сайт$"), website))
    application.add_handler(MessageHandler(filters.Regex("^Контакты$"), contacts))
    application.add_handler(MessageHandler(filters.Regex("^Оставить отзыв$"), leave_review))
    application.add_handler(MessageHandler(filters.Regex("^Записаться$"), appointment))
    application.add_handler(MessageHandler(filters.Regex("^Главное меню$"), main_menu_from_survey))
    application.add_handler(MessageHandler(filters.Regex("^Стоимость услуг$"), cost_services))
    application.add_handler(MessageHandler(filters.Regex("^Лекции и курсы$"), lectures_courses))
    application.add_handler(MessageHandler(filters.Regex("^Вопросы по лечению и консультации$"), questions_consultation))

    appointment_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_appointment, pattern="^appointment_")
        ],
        states={
            DAY: [
                CallbackQueryHandler(select_day, pattern="^day_"),
                CallbackQueryHandler(handle_back_from_appointment, pattern="^back_appointment")
            ],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
                CallbackQueryHandler(handle_back_from_appointment, pattern="^back_appointment")
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
                CallbackQueryHandler(handle_back_from_appointment, pattern="^back_appointment")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_appointment),
            MessageHandler(filters.ALL, cancel_appointment)
        ],
        per_message=False
    )
    application.add_handler(appointment_conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
