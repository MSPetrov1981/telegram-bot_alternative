import logging
import os

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
    AWAITING_COMMENT,
    AWAITING_NAME,
    AWAITING_PHONE,
    AWAITING_SERVICE,
    appointment_request,
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
    cancel_appointment_form,
    contacts,
    cost_services,
    directions_main,
    handle_survey_global,
    leave_review,
    lectures_courses,
    main_menu_from_survey,
    process_appointment_input,
    questions_consultation,
    services_main,
    specialists_main,
    start,
    website,
    website_main,
)

load_dotenv()
BOT_TOKEN1 = os.getenv("BOT_TOKEN1")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception: %s", context.error, exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте еще раз.")


def main():
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0)
    application = Application.builder().token(BOT_TOKEN1).request(request).build()
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler("start", start))

    # ConversationHandler для формы записи с возможностью отмены
    appointment_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Записаться$"), appointment_request),
            CallbackQueryHandler(button_appointment, pattern="^appointment_")
        ],
        states={
            AWAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment_input),
                CommandHandler("cancel", cancel_appointment_form)
            ],
            AWAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment_input),
                CommandHandler("cancel", cancel_appointment_form)
            ],
            AWAITING_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment_input),
                CommandHandler("cancel", cancel_appointment_form)
            ],
            AWAITING_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appointment_input),
                CommandHandler("cancel", cancel_appointment_form)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_appointment_form),
            MessageHandler(filters.Regex("^Отмена$"), cancel_appointment_form)
        ],
    )
    application.add_handler(appointment_conv_handler)

    # Inline-обработчики
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
    application.add_handler(CallbackQueryHandler(button_service_health_programs, pattern="^service_health_programs$"))
    application.add_handler(CallbackQueryHandler(button_service_diagnostics, pattern="^service_diagnostics$"))
    application.add_handler(CallbackQueryHandler(button_service_what_we_treat, pattern="^service_what_we_treat$"))
    application.add_handler(CallbackQueryHandler(button_diagnostic, pattern="^diagnostic_"))
    application.add_handler(CallbackQueryHandler(button_diagnostic_detail, pattern="^detail_diagnostic_"))
    application.add_handler(CallbackQueryHandler(button_health_program, pattern="^health_program_"))
    application.add_handler(CallbackQueryHandler(button_health_program_detail, pattern="^detail_health_program_"))
    application.add_handler(CallbackQueryHandler(button_treatment, pattern="^treatment_"))
    application.add_handler(CallbackQueryHandler(button_treatment_detail, pattern="^detail_treatment_"))
    application.add_handler(CallbackQueryHandler(button_back, pattern="^back_"))

    # Глобальный обработчик текста
    async def global_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("appointment_step") is not None:
            return
        text = update.message.text
        if text == "Специалисты":
            await specialists_main(update, context)
        elif text == "Услуги":
            await services_main(update, context)
        elif text == "Направления":
            await directions_main(update, context)
        elif text == "Наш сайт":
            await website_main(update, context)
        elif text == "Контакты":
            await contacts(update, context)
        elif text == "Оставить отзыв":
            await leave_review(update, context)
        elif text == "Главное меню":
            await main_menu_from_survey(update, context)
        elif text == "Стоимость услуг":
            await cost_services(update, context)
        elif text == "Лекции и курсы":
            await lectures_courses(update, context)
        elif text == "Вопросы по лечению и консультации":
            await questions_consultation(update, context)
        elif text == "Наш сайт" in text:
            await website(update, context)
        else:
            await handle_survey_global(update, context)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_text_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
