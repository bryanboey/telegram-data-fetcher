import csv
import logging
import random
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    PrefixHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)
from telegram import (
    ParseMode,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Start USER_SELECTION_PROCESS
CHOOSING, SELECTED_BUDGET, SELECTED_KEYWORD = range(3)

def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info("User %s started output selection conversation.", user.first_name)
    keyboard = [
        [
            InlineKeyboardButton("By Budget", callback_data='type_budget'),
            InlineKeyboardButton("By Keyword", callback_data='type_keyword'),
        ],
        [InlineKeyboardButton("No Preference", callback_data='type_none')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please select an option if you have a preference.', reply_markup=reply_markup)

    return CHOOSING

## callback_query data and logging
def button(update, context):
    query = update.callback_query
    query.answer()
    query.message.delete()
    logger.info("[InlineKeyboard] User %s selected %s.", query.message.chat.first_name, query.data)

    return

### selected options function
def type_budget(update, context):
    button(update, context)

    budget_keyboard = [['<$15', '$15 - $25', '$25 - $35', ],
                       ['$35 - $50', '$50 - $100', '>$100']]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please select your budget.',
                             reply_markup=ReplyKeyboardMarkup(budget_keyboard,
                                                              one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_BUDGET

def type_keyword(update: Update, context: CallbackContext):
    #button(update, context)

    keyword_keyboard = [['cafe', 'hawker', 'bar', ],
                        ['japanese', 'korean', 'italian']]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please select your food preference.',
                             reply_markup=ReplyKeyboardMarkup(keyword_keyboard,
                                                              one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_KEYWORD

#### selected option user input logging
def budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global budget_input
    budget_input = update.message.text
    logger.info("User %s entered budget: %s", user.first_name, update.message.text)
    update.message.reply_text('No problem! I got you fam.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return budgetSample(update, context)

def keyword(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global keyword_input
    keyword_input = update.message.text
    logger.info("User %s entered keyword: %s", user.first_name, update.message.text)
    update.message.reply_text('Sure thing! Let me see..',
        reply_markup=ReplyKeyboardRemove(),
    )

    return keywordSample(update, context)


#### generating Sample
def budgetSample(update, context) -> None:
    user = update.message.from_user
    with open('pty.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        set_one = list()
        for row in csv_dict_reader:  #
            if budget_input in row['price']:
                for item in row['name'].split(", "):
                    set_one.append(row)

        if len(set_one) == 0:  # if there's no entries found
            update.message.reply_text('Sorry, I couldn\'t find anything.')
            logger.info("User %s conversation ended", user.first_name)
            return ConversationHandler.END

        if len(set_one) != 0:  # entries found
            return getSampleFromSet(set_one, update, context)

def keywordSample(update, context) -> None:
    user = update.message.from_user
    with open('pty.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        set_one = list()
        for row in csv_dict_reader:  #
            if keyword_input.lower() in row['tags']:
                for item in row['name'].split(", "):
                    set_one.append(row)

        if len(set_one) == 0:  # if there's no entries found
            update.message.reply_text('Sorry, I couldn\'t find anything. Please try again.')
            return type_keyword(update, context)

        if len(set_one) != 0:  # entries found
            return getSampleFromSet(set_one, update, context)

def type_noneSample(update, context) -> None:
    button(update, context)
    query = update.callback_query
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Anything will do? Cool!')

    with open('pty.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        set_one = list()
        for row in csv_dict_reader:  #
            for item in row['name'].split(", "):
                    set_one.append(row)

        random_number_sample = min(len(set_one), 5)
        rt_randomSelect = random.sample(set_one, random_number_sample)

        text = 'I have randomly selected the following:\n'
        for i in range(len(rt_randomSelect)):
            text = text + '\n*' + str(i + 1) + '. ' + rt_randomSelect[i]["name"] + \
                   '*\n' + rt_randomSelect[i]["price"] + \
                   '\n' + '[' + rt_randomSelect[i]["address"] + ']' + '(' + rt_randomSelect[i]["maplink"] + ')' + '\n'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                 parse_mode=ParseMode.MARKDOWN,
                                 disable_web_page_preview=True)
        logger.info("Conversation with User %s has ended.", query.message.chat.first_name)
        return ConversationHandler.END

# retrieving sample from selected user input
def getSampleFromSet(set_one, update, context):
    user = update.message.from_user
    # number of random selection from sample. if sample is less than 5, smaller number will be taken instead
    random_number_sample = min(len(set_one), 5)
    rt_randomSelect = random.sample(set_one, random_number_sample)

    text = 'I have randomly selected the following:\n'
    for i in range(len(rt_randomSelect)):
        text = text + '\n*' + str(i + 1) + '. ' + rt_randomSelect[i]["name"] + \
               '*\n' + rt_randomSelect[i]["price"] + \
               '\n' + '[' + rt_randomSelect[i]["address"] + ']' + '(' + rt_randomSelect[i]["maplink"] + ')' + '\n'

    logger.info("Conversation with User %s has ended.", user.first_name)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return ConversationHandler.END

# fallback request to end conversation
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("TOKEN")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(type_budget, pattern='^type_budget$'),
                CallbackQueryHandler(type_keyword, pattern='^type_keyword$'),
                CallbackQueryHandler(type_noneSample, pattern='^type_none$'),
            ],
            SELECTED_BUDGET: [
                MessageHandler(Filters.text & ~Filters.command, budget),
                CommandHandler('cancel', cancel)
            ],
            SELECTED_KEYWORD: [
                MessageHandler(Filters.text & ~Filters.command, keyword),
                CommandHandler('cancel', cancel)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()





