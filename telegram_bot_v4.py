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

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm Botohyao, an information grabber!"
                                                                    "\n\n*Command list:*"
                                                                    "\n/hungry - randomly picks 5 places based on preference"
                                                                    "\n/masterlist - lists all food places"
                                                                    "\n/tags - lists all available keywords to search"
                                                                    "\n.filter <tag> - searches all places with <tag>"
                                                                    "\n/moreinfo - credits and more information",parse_mode=ParseMode.MARKDOWN)

def moreinfo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="\n\nThis is a private list of food places by my girlfriend and myself we wish to visit. "
                                                                    "I created this bot to serve as an assistant to retrieve specific data easily "
                                                                    "and quickly as opposed to opening and looking through a spreadsheet that's tiny on our phones."
                                                                    "\n\nCurrently working to improve user-friendliness of functions "
                                                                    "and curating more places to include in the list."
                                                                    "\n\nCredits:"
                                                                    "\nModules by python-telegram-bot"
                                                                    "\nBig thanks to Cameron & Jonathan for the guidance. 😊")

# Start USER_SELECTION_PROCESS
CHOOSING, SELECTED_BUDGET, SELECTED_KEYWORD = range(3)

def hungry(update: Update, context: CallbackContext) -> None:
    global budget_input
    global keyword_input
    budget_input = None
    keyword_input = None
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
    button(update, context)

    keyword_keyboard = [['Cafe', 'Hawker', 'Bar', ],
                        ['Japanese', 'Korean', 'Italian']]

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

#### Filters and generating Sample to random - can add more filters with functions and would work as multilayered
def filterBudget(item) -> bool:
    if budget_input is None:
        return True
    return budget_input == item['price']

def filterKeyword(item) -> bool:
    if keyword_input is None:
        return True
    if keyword_input.lower() in item['tags']:
        return True
    return False

def filterEverything(item) -> bool:
    return filterBudget(item) and filterKeyword(item)

def randomSample(update, context):
    with open('pty.csv', 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        filtered = list(filter(filterEverything, reader))
        sample = random.sample(filtered, min(len(filtered), 5))
        if len(sample) == 0:  # if there's no entries found
            update.message.reply_text('Sorry, I couldn\'t find anything. Please /start again.')
            return ConversationHandler.END

        if len(sample) != 0:  # entries found
            text = 'I have randomly selected the following:\n'
            for i in range(len(sample)):
                text = text + \
                            '\n*' + str(i + 1) + '. ' + sample[i]["name"] + \
                            '*\n' + sample[i]["price"] + \
                            '\n' + '[' + sample[i]["address"] + ']' + '(' + sample[i]["maplink"] + ')' + '\n'

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

# masterList command line
def masterList(update, context):
    with open('pty.csv', 'r') as csv_file:
        masterSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:  # this is where all unique tags are put into a set
            for item in row['name'].split(", "):  # removing comma from all strings in 'tags' column
                masterSet.add(item)

    message_to_userMaster = "Available places are: \n\n"
    index = 1
    for item in masterSet:
        message_to_userMaster = message_to_userMaster + str(index) + ". " + item + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_userMaster)

#filter search by !<keywords>
def filter_search(update, context):
    user_input = update.message.text #i.e ".tag <tag>
    keyword = str(user_input[8:]) #because user_input now includes "!tag", to search without prefix = [5:]
    output = ""
    with open('pty.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            if keyword in row['tags']:
                output = output + row['name'] + "\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text="For " + user_input[8:] + ", I have found:" + "\n\n" + output)

#output list of all available <tags> to search
def tags(update, context):
    with open('pty.csv', 'r') as csv_file:
        tagSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            for item in row['tags'].split(", "):
                tagSet.add(item)

    message_to_user = "Available keywords to search are: \n\n"
    index = 1
    for item in tagSet:
        message_to_user = message_to_user + str(index) + ". " + item.capitalize() + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_user)

# for unknown commands entered by user
def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("TOKEN")

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
                CallbackQueryHandler(randomSample, pattern='^type_none$'),
            ],
            SELECTED_BUDGET: [
                MessageHandler(Filters.text & ~Filters.command, budget),
                CommandHandler('cancel', cancel)
            ],
            SELECTED_KEYWORD: [
                MessageHandler(Filters.text & ~Filters.command, keyword),
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
