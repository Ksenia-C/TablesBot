"""
Implementation of echo bot.
"""

import os
import telebot
import pandas

def get_export_url(url):
    """Make export url from passed one."""
    options = url.split('/')
    if 'd' not in options:
        return (0, "Incorrect table url")
    ind_before_id = options.index('d')
    if ind_before_id + 1 >= len(options):
        return (0, "Failed to identify table")
    table_id = options[ind_before_id + 1]
    sheet_id = None
    options = options[-1].split('#')
    for option in options:
        pair = option.split("=")
        if len(pair) == 2 and pair[0] == 'gid':
            sheet_id = pair[1]
            break
    if sheet_id is None:
        return (0, "Failed to identify sheet")
    return (1,
    f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=csv&gid={sheet_id}")

def make_file_storage_path(chat_id):
    """Path to storage."""
    return f"./volumes/{chat_id}.txt"

def get_table_from_pandas(url):
    """Get table."""
    return pandas.read_csv(url)

def insert_new_string(chat_id, url, person_name):
    """Insert table from /add."""
    with open(make_file_storage_path(chat_id), 'a+', encoding = 'utf-8') as file:
        file.write( f"{url} {person_name}\n")

def get_searching_requests(chat_id):
    """Get requests for /show."""
    file = None
    try:
        file = open(f"./volumes/{chat_id}.txt", 'r', encoding = 'utf-8')
    except FileNotFoundError:
        return None
    request = file.readline()
    result = []
    while request:
        space_ind = request.find(' ')
        result.append((request[: space_ind], request[space_ind + 2: -2]))
        request = file.readline()
    file.close()
    return result


bot = telebot.TeleBot(os.environ.get("TOKEN"), parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Send info about bot to user."""
    bot.reply_to(message, '''I will show your result in assessment tables by request.\n\
    /add link_to_table_or_sheet (name copied from table) - add new person from table\n\
    /show - show all new changes in tables\n\
    /clear - delete all entries''')

@bot.message_handler(commands=['add'])
def add_table(message):
    """Add new table and name for chat.id."""
    space_after_url_ind = 5 + message.text[5:].find(" ")
    if space_after_url_ind == -1 or space_after_url_ind == len(message.text) or \
        message.text[space_after_url_ind + 1] != '(' or \
        message.text[-1] != ')':
        bot.send_message(message.chat.id,
            "Please retry with syntax /add link (name copied from table)")
        return
    export_url = get_export_url(message.text[5:space_after_url_ind])
    if export_url[0] == 0:
        bot.send_message(message.chat.id, "Please check your table link: "+ export_url[1])
        return
    searching_name = message.text[space_after_url_ind + 1:]
    insert_new_string(message.chat.id, export_url[1], searching_name)
    bot.send_message(message.chat.id, "Ok for add person "+ searching_name)

@bot.message_handler(commands=['show'])
def show_result(message):
    """Show strings from tables."""
    search_requests = get_searching_requests(message.chat.id)
    if search_requests is None:
        bot.send_message(message.chat.id, "You did not add any table")
        return
    for request in search_requests:
        table = get_table_from_pandas(request[0])
        person_ind = -1
        for i in range(len(table)):
            if table.iloc[i][0] == request[1] or table.iloc[i][1] == request[1]:
                person_ind = i
                break
        if person_ind == -1:
            continue
        bot.send_message(message.chat.id,
            '\n'.join([str(table.columns[i]) + ': ' + str(table.iloc[person_ind][i])
             for i in range(table.shape[1])]))

@bot.message_handler(commands=['clear'])
def clear_data(message):
    """Delete file with data."""
    os.remove(make_file_storage_path(message.chat.id))
    bot.send_message(message.chat.id, "ok, deleted")

if __name__ == '__main__':
    bot.infinity_polling()
