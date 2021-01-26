import csv
import logging
import random
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    PrefixHandler
)
from telegram import ParseMode


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm Botohyao, an information grabber!"
                                                                    "\n\n*Command list:*"
                                                                    "\n/random - randomly picks 2 places"
                                                                    "\n/masterlist - lists all food places"
                                                                    "\n/tags - lists all available tags to search"
                                                                    "\n.filter <tag> - searches all places with <tag>"
                                                                    "\n.rt <tag> - random tag, randomly picks 2 places with <tag>"
                                                                    "\n/help - credits and more information",parse_mode=ParseMode.MARKDOWN)

start_handler = CommandHandler('start', start)

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="\n\nAt this current version, you may only search/filter 'tags'."
                                                                    "\nType /start to see command list."
                                                                    "\n\nThis is a private list of food places by Cindy and myself that we wish to visit. "
                                                                    "I created this bot to serve as an assistant to retrieve specific data easily "
                                                                    "and quickly as opposed to opening and looking through a spreadsheet that's tiny on our phones."
                                                                    "\n\nCredits:"
                                                                    "\nModules by python-telegram-bot"
                                                                    "\nBig thanks to Cameron for the guidance. 😊")

help_handler = CommandHandler('help', help)


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


def randomtag_select(update, context):
    rt_input = update.message.text
    rt_keyword = str(rt_input[4:]) #to search input without prefix text
    with open('patoh-yao.csv', 'r') as csv_file:
        rt_nameSet = list()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:  #
            if rt_keyword in row['tags']: # <tag>
                for item in row['name'].split(", "):
                    rt_nameSet.append(item)
        rt_randomList = rt_nameSet
        rt_num_to_select = 2  # number of random selection from sample
        rt_randomSelect = random.sample(rt_randomList, rt_num_to_select)
        #rt_message_to_user = "For " + rt_keyword + ", I have randomly selected two options:\n\n"
        #rt_index = 1
        rts1 = str(rt_randomSelect[0])
        rts2 = str(rt_randomSelect[1])
        with open('patoh-yao.csv', 'r') as csv_file:  # to find matching address & price to random sample
            csv_dict_reader = csv.DictReader(csv_file)
            for row in csv_dict_reader:
                if rts1 in row['name']:
                    rts1address = row['address']
                    rts1price = row['price']
                if rts2 in row['name']:
                    rts2address = row['address']
                    rts2price = row['price']

        #for item in rt_randomSelect:
            #rt_message_to_user = rt_message_to_user + str(rt_index) + "." + item + "\n"
            #rt_index = rt_index + 1
        #context.bot.send_message(chat_id=update.effective_chat.id, text=rt_message_to_user + "\nPick a number and.. Rock Paper Scissors! ✊👋✌")
        context.bot.send_message(chat_id=update.effective_chat.id, text="For " + rt_keyword + ", I have randomly selected two options:"
                                                                        "\n\n*1. " + rts1 + "*     - " + rts1price +
                                                                        "\n" + rts1address +
                                                                        "\n\n*2. " + rts2 + "*     - " + rts2price +
                                                                        "\n" + rts2address,parse_mode=ParseMode.MARKDOWN)

#randomtag_select_handler = MessageHandler(Filters.text & (~Filters.command), randomtag_select)
randomtag_select_handler = PrefixHandler(['!', '.'], 'rt', randomtag_select)


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

#filter_search_handler = MessageHandler(Filters.text & (~Filters.command), filter_search)
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


def randomselect(update, context): #randomly select a name from a name column of csv
    with open('patoh-yao.csv', 'r') as csv_file:
        nameSet = set()
        csv_dict_reader = csv.DictReader(csv_file)
        for row in csv_dict_reader:
            for item in row['name'].split(", "):
                nameSet.add(item)
        randomList = list(nameSet) #this step to allow random to sample *important note of indentation
        num_to_select = 2 #number of random selection from sample
        randomSelect = random.sample(randomList, num_to_select)
        #message_to_userRandom = "I have randomly selected two options:\n\n"
        #index = 1
        rs1 = str(randomSelect[0])
        rs2 = str(randomSelect[1])

        with open('patoh-yao.csv', 'r') as csv_file:  # to find matching address & price to random sample
            csv_dict_reader = csv.DictReader(csv_file)
            for row in csv_dict_reader:
                if rs1 in row['name']:
                    rs1address = row['address']
                    rs1price = row['price']
                if rs2 in row['name']:
                    rs2address = row['address']
                    rs2price = row['price']

        #for item in randomSelect:
            #message_to_userRandom = message_to_userRandom + str(index) + "." + item + "\n"
            #index = index + 1
    #context.bot.send_message(chat_id=update.effective_chat.id, text=message_to_userRandom + "\nPick a number and.. Rock Paper Scissors! ✊👋✌")
    context.bot.send_message(chat_id=update.effective_chat.id, text="I have randomly selected two options:"
                                                                    "\n\n*1. " + rs1 + "*     - " + rs1price +
                                                                    "\n" + rs1address +
                                                                    "\n\n*2. " + rs2 + "*     - " + rs2price +
                                                                    "\n" + rs2address,parse_mode=ParseMode.MARKDOWN)

random_handler = CommandHandler('random', randomselect)

def unknown(update, context): #unknown commands
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)


def main():
    updater = Updater(token='token id', use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(help_handler)

    dispatcher.add_handler(masterlist_handler)

    dispatcher.add_handler(randomtag_select_handler)

    dispatcher.add_handler(filter_search_handler)

    dispatcher.add_handler(tags_handler)

    dispatcher.add_handler(random_handler)

    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

if __name__ == '__main__':
    main()
