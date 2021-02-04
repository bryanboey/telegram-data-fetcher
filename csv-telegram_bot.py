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
    Update
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

BUDGET, FOOD_TYPE = range(2)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm Botohyao, an information grabber!"
                                                                    "\n\n*Command list:*"
                                                                    "\n/suggest - randomly picks 5 places based on preference"
                                                                    "\n/masterlist - lists all food places"
                                                                    "\n/tags - lists all available tags to search"
                                                                    "\n.filter <tag> - searches all places with <tag>"
                                                                    "\n/help - credits and more information",parse_mode=ParseMode.MARKDOWN)

start_handler = CommandHandler('start', start)

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="\n\nAt this current version, you may only search/filter 'tags'."
                                                                    "\nType /start to see command list."
                                                                    "\n\nThis is a private list of food places by my girlfriend and myself we wish to visit. "
                                                                    "I created this bot to serve as an assistant to retrieve specific data easily "
                                                                    "and quickly as opposed to opening and looking through a spreadsheet that's tiny on our phones."
                                                                    "\n\nCredits:"
                                                                    "\nModules by python-telegram-bot"
                                                                    "\nBig thanks to Cameron & Jonathan for the guidance. 😊")

help_handler = CommandHandler('help', help)

def suggest(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['<$15', '$15 - $25', '$25 - $35',
                       '$35 - $50', '$50 - $100', '>$100']]

    update.message.reply_text(
        'Do you have a budget? Send /skip if you don\'t have one. Or send /cancel to stop.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return BUDGET


def budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global budget_input
    budget_input = update.message.text
    logger.info("User %s entered budget: %s", user.first_name, update.message.text)
    update.message.reply_text('Okay! What about food type?' ' Or send /skip if you don\'t have a preference.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return FOOD_TYPE


def skip_budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global budget_input
    budget_input = 0
    logger.info("User %s did not enter a budget.", user.first_name)
    update.message.reply_text(
        'Alrighty! Do you have a food preference?' 
        'Or send /skip if you don\'t have a preference.'
    )

    return FOOD_TYPE

def food_type(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global food_type_input
    food_type_input = update.message.text
    logger.info("User %s entered food type: %s", user.first_name, update.message.text)

    return randomer(update, context)


def skip_food_type(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global food_type_input
    food_type_input = 0
    logger.info("User %s did not enter food type.", user.first_name)
    update.message.reply_text(
        'No problemo! Here are some food suggestions:'
    )

    return randomer(update, context)


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def randomer(update, context) -> None:
    with open('patohplz.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        set_one = list()
        for row in csv_dict_reader: #combination of if statements based on user's choice
            if budget_input != '/skip': #choice, skip
                if food_type_input == 0:
                    if budget_input in row['price']:
                        for item in row['name'].split(", "):
                            set_one.append(row)

            if budget_input == '/skip': #skip, choice | skip, skip
                if food_type_input != 0:
                    if food_type_input.lower() in row['tags']:
                        for item in row['name'].split(", "):
                            set_one.append(row)
                if food_type_input == 0:
                    for item in row['name'].split(", "):
                        set_one.append(row)

            if budget_input != '/skip' and food_type_input != 0: #choice, choice
                if food_type_input.lower() in row['tags'] and budget_input in row['price']:
                    for item in row['name'].split(", "):  # removing comma from all strings in 'tags' column
                        set_one.append(row)

        if len(set_one) == 0: #if there's no entries found
            update.message.reply_text('Sorry, I couldn\'t find anything.')
            return ConversationHandler.END

        if len(set_one) != 0:
            return getSampleFromSet(set_one, update, context)

def getSampleFromSet(set_one, update, context):
    random_number_sample = min(len(set_one), 5)  #number of random selection from sample. if sample is less than 5, smaller number will be taken instead
    rt_randomSelect = random.sample(set_one, random_number_sample)

    text = 'I have randomly selected the following:\n'
    for i in range(len(rt_randomSelect)):
        text = text + '\n*' + str(i + 1) + '. ' + rt_randomSelect[i]["name"] + '*\n' + rt_randomSelect[i][
            "price"] + '\n' + rt_randomSelect[i]["address"] + '\n\n'

    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

def masterlist(update, context): #command line to output masterlist
    with open('patoh-yao.csv', 'r') as csv_file:
        nameSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:  # this is where all unique tags are put into a set
            for item in row['name'].split(", "):  # removing comma from all strings in 'tags' column
                nameSet.add(item)

    message_to_userMaster = "Available places are: \n\n"
    index = 1
    for item in nameSet:
        message_to_userMaster = message_to_userMaster + str(index) + ". " + item + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_userMaster)

masterlist_handler = CommandHandler('masterlist', masterlist)


def filter_search(update, context): #filter search by !<tags>
    user_input = update.message.text #i.e ".tag <tag>
    keyword = str(user_input[8:]) #because user_input now includes "!tag", to search without prefix = [5:]
    output = ""
    with open('patoh-yao.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            if keyword in row['tags']:
                output = output + row['name'] + "\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text="For " + user_input[8:] + ", I have found:" + "\n\n" + output)

filter_search_handler = PrefixHandler(['!', '.'], 'filter', filter_search)


def tags(update, context): #output list of all available <tags> to search
    with open('patoh-yao.csv', 'r') as csv_file:
        tagSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            for item in row['tags'].split(", "):
                tagSet.add(item)

    message_to_user = "Available tags are: \n\n"
    index = 1
    for item in tagSet:
        message_to_user = message_to_user + str(index) + ". " + item.capitalize() + "\n"
        index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_user)

tags_handler = CommandHandler('tags', tags)


def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("1522729097:AAG7EzwYRzeYVbVkw6siGTEspx1uGcCNjF8")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(help_handler)

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('suggest', suggest)],
        states={
            BUDGET: [MessageHandler(Filters.text, budget), CommandHandler('skip', skip_budget)],
            FOOD_TYPE: [MessageHandler(Filters.text & ~Filters.command, food_type),
                        CommandHandler('skip', skip_food_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(masterlist_handler)

    dispatcher.add_handler(filter_search_handler)

    dispatcher.add_handler(tags_handler)

    dispatcher.add_handler(unknown_handler)

    # dispatcher.add_handler(MessageHandler(Filters.text, randomer))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
