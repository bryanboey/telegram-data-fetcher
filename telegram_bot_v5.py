import logging
import random
import gspread
from math import cos, asin, sqrt
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
    KeyboardButton,
    Update
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

gc = gspread.service_account('json key')
sht1 = gc.open_by_key('spread id')

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm Botohyao, an information grabber!"
                                                                    "\n\n*Command list:*"
                                                                    "\n/hungry - randomly picks 5 places based on preference"
                                                                    "\n/masterlist - lists all food places"
                                                                    "\n/tags - lists all available keywords to search"
                                                                    "\n.filter <keyword> - searches all places with <keyword>"
                                                                    "\n/moreinfo - credits and more information",
                             parse_mode=ParseMode.MARKDOWN)

    logger.info("User %s used command: /start", update.message.from_user.first_name)
    return

def moreinfo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='\n\nThis is a private list of food places by my girlfriend and myself we wish to visit. '
                                                                    'I created this bot to serve as an assistant to retrieve specific data easily '
                                                                    'and quickly as opposed to opening and looking through a spreadsheet that\'s tiny on our phones.'
                                                                    '\n\nCurrently working to improve user-friendliness of functions '
                                                                    'and curating more places to include in the list.'
                                                                    '\n\n<a href="https://github.com/bryanboey/csv-telegram">My GitHub</a>'                                     
                                                                    '\n\nCredits:'
                                                                    '\nModules by python-telegram-bot'
                                                                    '\nBig thanks to Cameron & Jonathan for the guidance. 😊',
                             parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    logger.info("User %s used command: /moreinfo", update.message.from_user.first_name)
    return

# Start USER_SELECTION_PROCESS
CHOOSING, SELECTED_BUDGET, SELECTED_KEYWORD, SELECTED_LOCATION = range(4)

# Conversation command trigger
def hungry(update: Update, context: CallbackContext) -> None:
    global budget_input
    global keyword_input
    global region_input
    global user_lat
    global user_lon
    budget_input = None
    keyword_input = None
    region_input = None
    user_lat = None
    user_lon = None

    keyboard = [
        [
            InlineKeyboardButton("By Budget", callback_data='type_budget'),
            InlineKeyboardButton("By Keyword", callback_data='type_keyword'),
        ],
        [InlineKeyboardButton("By Location", callback_data='type_location'),
         InlineKeyboardButton("No Preference", callback_data='type_none')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please select an option if you have a preference.', reply_markup=reply_markup)

    logger.info("User %s started output selection conversation.", update.message.from_user.first_name)
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

def type_location(update: Update, context: CallbackContext):
    button(update, context)

    share_keyboard = KeyboardButton(text="Share My Location", request_location=True)
    keyboard1 = [[share_keyboard, ],
                 ['West', 'Central', 'East', ],
                 ['North', 'North-East']]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Please select a region or share your location.', reply_markup=ReplyKeyboardMarkup(keyboard1,
                                                             one_time_keyboard=True, resize_keyboard=True),
                             )

    return SELECTED_LOCATION

def type_none(update: Update, context: CallbackContext):
    button(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    'Anything will do? Cool!'
                             )

    return randomSample(update, context)

#### selected option user input logging
def budget(update: Update, context: CallbackContext) -> int:
    global budget_input
    budget_input = update.message.text
    update.message.reply_text(
        'No problemo! I gotchu fam.',
        reply_markup=ReplyKeyboardRemove(),
    )

    logger.info("User %s entered budget: %s", update.message.from_user.first_name, update.message.text)
    return randomSample(update, context)

def keyword(update: Update, context: CallbackContext) -> int:
    global keyword_input
    keyword_input = update.message.text
    update.message.reply_text(
        'Sure thing! Let me see..',
        reply_markup=ReplyKeyboardRemove(),
    )

    logger.info("User %s entered keyword: %s", update.message.from_user.first_name, update.message.text)
    return randomSample(update, context)

def getLocation(update, context):
    global region_input
    region_input = update.message.text
    update.message.reply_text(
        'Alrighty then!',
        reply_markup=ReplyKeyboardRemove(),
    )

    logger.info("User %s entered region: %s", update.message.from_user.first_name, update.message.text)
    return randomSample(update, context)

def getNearby(update, context):
    user = update.message
    global user_lat
    global user_lon
    user_lat = user.location.latitude
    user_lon = user.location.longitude
    update.message.reply_text(
        'Got it! Looking around..',
        reply_markup=ReplyKeyboardRemove(),
    )

    logger.info("User %s shared location. Latitude: %s, Longitude: %s",
                user.chat.first_name, user.location.latitude, user.location.longitude)
    return randomSample(update, context)

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

R = 6371000 #radius of the Earth in m
def distance(lon1, lat1, lon2, lat2):
    x = (lon2 - lon1) * cos(0.5*(lat2+lat1))
    y = (lat2 - lat1)
    return R * sqrt( x*x + y*y )

def filterNearby(item) -> bool:
    if None in {user_lat, user_lon}:
        return True
    if distance(item["lat"], item["lon"], user_lat, user_lon) < 100000:
        return True
    return False

def filterRegion(item) -> bool:
    if region_input is None:
        return True
    return region_input == item['Region']

def filterEverything(item) -> bool:
    return filterBudget(item) and filterKeyword(item) and filterRegion(item) and filterNearby(item)

##### Result output
def randomSample(update, context):
    print(budget_input, keyword_input, region_input, user_lat, user_lon)
    filtered = list(filter(filterEverything, e2z_list))
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
        print(text)
    logger.info("Conversation with User has ended.")
    return ConversationHandler.END

# fallback request to end conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    logger.info("User %s canceled the conversation.", update.message.from_user.first_name)
    return ConversationHandler.END

# masterList command line
def masterList(update, context):
    masterList_text = "Available places are: \n\n"
    index = 1
    for item in e2z_list:
        masterList_text = masterList_text + str(index) + ". " + item['Name'] + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=masterList_text)

    logger.info("User %s used command: /masterlist", update.message.from_user.first_name)
    return

#filter search by !<keywords>
def filter_search(update, context):
    user_input = update.message.text #i.e ".tag <tag>
    keyword = str(user_input[8:]) #because user_input now includes "!tag", to search without prefix = [5:]

    text = "Available places for '" + keyword + "' are: \n\n"
    index = 1
    for item in e2z_list:
        if keyword in item['Tags']:
            text = text + str(index) + ". " + item['Name'] + "\n"
            index = index + 1

    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    logger.info("User %s used filter_search command: %s", update.message.from_user.first_name, keyword)
    return

#output list of all available <tags> to search
def tags(update, context):
    tagSet = set()
    for item in e2z_list:
        for i in item['Tags'].split(", "):
            tagSet.add(i)
    message_to_user = "Available keywords to search are: \n\n"
    index = 1
    for item in sorted(tagSet):
        message_to_user = message_to_user + str(index) + ". " + item.capitalize() + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_user)

    logger.info("User %s used command: /tags", update.message.from_user.first_name)
    return

# for unknown commands entered by user
def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

    logger.info("User %s typed an unknown command: %s", update.message.from_user.first_name, update.message.text)
    return

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("token")

    worksheet = sht1.worksheet("masterList")
    global e2z_list
    e2z_list = worksheet.get_all_records(empty2zero=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("moreinfo", moreinfo))

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
                MessageHandler(Filters.text & ~Filters.command, getLocation),
                MessageHandler(Filters.location & ~Filters.command, getNearby),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("masterlist", masterList))
    dispatcher.add_handler(PrefixHandler(['!', '.'], "filter", filter_search))
    dispatcher.add_handler(CommandHandler("tags", tags))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
