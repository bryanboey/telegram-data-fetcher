import logging
import random
import gspread
from math import cos, asin, sqrt
from typing import Dict
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

gc = gspread.service_account('xxxxx')
sht1 = gc.open_by_key('xxxxx')

# main body
SELECT_ACTION, SELECT_FILTER, SELECT_FILTER_OPTION = range(3)
# filter options input
LOCATION_INPUT = range(3,4)
KEYWORD_INPUT = range(4,5)

BUDGET, CURRENT_SELECTED_FILTER = range(5,7)
START_OVER = range(7,8)

STOPPING = range(8,9)
END = ConversationHandler.END

# Conversation command trigger
def start(update: Update, context: CallbackContext) -> None:


    text = (
        "Search function initiated. Add filters to set search criteria. "
        "Once you have entered your desired parameters click 'Search' button."
        "To cancel, type /stop."
    )

    keyboard = [
        [
            InlineKeyboardButton("Add Filters", callback_data='ADD_FILTER'),
            InlineKeyboardButton("Show Filters", callback_data='SHOWING'),
        ],
        [
            InlineKeyboardButton("Search", callback_data='SEARCH'),
            InlineKeyboardButton("Exit", callback_data='END')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        user_data = context.user_data
        user_data[BUDGET] = None
        user_data['KEYWORD'] = None
        user_data['LOCATION'] = None
        user_data['lat_input'] = None
        user_data['lon_input'] = None
        update.message.reply_text(text=text, reply_markup=reply_markup)
        logger.info("User %s started output selection conversation.", update.message.from_user.first_name)

    context.user_data[START_OVER] = False
    return SELECT_ACTION

def add_filter(update, context):
    text = (
        "Select the criteria you wish to set."
    )

    keyboard = [
        [
            InlineKeyboardButton("Budget", callback_data=str(BUDGET)),
            InlineKeyboardButton("Keyword", callback_data='KEYWORD'),
        ],
        [
            InlineKeyboardButton("Location", callback_data='LOCATION'),
            InlineKeyboardButton("Back", callback_data='END')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get(START_OVER):
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    else:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return SELECT_FILTER

def select_filter_option(update, context):
    update.callback_query.answer()
    user_selected_filter = update.callback_query.data
    print('USER SELECTED FILTER', user_selected_filter)
    context.user_data[CURRENT_SELECTED_FILTER] = user_selected_filter
    print('this is user_data', context.user_data)

    if user_selected_filter == str(BUDGET):
        budget_options(update, context)
    if user_selected_filter == 'KEYWORD':
        keyword_options(update, context)
    if user_selected_filter == 'LOCATION':
        location_options(update, context)

    return SELECT_FILTER_OPTION

def budget_options(update, context):
    text = (
        "Enter budget or select 'Back' if you don't have one."
    )

    budget_keyboard = [
        [
            InlineKeyboardButton("<$10", callback_data='<$10'),
            InlineKeyboardButton("$10 - $25", callback_data='$10 - $25'),
            InlineKeyboardButton("$25 - $50", callback_data='$25 - $50'),
        ],
        [
            InlineKeyboardButton("$50 - $100", callback_data='$50 - $100'),
            InlineKeyboardButton(">$100", callback_data='>$100'),
            InlineKeyboardButton("Back", callback_data="END"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(budget_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def keyword_options(update: Update, context: CallbackContext):
    text = (
        "Keyword search:\n"
        "Select a keyword using the buttons or if you're feeling lucky "
        "select 'Manual input' to search a keyword."
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
            InlineKeyboardButton("Something 1", callback_data="Something1"),
            InlineKeyboardButton("Manual Input", callback_data="MANUAL"),
            InlineKeyboardButton("Back", callback_data="END"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyword_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def requestKeyword(update: Update, context: CallbackContext):
    text = 'Alright, kindly enter a keyword ' 'for example, "coffee", "german".'

    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return KEYWORD_INPUT

def getKeyword(update, context):
    text = update.message.text
    user_data = context.user_data
    user_data['KEYWORD'] = text

    context.user_data[START_OVER] = True
    add_filter(update, context)
    print(user_data)
    return END

def location_options(update: Update, context: CallbackContext):
    text = (
        "Please select a region or share your location."
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
            InlineKeyboardButton("Share my Location", callback_data="Nearby"),
            InlineKeyboardButton("Back", callback_data="END"),
        ],
    ]
    #share_keyboard = KeyboardButton(text="Share My Location", request_location=True)
    reply_markup = InlineKeyboardMarkup(location_keyboard)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return

def requestNearby(update, context):
    text = "Please click reply button to share your location"
    share_keyboard = KeyboardButton(text="Share My Location", request_location=True)
    keyboard = [[share_keyboard]]
    context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                             reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))

    return LOCATION_INPUT

def getNearby(update, context):
    lat_input = update.message.location.latitude
    lon_input = update.message.location.longitude
    user_data = context.user_data
    user_data['LAT_INPUT'] = lat_input
    user_data['LON_INPUT'] = lon_input
    user_data['LOCATION'] = 'Near your location'
    print(user_data['LAT_INPUT'], user_data['LON_INPUT'])

    update.message.reply_text('Got it!', reply_markup=ReplyKeyboardRemove())
    context.user_data[START_OVER] = True
    add_filter(update, context)

    return END

def save_input(update, context) -> str:
    user_data = context.user_data
    user_selected_filter_option = update.callback_query.data
    print(user_selected_filter_option)
    print(user_data[CURRENT_SELECTED_FILTER])
    filter_type = user_data[CURRENT_SELECTED_FILTER]
    user_data[filter_type] = user_selected_filter_option

    del user_data[CURRENT_SELECTED_FILTER]

    add_filter(update, context)
    print(user_data)
    return SELECT_FILTER

def show_user_filters(update, context):
    user_data = context.user_data
    print(context.user_data)
    print('1', context.user_data.get(BUDGET))
    print('budget is ', user_data[BUDGET])
    return SELECT_ACTION

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

##### Main Function
def randomSample(update, context):
    user_data = context.user_data
    print(user_data['BUDGET'], user_data['KEYWORD'], user_data['LOCATION'], user_data['lat_input'], user_data['lon_input'])
    filtered = list(filter(filterEverything, e2z_list))
    sample = random.sample(filtered, min(len(filtered), 5))
    if len(sample) == 0:  # if there's no entries found
        context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, I couldn\'t find anything. Please /start again.')
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

def search_button(update, context):
    return randomSample(update, context)

# end from inlinekeyboard
def end(update: Update, context: CallbackContext) -> int:
    update.callback_query.edit_message_text(
        'Bye! I hope we can talk again some day.')

    logger.info("User canceled the conversation [Main Menu - Exit].")
    return ConversationHandler.END

def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

    return END

# end from within nested conversation
def stop_nested(update: Update, context: CallbackContext) -> None:
    """Completely end conversation from within nested conversation."""
    update.message.reply_text('Okay, bye.')

    return STOPPING

# end add_filter menu and return to main menu
def end_filter_selection(update, context):
    context.user_data[START_OVER] = True
    start(update, context)

    return SELECT_ACTION

# return to add filter menu from filter options menu
def return_add_filter_menu(update, context):
    add_filter(update, context)

    return SELECT_FILTER

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("token")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    worksheet = sht1.worksheet("masterList")
    global e2z_list
    e2z_list = worksheet.get_all_records(empty2zero=True)

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
                CallbackQueryHandler(show_user_filters, pattern='^SHOWING$'),
                CallbackQueryHandler(search_button, pattern='^SEARCH$'),
                CallbackQueryHandler(end, pattern='^END$'),
            ],
            SELECT_FILTER: [
                CallbackQueryHandler(select_filter_option, pattern='^' + str(BUDGET) + '$'),
                CallbackQueryHandler(end_filter_selection, pattern='^END$'),
            ],
            SELECT_FILTER_OPTION: [
                getNearby_conv,
                getKeyword_conv,
                CallbackQueryHandler(save_input, pattern='^(?!' + 'END' + ').*$'),
                CallbackQueryHandler(return_add_filter_menu, pattern='^END$'),
            ]
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(CommandHandler('print', show_user_filters))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
