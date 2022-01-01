"""
Implementation of echo bot.
"""

import os
import telebot
import pandas
import json

used_commands = {}


class Table:
    def __init__(self,
                 name=None,
                 link=None,
                 export_link=None,
                 searching_cell=None) -> None:
        self.name = name
        self.link = link
        self.export_link = export_link
        self.searching_cell = searching_cell


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
    return (1, "https://docs.google.com/spreadsheets/d/" +
            f"{table_id}/export?format=csv&gid={sheet_id}")


def make_file_storage_path(chat_id):
    """Path to storage."""
    return f"./volumes/{chat_id}.txt"


def get_table_from_pandas(url):
    """Get table."""
    return pandas.read_csv(url)


def insert_new_string(chat_id, user_table):
    """Insert table from /add."""
    with open(make_file_storage_path(chat_id), 'a+', encoding='utf-8') as file:
        table_line = json.dumps(user_table.__dict__)
        file.write(f"{table_line}\n")


def get_searching_requests(chat_id):
    """Get requests for /show."""
    file = None
    try:
        file = open(f"./volumes/{chat_id}.txt", 'r', encoding='utf-8')
    except FileNotFoundError:
        return None
    user_table = file.readline()
    result = []
    while user_table:
        table = Table(**json.loads(user_table))
        result.append(table)
        user_table = file.readline()
    file.close()
    return result


bot = telebot.TeleBot(os.environ.get("TOKEN"), parse_mode=None)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Send info about bot to user."""
    bot.reply_to(message, '''I will show your result in assessment tables by request.\n\
    /add link_to_table_or_sheet (name copied from table)\
    - add new person from table\n\
    /show - show all new changes in tables\n\
    /clear - delete all entries''')

# -------------------- Add -------------------- #


@bot.message_handler(commands=['add'])
def add_table(message):
    """Add new table and name for chat.id."""
    msg = bot.reply_to(message, """\
        Вставьте ссылку с нужного листа google tables с публичным доступом
        """)
    user_table = Table()
    bot.register_next_step_handler(msg, process_link_step, user_table)


def process_link_step(message, user_table: Table):
    if message.text in used_commands:
        used_commands[message.text](message)
        return
    link = message.text
    export_link = get_export_url(link)
    if export_link[0] == 0:
        msg = bot.reply_to(message, "Please insert valid google table url")
        bot.register_next_step_handler(msg, process_link_step, user_table)
        return
    user_table.link = link
    user_table.export_link = export_link[1]
    msg = bot.reply_to(message, """\
        Вставьте полностью скопированный текст ячейки,\
            по которому можно отслеживать результаты
        """)
    bot.register_next_step_handler(msg, process_cell_step, user_table)


def process_cell_step(message, user_table: Table):
    if message.text in used_commands:
        used_commands[message.text](message)
        return
    user_table.searching_cell = message.text
    msg = bot.reply_to(message, """\
        Название таблицы для вас (рекомендуется короткое)
        """)
    bot.register_next_step_handler(msg, process_name_step, user_table)


def process_name_step(message, user_table: Table):
    if message.text in used_commands:
        used_commands[message.text](message)
        return
    user_table.name = message.text
    insert_new_string(message.chat.id, user_table)
    bot.send_message(message.chat.id, f"Ok for {user_table.searching_cell}")


# -------------------- Show -------------------- #

@bot.message_handler(commands=['show'])
def show_result(message):
    """Show strings from tables."""
    table_names = message.text.split(' ')[1:]
    search_requests = get_searching_requests(message.chat.id)
    if search_requests is None:
        bot.send_message(message.chat.id, "You did not add any table")
        return
    for request in search_requests:
        if request.name not in table_names:
            continue
        table = get_table_from_pandas(request.export_link)
        person_ind = -1
        for i in range(len(table)):
            if request.searching_cell in [table.iloc[i][0], table.iloc[i][1]]:
                person_ind = i
                break
        if person_ind == -1:
            continue
        s_result = '\n'.join([str(table.columns[i]) + ': ' +
                             str(table.iloc[person_ind][i])
                             for i in range(table.shape[1])])
        bot.send_message(message.chat.id, f"{request.name}\n{s_result}")


# -------------------- Clear -------------------- #

@bot.message_handler(commands=['clear'])
def clear_data(message):
    """Delete file with data."""
    os.remove(make_file_storage_path(message.chat.id))
    bot.send_message(message.chat.id, "ok, deleted")


used_commands = {
    '/start': send_welcome,
    '/help': send_welcome,
    '/add': add_table,
    '/show': show_result,
    '/clear': clear_data,
}
bot.infinity_polling()
