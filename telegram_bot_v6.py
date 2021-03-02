import logging
import random
import gspread
import time
from math import radians, cos, sin, asin, sqrt
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

# Google Sheets Service Key and Sheet information
gc = gspread.service_account('json key')
sht1 = gc.open_by_key('sheet id')

# MAIN STATES
SELECT_ACTION, SELECT_FILTER, SELECT_FILTER_OPTION, RESULTS_OUTPUT = range(4)
# UNIQUE STATES
LOCATION_INPUT = range(4,5)
KEYWORD_INPUT = range(5,6)
STOPPING = range(6,7)
BBT_LOCATION = range(7,8)
END = ConversationHandler.END

#   First level conversation
def start(update, context) -> None:
    text0 = "Hello and welcome. I'm Botohyao. Looking for places to eat?"
    text = (
        "You may use 'Add Filters' if you have a preference. If you don't, "
        "you can simply 'Search' without entering any filters. 'Show Filters' "
        "will display all entered filters.\n\n"
        "To cancel, type /stop."
    )

    keyboard = [
        [
            InlineKeyboardButton("Add Filters", callback_data='ADD_FILTER'),
            InlineKeyboardButton("Search", callback_data='SEARCH'),
        ],
        [
            InlineKeyboardButton("Show Filters", callback_data='SHOWING'),
            InlineKeyboardButton("Exit", callback_data='END')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get('START_OVER'):
        logger.info("User [%s] returned to Top level conversation, [Main Menu]",
                    update.callback_query.message.chat.first_name)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        logger.info("User [%s] started Top level conversation, [Main Menu]", update.message.from_user.first_name)
        user_data = context.user_data
        user_data['BUDGET'] = None
        user_data['KEYWORD'] = None
        user_data['LOCATION'] = None
        user_data['LAT_INPUT'] = None
        user_data['LON_INPUT'] = None
        update.message.reply_text(text=text0 + "\n\n" + text, reply_markup=reply_markup)

    context.user_data['START_OVER'] = False
    context.user_data['LEVEL_TWO'] = False
    context.user_data['GET_BBT'] = False
    return SELECT_ACTION

def findMyBbt(update, context):
    context.user_data['GET_BBT'] = True
    logger.info("User [%s] started BBT Conversation", update.message.from_user.first_name)
    return requestNearby(update, context)

##  Second level Conversation
def add_filter(update, context):
    text = (
        "Select the criteria you wish to set. "
        "You may set up to 3 filters to narrow your search. "
        "Once you're satisfied, select 'Back' and use the 'Search' button. "
        "To cancel, type /stop."
    )

    keyboard = [
        [
            InlineKeyboardButton("Budget", callback_data='BUDGET'),
            InlineKeyboardButton("Keyword", callback_data='KEYWORD'),
            InlineKeyboardButton("Location", callback_data='LOCATION'),
        ],
        [
            InlineKeyboardButton("Show Filters", callback_data='SHOWING'),
            InlineKeyboardButton("Back", callback_data='END'),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get('START_OVER'):
        logger.info("User [%s] returned to Second level conversation, [Add Filter]",
                    update.message.chat.first_name)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    else:
        logger.info("User [%s] entered Second level conversation, [Add Filter]",
                    update.callback_query.message.chat.first_name)
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    context.user_data['START_OVER'] = False
    context.user_data['LEVEL_TWO'] = True
    return SELECT_FILTER

def select_filter_option(update, context):
    update.callback_query.answer()
    user_selected_filter = update.callback_query.data
    context.user_data['CURRENT_SELECTED_FILTER'] = user_selected_filter
    logger.info("User [%s] selected [%s] filter.",
                update.callback_query.message.chat.first_name, user_selected_filter)

    if user_selected_filter == 'BUDGET':
        budget_options(update, context)
    if user_selected_filter == 'KEYWORD':
        keyword_options(update, context)
    if user_selected_filter == 'LOCATION':
        location_options(update, context)

    return SELECT_FILTER_OPTION

def showFilters(update, context):
    user_data = context.user_data
    logger.info("User [%s] selected [Show Filters]. "
                "[BUDGET: %s], [KEYWORD: %s], [LOCATION: %s], [LAT, LON: %s, %s]",
                update.callback_query.message.chat.first_name, user_data['BUDGET'],
                user_data['KEYWORD'], user_data['LOCATION'], user_data['LAT_INPUT'], user_data['LON_INPUT'])
    if user_data['LAT_INPUT'] != None:
        location_text = "Nearby your location"
    else:
        location_text = str(user_data['LOCATION'])

    text = (
        "Current entered filters: "
        "\n\n*Budget:* " + str(user_data['BUDGET']) +
        "\n\n*Keyword:* " + str(user_data['KEYWORD']) +
        "\n\n*Location:* " + location_text +
        "\n\nUse 'Clear Filter' to remove all entered filters."
    )

    showfilter_keyboard = [
        [
            InlineKeyboardButton("Clear Filters", callback_data='CLEAR_FILTERS'),
            InlineKeyboardButton("Back", callback_data='END'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(showfilter_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    if context.user_data.get('LEVEL_TWO'):
        return SELECT_FILTER_OPTION
    else:
        return SELECT_FILTER

### Third level conversation
def budget_options(update, context):
    text = (
        "Enter your budget or select 'Back' if you don't have one. To cancel, type /stop."
    )

    budget_keyboard = [
        [
            InlineKeyboardButton("<$10", callback_data="<$10"),
            InlineKeyboardButton("$10 - $25", callback_data="$10 - $25"),
            InlineKeyboardButton("$25 - $50", callback_data="$25 - $50"),
        ],
        [
            InlineKeyboardButton("$50 - $100", callback_data="$50 - $100"),
            InlineKeyboardButton(">$100", callback_data=">$100"),
        ],
        [
            InlineKeyboardButton("Clear", callback_data="None"),
            InlineKeyboardButton("Back", callback_data="END"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(budget_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def keyword_options(update, context):
    text = (
        "Select a keyword using the buttons or if you're feeling lucky "
        "select 'Manual input' to enter a keyword to search. To cancel, type /stop."
    )

    keyword_keyboard = [
        [
            InlineKeyboardButton("Local", callback_data="Local"),
            InlineKeyboardButton("Cafe", callback_data="Cafe"),
            InlineKeyboardButton("Bar", callback_data="Bar"),
        ],
        [
            InlineKeyboardButton("Japanese", callback_data="Japanese"),
            InlineKeyboardButton("Korean", callback_data="Korean"),
            InlineKeyboardButton("Italian", callback_data="Italian"),
        ],
        [
            InlineKeyboardButton("Manual input", callback_data="MANUAL"),
            InlineKeyboardButton("Clear", callback_data="None"),
            InlineKeyboardButton("Back", callback_data="END"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyword_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def location_options(update, context):
    text = (
        "Select a region or share your location to get results nearby you. "
        "To cancel, type /stop."
    )

    location_keyboard = [
        [
            InlineKeyboardButton("West", callback_data="West"),
            InlineKeyboardButton("Central", callback_data="Central"),
            InlineKeyboardButton("East", callback_data="East"),
        ],
        [
            InlineKeyboardButton("North", callback_data="North"),
            InlineKeyboardButton("North-East", callback_data="North-East"),
        ],
        [
            InlineKeyboardButton("Share My Location", callback_data="Nearby"),
        ],
        [
            InlineKeyboardButton("Clear", callback_data="None"),
            InlineKeyboardButton("Back", callback_data="END"),
        ],
    ]
    #share_keyboard = KeyboardButton(text="Share My Location", request_location=True)
    reply_markup = InlineKeyboardMarkup(location_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def clearFilters(update, context):
    user_data = context.user_data
    if user_data['BUDGET'] == user_data['KEYWORD'] == user_data['LOCATION'] == user_data['LAT_INPUT'] == None:
        logger.info("User [%s] selected [Clear Filters]. No filters to clear.",
                    update.callback_query.message.chat.first_name)
        return
    else:
        user_data['BUDGET'] = None
        user_data['KEYWORD'] = None
        user_data['LOCATION'] = None
        user_data['LAT_INPUT'] = None
        user_data['LON_INPUT'] = None
        logger.info("User [%s] selected [Clear Filters]. Filters has been cleared.",
                    update.callback_query.message.chat.first_name)

    return showFilters(update, context)

#### Unique level conversation
def requestKeyword(update, context):
    update.callback_query.message.delete()
    text = 'Alright, kindly enter a keyword ' 'for example, "coffee", "german". To cancel, type /stop.'
    logger.info("User [%s] waiting to enter [Manual Keyword]",
                update.callback_query.message.chat.first_name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return KEYWORD_INPUT

def getKeyword(update, context):
    text = update.message.text
    user_data = context.user_data
    user_data['KEYWORD'] = text
    logger.info("User [%s] entered [Manual KEYWORD: %s]",
                update.message.from_user.first_name, text)

    context.user_data['START_OVER'] = True
    add_filter(update, context)
    return END

def requestNearby(update, context):
    text = "Please click reply button to share your location. To cancel, type /stop."
    share_keyboard = KeyboardButton(text="Share My Location", request_location=True)
    keyboard = [[share_keyboard]]
    context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                             reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    if context.user_data.get('GET_BBT'):
        logger.info("User [%s] waiting to share location",
                    update.message.from_user.first_name)
        return BBT_LOCATION
    else:
        logger.info("User [%s] waiting to share location",
                    update.callback_query.message.chat.first_name)
        update.callback_query.message.delete()
        return LOCATION_INPUT

def getNearby(update, context):
    lat_input = update.message.location.latitude
    lon_input = update.message.location.longitude
    user_data = context.user_data
    user_data['LAT_INPUT'] = lat_input
    user_data['LON_INPUT'] = lon_input
    user_data['LOCATION'] = None
    if context.user_data.get('GET_BBT'):
        logger.info("User [%s] shared location [%s, %s]",
                    update.message.from_user.first_name, lat_input, lon_input)
        update.message.reply_text('Finding you some bubble tea..', reply_markup=ReplyKeyboardRemove())
        return getBbtSample(update, context)
    else:
        logger.info("User [%s] shared location [%s, %s]",
                    update.message.from_user.first_name, lat_input, lon_input)
        update.message.reply_text('Got it!', reply_markup=ReplyKeyboardRemove())
        context.user_data['START_OVER'] = True
        add_filter(update, context)

        return END

# Storing data based on user selections
def save_input(update, context) -> str:
    user_data = context.user_data
    user_selected_filter_option = update.callback_query.data
    filter_type = user_data['CURRENT_SELECTED_FILTER']
    logger.info("User [%s] added [%s: %s]",
                update.callback_query.message.chat.first_name, filter_type, user_selected_filter_option)

    locationOpt = ['West', 'East', 'Central', 'North', 'North-East']
    if user_selected_filter_option in locationOpt:
        user_data['LAT_INPUT'] = None
        user_data['LON_INPUT'] = None
        user_data[filter_type] = user_selected_filter_option
    if user_selected_filter_option == 'None':
        user_data[filter_type] = None
        if filter_type == 'LOCATION':
            user_data['LAT_INPUT'] = None
            user_data['LON_INPUT'] = None
    else:
        user_data[filter_type] = user_selected_filter_option

    del user_data['CURRENT_SELECTED_FILTER']

    add_filter(update, context)
    return SELECT_FILTER

# Haversine Formula
def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)"""
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

##### Main Function
def randomSample(update, context):
    user_data = context.user_data
    # Filters
    def filterBudget(item) -> bool:
        if user_data['BUDGET'] is None:
            return True
        return user_data['BUDGET'] == item['Price']

    def filterKeyword(item) -> bool:
        if user_data['KEYWORD'] is None:
            return True
        if user_data['KEYWORD'].lower() in item['Tags']:
            return True
        return False

    def filterNearby(item) -> bool:
        if None in {user_data['LON_INPUT'], user_data['LAT_INPUT']}:
            return True
        if haversine(item['lon'], item['lat'], user_data['LON_INPUT'], user_data['LAT_INPUT']) < 1.5:
            return True
        return False

    def filterRegion(item) -> bool:
        if user_data['LOCATION'] is None:
            return True
        return user_data['LOCATION'] == item['Region']

    def filterEverything(item) -> bool:
        return filterBudget(item) and filterKeyword(item) and filterRegion(item) and filterNearby(item)

    filtered = list(filter(filterEverything, e2z_list))
    sample = random.sample(filtered, min(len(filtered), 5))
    if len(sample) == 0:  # if there's no entries found
        logger.info("User [%s] yielded no results from entered filters. Conversation ended.",
                    update.callback_query.message.chat.first_name)
        update.callback_query.edit_message_text(text='Sorry, I couldn\'t find anything. Please /start again.')
        return ConversationHandler.END

    if len(sample) != 0:  # entries found
        text = 'I have found the following:\n'
        for i in range(len(sample)):
            print(sample[i]["Name"])
            text = text + \
                   '\n*' + str(i + 1) + '. ' + sample[i]["Name"] + \
                   '*\n' + sample[i]["Price"] + \
                   '\n' + '[' + sample[i]["Address"] + ']' + '(' + sample[i]["Maplink"] + ')' + '\n'

        results_keyboard = [
            [
                InlineKeyboardButton("Search Again", callback_data="SEARCH_AGAIN"),
                InlineKeyboardButton("Restart", callback_data="RESTART"),
                InlineKeyboardButton("Exit", callback_data="END"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(results_keyboard)

        logger.info("User [%s] in [Results State], waiting for selection.",
                    update.callback_query.message.chat.first_name)
        update.callback_query.edit_message_text(text=text,
                                 parse_mode=ParseMode.MARKDOWN,
                                 disable_web_page_preview=True, reply_markup=reply_markup)
    time.sleep(3)
    return RESULTS_OUTPUT

def search_button(update, context):
    user_data = context.user_data
    logger.info("User [%s] selected [Search / Search Again] with parameters "
                "[BUDGET: %s], [KEYWORD: %s], [LOCATION: %s], [LAT, LON: %s, %s]",
                update.callback_query.message.chat.first_name, user_data['BUDGET'],
                user_data['KEYWORD'], user_data['LOCATION'], user_data['LAT_INPUT'], user_data['LON_INPUT'])
    return randomSample(update, context)

def restart_button(update, context):
    logger.info("User [%s] selected [Restart].", update.callback_query.message.chat.first_name)
    user_data = context.user_data
    user_data['BUDGET'] = None
    user_data['KEYWORD'] = None
    user_data['LOCATION'] = None
    user_data['LAT_INPUT'] = None
    user_data['LON_INPUT'] = None

    context.user_data['START_OVER'] = True
    start(update, context)
    return SELECT_ACTION

def getBbtSample(update, context):
    user_data = context.user_data

    def filterNearby1(item) -> bool:
        if None in {user_data['LON_INPUT'], user_data['LAT_INPUT']}:
            return True
        if haversine(item['lon'], item['lat'], user_data['LON_INPUT'], user_data['LAT_INPUT']) < 1.5:
            return True
        return False

    filtered = list(filter(filterNearby1, bbt_lst))
    sample = random.sample(filtered, min(len(filtered), 5))
    if len(sample) == 0:  # if there's no entries found
        logger.info("User [%s] yielded no results. BBT conversation has ended.",
                    update.message.chat.first_name)
        update.message.reply_text(text='Sorry, I couldn\'t find any in the area.')
        return ConversationHandler.END

    if len(sample) != 0:  # entries found
        text = 'I have found the following:\n'
        for i in range(len(sample)):
            print(sample[i]["Name"])
            approx = (
                round(haversine(sample[i]["lon"], sample[i]["lat"],
                                user_data["LON_INPUT"], user_data["LAT_INPUT"]), 3)
            )
            text = text + \
                   '\n<b>' + str(i + 1) + '. ' + sample[i]["Name"] + '\n</b>' + \
                   '<a href="' + sample[i]["Maplink"] + '">' + sample[i]["Address"] + '</a>\n' + \
                   '<i>approx. ' + str(approx) + ' km away</i>\n'

        logger.info("User [%s] BBT conversation has ended.",
                    update.message.chat.first_name)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                 parse_mode=ParseMode.HTML,
                                 disable_web_page_preview=True)

        return END

# Stopping conversation types
def end(update, context) -> int:
    """End Conversation by InlineKeyboard."""
    update.callback_query.edit_message_text(
        'Bye! I hope we can talk again some day.')

    logger.info("User [%s] exited the conversation, [Exit], from [Main Menu / Results State].",
                update.callback_query.message.chat.first_name)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    logger.info("User %s canceled the conversation.", update.message.from_user.first_name)
    return ConversationHandler.END

def stop(update, context) -> None:
    """End Conversation by command, /stop."""
    update.message.reply_text('Okay, bye.')

    return END

def stop_nested(update, context):
    """Completely end conversation from within nested conversation by command, /stop."""
    update.message.reply_text('Okay, bye.')

    return STOPPING

def end_filter_selection(update, context):
    """End Second level conversation, add_filter, and Return to First level conversation."""
    logger.info("User [%s] selected to return to previous menu, [Main Menu], "
                "from [Add Filter / Show Filters]",
                update.callback_query.message.chat.first_name)
    context.user_data['START_OVER'] = True
    start(update, context)

    return SELECT_ACTION

def return_add_filter_menu(update, context):
    """End Third level conversation, filter options menu,
    and Return to Second level conversation, add_filter menu."""
    logger.info("User [%s] selected to return to previous menu, [Add Filter], "
                "from [Filter Option Selection / Show Filters]",
                update.callback_query.message.chat.first_name)
    add_filter(update, context)

    return SELECT_FILTER

# Miscellaneous Commands
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

    logger.info("User [%s] used command, [/tags]", update.message.from_user.first_name)
    return

def commandsList(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="*Command list:*\n"
                                                                    "\n/start - food search function"
                                                                    "\n/findmybbt - search nearby bbt"
                                                                    "\n/tags - lists all available keywords to search"
                                                                    "\n/commands - command list"
                                                                    "\n/moreinfo - credits and more information",
                             parse_mode=ParseMode.MARKDOWN)

    logger.info("User [%s] used command, [/commands]", update.message.from_user.first_name)
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

    logger.info("User [%s] used command, [/moreinfo]", update.message.from_user.first_name)
    return

def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

    logger.info("User [%s] typed an unknown command, [%s]", update.message.from_user.first_name, update.message.text)
    return

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("token")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    worksheet = sht1.worksheet("masterList")
    worksheet2 = sht1.worksheet("Bobber Tea")
    global e2z_list
    e2z_list = worksheet.get_all_records(empty2zero=True)
    global bbt_lst
    bbt_lst = worksheet2.get_all_records(empty2zero=True)

    getNearby_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(requestNearby, pattern='^Nearby$')],
        states={
            LOCATION_INPUT: [
                MessageHandler(Filters.location & ~Filters.command, getNearby),
            ],
        },
        fallbacks=[
            CommandHandler('stop', stop_nested),
            CallbackQueryHandler(return_add_filter_menu, pattern='^END$')
        ],
        map_to_parent={
            END: SELECT_FILTER,
            STOPPING: END,
        },
    )

    getKeyword_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(requestKeyword, pattern='^MANUAL$')],
        states={
            KEYWORD_INPUT: [
                MessageHandler(Filters.text & ~Filters.command, getKeyword),
            ],
        },
        fallbacks=[
            CommandHandler('stop', stop_nested),
            CallbackQueryHandler(return_add_filter_menu, pattern='^END$')
        ],
        map_to_parent={
            END: SELECT_FILTER,
            STOPPING: END,
        },
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [
                CallbackQueryHandler(add_filter, pattern='^ADD_FILTER$'),
                CallbackQueryHandler(showFilters, pattern='^SHOWING$'),
                CallbackQueryHandler(search_button, pattern='^SEARCH$'),
                CallbackQueryHandler(end, pattern='^END$'),
            ],
            SELECT_FILTER: [
                CallbackQueryHandler(showFilters, pattern='^SHOWING$'),
                CallbackQueryHandler(clearFilters, pattern='^CLEAR_FILTERS$'),
                CallbackQueryHandler(select_filter_option, pattern='^BUDGET$|^KEYWORD$|^LOCATION$'),
                CallbackQueryHandler(end_filter_selection, pattern='^END$'),
            ],
            SELECT_FILTER_OPTION: [
                CallbackQueryHandler(clearFilters, pattern='^CLEAR_FILTERS$'),
                getNearby_conv,
                getKeyword_conv,
                CallbackQueryHandler(save_input, pattern='^(?!' + 'END' + ').*$'),
                CallbackQueryHandler(return_add_filter_menu, pattern='^END$'),
            ],
            RESULTS_OUTPUT: [
                CallbackQueryHandler(search_button, pattern='^SEARCH_AGAIN$'),
                CallbackQueryHandler(restart_button, pattern='^RESTART$'),
                CallbackQueryHandler(end, pattern='^END$'),
            ]
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    bbt_conv = ConversationHandler(
        entry_points=[CommandHandler('findmybbt', findMyBbt)],
        states={
            BBT_LOCATION: [
                MessageHandler(Filters.location & ~Filters.command, getNearby),
            ],
        },
        fallbacks=[CommandHandler('stop', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(bbt_conv)
    dispatcher.add_handler(CommandHandler('tags', tags))
    dispatcher.add_handler(CommandHandler('commands', commandsList))
    dispatcher.add_handler(CommandHandler('moreinfo', moreinfo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
