#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import csv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#GENDER, PHOTO, LOCATION, BIO = range(4)
BUDGET, FOOD_TYPE = range(2)

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['>$15', '$15 - $25', '$25 - $35',
                       '$35 - $50', '$50 - $100', '>$100']]
    #reply_keyboard = [['Boy', 'Girl', 'Other']]

    update.message.reply_text(
        'Hi! My name is Professor Bot. I will hold a conversation with you. '
        'Send /cancel to stop talking to me.\n\n'
        'Do you have a budget? Or send /skip if you don\'t have one.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return BUDGET


def budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    global budget_input = update.message.text
    logger.info("User %s entered budget: %s", user.first_name, update.message.text)
    update.message.reply_text('Okay! What about food type?' ' Or send /skip if you don\'t have a preference.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return FOOD_TYPE

budget()

def skip_budget(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
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
    update.message.reply_text('Thank you! Here are some food suggestions:')

    return randomer()


def skip_food_type(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not enter food type.", user.first_name)
    update.message.reply_text(
        'No problemo! Here are some food suggestions:'
    )

    return randomer()


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def randomer(update: Update, context: Context):
    with open('patohplz.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        set_one = list()
        for row in csv_dict_reader:
            if food_type_input in row['tags'] and budget_input in row['price']:
                for item in row['name'].split(", "):  # removing comma from all strings in 'tags' column
                    set_one.append(item)
                randomList = set_one
                random_number_sample = 2  # number of random selection from sample
                rt_randomSelect = random.sample(randomList, random_number_sample)
                sample1 = str(rt_randomSelect[0])
                sample2 = str(rt_randomSelect[1])
                #sample3 = str(rt_randomSelect[2])
                #sample4 = str(rt_randomSelect[3])
                #sample5 = str(rt_randomSelect[4])
                with open('patoh-yao.csv', 'r') as csv_file:  # to find matching address & price to random sample
                    csv_dict_reader = csv.DictReader(csv_file)
                    for row in csv_dict_reader:
                        if sample1 in row['name']:
                            sample1_address = row['address']
                            sample1_price = row['price']
                        if sample2 in row['name']:
                            sample2_address = row['address']
                            sample2_price = row['price']

                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="I have randomly selected two options:"
                                              "\n\n*1. " + sample1 + "*" +
                                              "\n" + sample1_price +
                                              "\n" + sample1_address +
                                              "\n\n*2. " + sample2 + "*" +
                                              "\n" + sample2_price +
                                              "\n" + sample2_address, parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater("token")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BUDGET: [MessageHandler(Filters.text, budget), CommandHandler('skip', skip_budget)],
            FOOD_TYPE: [MessageHandler(Filters.text & ~Filters.command, food_type), CommandHandler('skip', skip_food_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
