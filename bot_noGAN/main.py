from telegram_bot.model import StyleTransferModel
#from telegram_token import token
from io import BytesIO

from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram.ext.dispatcher import run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

# В бейзлайне пример того, как мы можем обрабатывать две картинки, пришедшие от пользователя.

model = StyleTransferModel()
first_image_file = {}
PHOTO = 0

def send_prediction_on_photo(update, context):
    chat_id = update.message.chat_id
    print("Got image from {}".format(chat_id))
    update.message.reply_text('Принял фото')

    image_file = update.message.photo[-1].get_file()

    if chat_id in first_image_file:
        # первая картинка, которая к нам пришла станет content image, а вторая style image
        content_image_stream = BytesIO()
        first_image_file[chat_id].download(out=content_image_stream)
        del first_image_file[chat_id]

        style_image_stream = BytesIO()
        image_file.download(out=style_image_stream)
        del image_file

        output = model.transfer_style(content_image_stream, style_image_stream)

        # теперь отправим назад фото
        output_stream = BytesIO()
        output.save(output_stream, format='PNG')
        output_stream.seek(0)
        update.message.reply_photo(photo=output_stream)
        print("Sent Photo to user")
        return ConversationHandler.END
    else:
        first_image_file[chat_id] = image_file
        return PHOTO



def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

    return PHOTO

def cancel(update, context):
    update.message.reply_text('Bye! I hope we can talk again some day.',)
    return ConversationHandler.END


if __name__ == '__main__':
    token = "___"
    # Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    updater = Updater(token, use_context=True,
                      request_kwargs={'proxy_url': 'socks5h://163.172.152.192:1080'})
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            PHOTO: [MessageHandler(Filters.photo, send_prediction_on_photo), ],

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    start_button = InlineKeyboardButton('start')
    InlineKeyboardMarkup(start_button)

    dp.add_handler(conv_handler)
    run_async(conv_handler)
    updater.start_polling()

    updater.idle()
