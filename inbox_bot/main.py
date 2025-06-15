import os.path
import telebot
import threading
import locale
from tg_util import TgMsg
import settings


# локаль
locale.setlocale(locale.LC_ALL, settings.MY_LOCALE)
# создаем экземпляр бота
bot = telebot.TeleBot(settings.TOKEN, parse_mode=None)
# создаем событие для синхронизации, чтобы обновлял данные только один поток
event = threading.Event()
event.set()


# Функция, обрабатывающая команду /start, /help
@bot.message_handler(commands=["start", "help"])
def handle_help(message, res=False):
    if message.from_user.id not in settings.ALLOWED_USERS:
        bot.send_message(message.chat.id, 'This is private bot, sorry')
        return
    bot.send_message(message.chat.id, settings.HELP)
    bot.send_message(message.chat.id, f"Это же ты, {settings.ALLOWED_USERS[message.from_user.id]}!")


# Функция сохранения сообщения, в которую может заходить только один потом
def save_message(message):
    global event
    event.wait()
    event.clear()
    reply = ''
    # читаю сообщение
    tgmsg = TgMsg(message, bot, settings.KNOWN_USERS)
    # print(tgmsg)
    content = ''
    # определяю имя файла
    dtm = tgmsg.dtm
    fname = dtm.strftime('%Y%m%d_%H%M%S')
    filefull = os.path.join(settings.IN_PATH, fname + '.md')
    # записываю заголовок
    if not os.path.exists(filefull):
        content += '# \n'
        content += 'id:: {}\n'.format(dtm.strftime('%Y%m%d%H%M%S'))
        content += 'ctype:: #telegram\n'
        content += '\n---\n'
        reply += 'Создан [[{}]]\n'.format(fname)
    # отправитель
    content += "\n**" + dtm.strftime('%Y-%m-%d %a %H:%M:%S').lower() + ". @" + tgmsg.user + ":**\n"
    print(content)
    # текст
    if tgmsg.text:
        content += tgmsg.text + '\n'
    # вложения
    attach_dtm = dtm
    for attach in tgmsg.files.keys():
        # print(attach)
        attachfile = attach_dtm.strftime('%Y%m%d_%H%M%S_').lower() + attach
        attachfull = os.path.join(settings.IN_PATH, attachfile)
        while os.path.exists(attachfull):
            attachfile = attach_dtm.strftime('%Y%m%d_%H%M%S_').lower() + attach
            attachfull = os.path.join(settings.IN_PATH, attachfile)
        with open(attachfull, 'wb') as f:
            f.write(tgmsg.files[attach])
        content += '\n![[{}]]\n'.format(attachfile)
        reply += 'Вложен {}\n'.format(attachfile)
    # сохраняю файл
    with open(filefull, 'a') as f:
        f.write(content)

    event.set()
    return reply


# Обработка сообщений, которые можно сохранить
@bot.message_handler(content_types=["text", "caption", "photo", "video", "voice", "video_note", "document"])
def handle_message(message):
    if message.from_user.id not in settings.ALLOWED_USERS:
        bot.send_message(message.chat.id, 'This is private bot, sorry')
        return
    try:
        reply = save_message(message)
        print(reply)
        bot.send_message(settings.ADMIN_USER, reply)
    except Exception as e:
        print(e)
        bot.send_message(settings.ADMIN_USER, f'ERROR {e}')


# Запускаем бота
print("Starting eg_inbox_bot...")
bot.infinity_polling()
