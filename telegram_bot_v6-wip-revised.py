def randomSample(update, context):
    user_data = context.user_data

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

    R = 6371000  # radius of the Earth in m
    def distance(lon1, lat1, lon2, lat2):
        x = (lon2 - lon1) * cos(0.5 * (lat2 + lat1))
        y = (lat2 - lat1)
        return R * sqrt(x * x + y * y)

    def filterNearby(item) -> bool:
        if None in {user_data['LAT_INPUT'], user_data['LON_INPUT']}:
            return True
        if distance(item["lat"], item["lon"], user_data['LAT_INPUT'], user_data['LON_INPUT']) < 100000:
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
