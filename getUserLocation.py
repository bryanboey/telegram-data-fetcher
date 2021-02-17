import csv
from math import cos, asin, sqrt
import logging
import random
import gspread
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
    Update,
    KeyboardButton
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

gc = gspread.service_account('json key')
sht1 = gc.open_by_key('sheet id')

CHOOSING, SELECTED_BUDGET, SELECTED_KEYWORD, SELECTED_LOCATION = range(4)

def hungry(update: Update, context: CallbackContext) -> None:
    global budget_input
    global keyword_input
    global user_lat
    global user_lon
    budget_input = None
    keyword_input = None
    user_lat = None
    user_lon = None
    user = update.message.from_user
    logger.info("User %s started output selection conversation.", user.first_name)
    keyboard = [
        [
            InlineKeyboardButton("By Budget", callback_data='type_budget'),
            InlineKeyboardButton("By Keyword", callback_data='type_keyword'),
        ],
        [InlineKeyboardButton("Nearby Me", callback_data='type_location'),
         InlineKeyboardButton("No Preference", callback_data='type_none')],
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

    budget_keyboard = [['<$10', '$10 - $25', '$25 - $50', ],
                       ['$50 - $100', '>$100']]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please select your budget or type /cancel to stop.',
                             reply_markup=ReplyKeyboardMarkup(budget_keyboard,
                                                              one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_BUDGET

def type_keyword(update: Update, context: CallbackContext):
    button(update, context)

    keyword_keyboard = [['Local', 'Cafe', 'Bar', ],
                        ['Japanese', 'Korean', 'Italian']]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please select your food preference or type /cancel to stop.',
                             reply_markup=ReplyKeyboardMarkup(keyword_keyboard,
                                                              one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_KEYWORD

def type_none(update: Update, context: CallbackContext):
    button(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Anything will do? Cool!'
                             )

    return randomSample(update, context)

def type_location(update: Update, context: CallbackContext):

    location_keyboard = KeyboardButton(text="Share My Location", request_location=True)

    keyboard1 = [[location_keyboard]]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please send location', reply_markup=ReplyKeyboardMarkup(keyboard1,
                                                             one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_LOCATION

#### selected option user input logging
def budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global budget_input
    budget_input = update.message.text
    logger.info("User %s entered budget: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'No problem! I gotchu fam.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return randomSample(update, context)

def keyword(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global keyword_input
    keyword_input = update.message.text
    logger.info("User %s entered keyword: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'Sure thing! Let me see..',
        reply_markup=ReplyKeyboardRemove(),
    )

    return randomSample(update, context)

def getLocation(update, context):
    user = update.message
    global user_lat
    global user_lon
    user_lat = user.location.latitude
    user_lon = user.location.longitude
    logger.info("User %s entered latitude and longitude: %s, %s", user.chat.first_name, user.location.latitude, user.location.longitude)
    update.message.reply_text(
        'Sure thing! Let me see..',
        reply_markup=ReplyKeyboardRemove(),
    )
    return filterLocation(update, context)

#### Filters and generating Sample to random - can add more filters with functions and would work as multilayered
def filterBudget(item) -> bool:
    if budget_input is None:
        return True
    return budget_input == item['Price']

def filterKeyword(item) -> bool:
    if keyword_input is None:
        return True
    if keyword_input.lower() in item['Tags']:
        return True
    return False

def filterEverything(item) -> bool:
    return filterBudget(item) and filterKeyword(item)

def randomSample(update, context):
    worksheet = sht1.worksheet("masterList")
    pty_dictList = worksheet.get_all_records()
    filtered = list(filter(filterEverything, pty_dictList))
    sample = random.sample(filtered, min(len(filtered), 5))
    if len(sample) == 0:  # if there's no entries found
        update.message.reply_text('Sorry, I couldn\'t find anything. Please /start again.')
        return ConversationHandler.END

    if len(sample) != 0:  # entries found
        text = 'I have randomly selected the following:\n'
        for i in range(len(sample)):
            text = text + \
                        '\n*' + str(i + 1) + '. ' + sample[i]["Name"] + \
                        '*\n' + sample[i]["Price"] + \
                        '\n' + '[' + sample[i]["Address"] + ']' + '(' + sample[i]["Maplink"] + ')' + '\n'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                 parse_mode=ParseMode.MARKDOWN,
                                 disable_web_page_preview=True)
    logger.info("Conversation with User has ended.")
    return ConversationHandler.END

R = 6371000 #radius of the Earth in m
def distance(lon1, lat1, lon2, lat2):
    x = (lon2 - lon1) * cos(0.5*(lat2+lat1))
    y = (lat2 - lat1)
    return R * sqrt( x*x + y*y )

def filterLocation(update, context):
    worksheet = sht1.worksheet("masterList")
    pty_dictList = worksheet.get_all_records(empty2zero=True)
    results = sorted(pty_dictList, key=lambda i: distance(i["lat"], i["lon"], user_lat, user_lon))

    if len(results) == 0:  # if there's no entries found
        update.message.reply_text('Sorry, I couldn\'t find anything. Please /start again.')
        return ConversationHandler.END

    if len(results) != 0:  # entries found
        text = 'In the area, you have the following:\n'
        for i in range(len(results[:5])):
            text = text + \
                    '\n*' + str(i + 1) + '. ' + results[i]["Name"] + \
                    '*\n' + results[i]["Price"] + \
                    '\n' + '[' + results[i]["Address"] + ']' + '(' + results[i]["Maplink"] + ')' + '\n'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                             parse_mode=ParseMode.MARKDOWN,
                             disable_web_page_preview=True)
    logger.info("Conversation with User has ended.")
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
    updater = Updater("token")

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('hungry', hungry)],
        states={
            CHOOSING: [
                CallbackQueryHandler(type_budget, pattern='^type_budget$'),
                CallbackQueryHandler(type_keyword, pattern='^type_keyword$'),
                CallbackQueryHandler(type_none, pattern='^type_none$'),
                CallbackQueryHandler(type_location, pattern='^type_location$'),
            ],
            SELECTED_BUDGET: [
                MessageHandler(Filters.text & ~Filters.command, budget),
                CommandHandler('cancel', cancel)
            ],
            SELECTED_KEYWORD: [
                MessageHandler(Filters.text & ~Filters.command, keyword),
                CommandHandler('cancel', cancel)
            ],
            SELECTED_LOCATION: [
                MessageHandler(Filters.location & ~Filters.command, getLocation),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()

