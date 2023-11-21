import logging

import poem_creator as pc
import conf
import telegram
print(telegram.__file__)
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, File
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# logger = logging.getLogger(__name__)


def function_name(update, context):
    global waiting_for_response
    if waiting_for_response:
        pass


FILE, RHYME, ININFO, YN = range(4)

file, rhyme, in_info, y_n = '', '', '', ''


async def command_start(update, context):
    '''
        Функция инициации и приветствия.
        Здесь же отправляется сообщение, подразумевающее выбор книги/фильма из 3х вариантов пользователем.
    '''
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Hi there! I'm Bot Rifmoplet!\n\n"
                                        "I can create poems based on \n  ☆ mainstream books & films,\n  ☆ the word "
                                        "and metre that you send\n\nᕙ( ͡° ͜ʖ ͡°)ᕗ")

    reply_keyboard = [['Harry Potter', 'The Godfather', 'Twilight']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Let's start with a choice of the theme: \n\n☆ Harry Potter and the Prisoner of Azkaban\n"
        "☆ The Godfather\n"
        "☆ Twilight",
        reply_markup=markup_key,
    )
    return FILE


async def main_theme(update, context):
    '''
        Функция принимает на вход книгу/фильм, выбранный пользователем.
        Здесь же отправляется сообщение, подразумевающее выбор рифмо_схемы из 3х вариантов пользователем.
    '''
    chat_id = update.message.chat_id
    user = update.message.from_user
    global file
    file = update.message.text
    reply_keyboard = [['AABB', 'ABAB', 'ABBA']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_photo(chat_id, 'rhyme.jpg', caption="Those are the rhyme schemes you can choose from!")
    await update.message.reply_text(
        'Which one do you like?\n\n',
        reply_markup=markup_key,
    )
    return RHYME


async def rhyme_schemes(update, context):
    '''
        Функция принимает на вход рифмо_схему, выбранную пользователем.
        Здесь же отправляется сообщение, подразумевающее ввод данных пользователем с клавиатуры.
    '''
    chat_id = update.message.chat_id
    user = update.message.from_user
    global rhyme_scheme
    rhyme_scheme = update.message.text
    await update.message.reply_text("Now send me\n  ☆ the word,\n  ☆ the index of its line (A or B),\n  ☆ min, max number of syllables "
                                    "in line, \nseparated by a space\n\n ~~ For example, day A 5,10"
                                    )
    return ININFO

async def info(update, context):
    '''
        Функция принимает на вход строку, введенную пользователем, и обрабатывает ее.
        Здесь же предлагается создать по тем же исходным данным новое стихотворение.
    '''
    chat_id = update.message.chat_id
    user = update.message.from_user
    global in_info
    in_info = update.message.text
    word, sel_ab, syllable_count = in_info.split()
    syllable_count = syllable_count.split(',')
    data = {'Harry Potter': 'hp.db', 'The Godfather': 'gf.db', 'Twilight': 'tw.db'}
    global db
    db = data[file]
    global notsel_ab
    if sel_ab == 'A':
        notsel_ab = 'B'
    else:
        notsel_ab = 'A'
    await update.message.reply_text('Got it! \nYour poem is coming in an instant...')
    final_poem = pc.poem_creation(db, word, rhyme_scheme, sel_ab, notsel_ab, syllable_count)
    await update.message.reply_text('Here it is :)\n\n' + final_poem + '\n' + 6 * '-' + '\nBy BotRifmoplet')
    reply_keyboard = [['YES!', 'NO!']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        'Do you want another one? \n\n',
        reply_markup=markup_key,
    )
    return YN

async def chance_to_stop(update, context):
    '''
        Функция принимает на вход ответ пользователя.
        Если он положительный, выводит еще одно стихотворение.
    '''
    chat_id = update.message.chat_id
    user = update.message.from_user
    global y_n
    y_n = update.message.text
    if y_n == 'YES!':
        word, sel_ab, syllable_count = in_info.split()
        syllable_count = syllable_count.split(',')
        final_poem = pc.poem_creation(db, word, rhyme_scheme, sel_ab, notsel_ab, syllable_count)
        await update.message.reply_text('Here it is :)\n\n' + final_poem + '\n' + 6 * '-' + '\nBy BotRifmoplet')
    await update.message.reply_text('Hope you enjoyed it!\nTo continue press /start')
    return ConversationHandler.END

async def cancel(update, context):
    user = update.message.from_user
    await update.message.reply_text(
        "Not being poetic today? It's ok\n"
        "Text me any time!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def help_command(update, context):
    await update.message.reply_text(
        'To run this bot, type /start\n'
        'To stop me, type /cancel'
    )


async def ans(update, context):
    message = "Sorry, I don't get it :с\n Try /start or /help"
    await update.message.reply_text(message)


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', command_start)],
        # start
        states={
            FILE: [MessageHandler(filters.Regex('^(Harry Potter|The Godfather|Twilight)$'), main_theme)],
            RHYME: [MessageHandler(filters.Regex('^(AABB|ABAB|ABBA)$'), rhyme_schemes)],
            ININFO: [MessageHandler(filters.TEXT & (~filters.COMMAND), info)],
            YN: [MessageHandler(filters.Regex('^(YES!|NO!)$'), chance_to_stop)]
        },
        # exit
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(CommandHandler('help', help_command))
    # application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)

    application.add_handler(MessageHandler(filters.COMMAND, ans))

    application.run_polling()


if __name__ == '__main__':
    TOKEN = conf.TOKEN
    main()
