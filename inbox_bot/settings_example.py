
# Информация, которую вывести в ответ на /start или /help
HELP = '''Привет! Я - бот для сохранения заметок в инбокс. Я работаю только для разрешенных пользователей.
Мой разработчик {ссылка на профиль разработчика в Telegram} может ответить на вопросы о использовании бота.

Hello! I'm bot for saving notes to inbox. I'm working only for allowed users. 
My developer {link to developer's Telegram profile} can answer the questions about usage of bot.
'''

# Токен для доступа к Telegram
TOKEN = ''

# Пользователь, которому присылать сообщения об ошибках (id from Telegram)
ADMIN_USER = 0

# Пользователи, которым разрешен доступ к боту (словарь id -> имя)
ALLOWED_USERS = {0: 'я'}

# Известные пользователи (словарь id -> имя)
KNOWN_USERS = {
    0: 'я'
}

# Путь, куда сохранять полученные заметки
IN_PATH = '~/Downloads'

# Локаль влияет на формат дат
MY_LOCALE = 'ru_RU.utf-8'
