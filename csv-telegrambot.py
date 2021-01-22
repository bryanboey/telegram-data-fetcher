import csv
import logging
import random
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

updater = Updater(token='token id', use_context=True)

dispatcher = updater.dispatcher

updater.start_polling()


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm Botohyao. Patohyao's infograbber! \n\nCommand list:\n/random - randomly selects a place to eat\n/tags - list all unique tags from the list\n!<tag> - searches all places with <tag>")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi, I'm Botohyao!\n\nThis is a private list of food establishments that Bryan & Cindy has compiled.\n\nAt this current version, you may only search 'tags'. Example: !cheap or !korean, etc. Type '/tags' to see a list of tags.")

dispatcher.add_handler(CommandHandler("help", help))
help_handler = CommandHandler('help', help)

def masterlist(update, context): #command line to output masterlist
    with open('patohplz.csv', 'r') as csv_file:
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

dispatcher.add_handler(CommandHandler("masterlist", masterlist))
masterlist_handler = CommandHandler('masterlist', masterlist)

def filter_search(update, context): #filter search by !<tags>
    user_input = update.message.text #i.e "cheap", "korean"
    key = "!"
    if "!" not in user_input: #i want to remove error messages and ignore messages without ! trigger
        return None
    if key in user_input: #i want to differentiate tag search from normal typing *currently still reading/not ignoring texts without !
        keyword = str(user_input[1:]) #because user_input now includes "!" such as !cheap, search parameter need to be without "!" hence [1:]
    output = ""
    with open('patohplz.csv', 'r') as csv_file:
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            if keyword in row['tags']:
                output = output + row['name'] + "\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text="For " + user_input[1:] + ", I have found:" + "\n\n" + output)

filter_search_handler = MessageHandler(Filters.text & (~Filters.command), filter_search)
dispatcher.add_handler(filter_search_handler)


def tags(update, context): #output list of all available <tags> to search
    with open('patohplz.csv', 'r') as csv_file:
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

dispatcher.add_handler(CommandHandler("tags", tags))
tags_handler = CommandHandler('tags', tags)


def randomselect(update, context): #randomly select a name from a name column of csv
    with open('patohplz.csv', 'r') as csv_file:
        nameSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            for item in row['name'].split(", "):
                nameSet.add(item)
        randomList = list(nameSet) #this step to allow random to sample *important note of indentation
        num_to_select = 2 #number of random selection from sample
        randomSelect = random.sample(randomList, num_to_select)
        message_to_userRandom = "I have randomly selected two options:\n\n"
        index = 1
        for item in randomSelect:
            message_to_userRandom = message_to_userRandom + str(index) + "." + item + "\n"
            index = index + 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_userRandom + "\nPick a number and.. Rock Paper Scissors! ✊👋✌")

dispatcher.add_handler(CommandHandler("random", randomselect))
random_handler = CommandHandler('random', randomselect)

def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)
