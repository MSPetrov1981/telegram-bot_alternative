import logging
import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Update
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
    AWAITING_COMMENT, AWAITING_NAME, AWAITING_PHONE, AWAITING_SERVICE,
    appointment_request, button_appointment, button_back, button_diagnostic,
    button_diagnostic_detail, button_direction, button_direction_detail,
    button_direction_more_detail, button_doctor, button_health_program,
    button_health_program_detail, button_procedure, button_service_diagnostics,
    button_service_doctor, button_service_doctor_detail,
    button_service_health_programs, button_service_procedures,
    button_service_specialists, button_service_what_we_treat,
    button_specialization, button_treatment, button_treatment_detail,
    cancel_appointment_form, contacts, cost_services, directions_main,
    handle_survey_global, leave_review, lectures_courses,
    main_menu_from_survey, process_appointment_input, questions_consultation,
    services_main, specialists_main, start, website, website_main,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN1")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN1 not found in .env")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception: %s", context.error, exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def main() -> None:
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0)
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    application.add_error_handler(error_handler)

    # Основная команда
    application.add_handler(CommandHandler("start", start))

    # ConversationHandler для формы записи
    appointment_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^Записаться$"), appointment_request),
            CallbackQueryHandler(button_appointment, pattern=r"^appointment_"),
        ],
        states={
            state: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment_input),
                CommandHandler("cancel", cancel_appointment_form),
            ]
            for state in (AWAITING_NAME, AWAITING_PHONE, AWAITING_SERVICE, AWAITING_COMMENT)
        },
        fallbacks=[
            CommandHandler("cancel", cancel_appointment_form),
            MessageHandler(filters.Regex(r"^Отмена$"), cancel_appointment_form),
        ],
    )
    application.add_handler(appointment_conv_handler)

    # Inline-обработчики
    inline_patterns = {
        r"^doctor_": button_doctor,
        r"^service_specialists$": button_service_specialists,
        r"^specialization_": button_specialization,
        r"^service_doctor_": button_service_doctor,
        r"^detail_service_doctor_": button_service_doctor_detail,
        r"^service_procedures$": button_service_procedures,
        r"^procedure_": button_procedure,
        r"^direction_": button_direction,
        r"^detail_direction_": button_direction_detail,
        r"^more_detail_direction_": button_direction_more_detail,
        r"^service_health_programs$": button_service_health_programs,
        r"^service_diagnostics$": button_service_diagnostics,
        r"^service_what_we_treat$": button_service_what_we_treat,
        r"^diagnostic_": button_diagnostic,
        r"^detail_diagnostic_": button_diagnostic_detail,
        r"^health_program_": button_health_program,
        r"^detail_health_program_": button_health_program_detail,
        r"^treatment_": button_treatment,
        r"^detail_treatment_": button_treatment_detail,
        r"^back_": button_back,
    }
    for pattern, handler in inline_patterns.items():
        application.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    # Глобальный текстовый обработчик
    async def global_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.user_data.get("appointment_step") is not None:
            return

        text = update.message.text
        menu_map = {
            "Специалисты": specialists_main,
            "Услуги": services_main,
            "Направления": directions_main,
            "Наш сайт": website_main,
            "Контакты": contacts,
            "Оставить отзыв": leave_review,
            "Главное меню": main_menu_from_survey,
            "Стоимость услуг": cost_services,
            "Лекции и курсы": lectures_courses,
            "Вопросы по лечению и консультации": questions_consultation,
        }
        handler = menu_map.get(text)
        if handler:
            await handler(update, context)
        elif "Наш сайт" in text:
            await website(update, context)
        else:
            await handle_survey_global(update, context)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_text_handler))
    logger.info("Bot started polling...")
    application.run_polling()

if __name__ == "__main__":
    main()