# How to install
Приведены команды для операционной системы Linux.

## 1. Скачать исходный код, установить зависимости
```
# Clone repository
cd ~
mkdir eg_bots
cd ./eg_bots
git clone https://github.com/e-ginger/eg_bots.git

# Setup virtual environment
python3 --version
python -m venv --copies venv
source venv/bin/activate
which python

# Install requirements
pip install pytelegrambotapi
pip install openai
pip install pydub
```

Установить ffmpeg, который требуется для работы pydub:
- На Windows: скачать с официального сайта и добавить в PATH
- На Linux: sudo apt-get install ffmpeg
- На Mac: brew install ffmpeg


## 2. Настроить inbox_bot
### 2.1 
Файл inbox_bot/settings_example.py скопировать с именем inbox_bot/settings.py.

### 2.2
С помощью бота @BotFather создать своего бота с любым именем, например `<ваш_ник>_inbox_bot`. BotFather вернет API-ключ. 

API-ключ нужно добавить в файле inbox_bot/settings.py:
```
TOKEN = 'сюда вставить токен от BotFather'
```

### 2.3
Узнать свой числовой ID в Telegram. Для этого отправить любое сообщение боту @getmyid_bot, и он автоматически покажет ваш ID.

В файле inbox_bot/settings.py прописать доступ к боту. Для ADMIN_USER, ALLOWED_USERS, KNOWN_USERS вместо нуля подставить свой ID.

Примечание:
- ADMIN_USER - основной пользователь и администратор бота.
- KNOWN_USERS - пользователи, чье имя при сохранении пересланных сообщений будет заменяться указанным псевдонимом.
- ALLOWED_USERS - пользователи, которым, кроме вас, разрешен доступ к боту.

### 2.4
В файле inbox_bot/settings.py прописать путь к папке, куда сохранять заметки (IN_PATH).

### 2.5
Скрипт eg_inbox_bot.sh сделать исполняемым: `chmod +x eg_inbox_bot.sh`.
Запустить бота с помощью eg_inbox_bot.sh.


## 3. Настроить personal_gpt_bot

### 3.1
Скрипт eg_inbox_bot.sh сделать исполняемым: `chmod +x eg_personal_gpt_bot.sh`.
Попробовать запустить бота с помощью eg_inbox_bot.sh.

Бот остановится с ошибкой, но создаст пустой файл конфигурации personal_gpt_bot/config.json.

### 3.2
С помощью бота @BotFather создать своего бота с любым именем, например `<ваш_ник>_personal_gpt_bot`. BotFather вернет API-ключ.
Добавить этот ключ в config.json в поле bot_token.

### 3.3
Заполнить в config.json общий список моделей ai_models_list. Провайдер может быть любой OpenAI-совместимый по API. Вот пример для vsegpt: 
```
    {
      "name": "openai/gpt-4o-mini",
      "provider": "3rd party (openai-format)",
      "enabled": true,
      "baseUrl": "https://api.vsegpt.ru/v1",
      "apiKey": "здесь api-ключ от провайдера",
      "capabilities": [],
      "stream": true,
      "displayName": "vsegpt gpt-4o-mini"
    },
```
По умолчанию в этот список добавлена dummy - модель-заглушка, встроенная в бот.
Формат описания модели очень близок к Obsidian Copilot, 
чтобы скопировать настройки моделей из {obsidan vault path}/.obsidian/plugins/copilot/data.json.

### 3.4
Узнать свой числовой ID в Telegram. Для этого отправить любое сообщение боту @getmyid_bot, и он автоматически покажет ваш ID.
В config.json в массиве users вместо 0 прописать свой ID. Можно добавить и других разрешенных пользователей по ID.

### 3.5
Для каждого пользователя в config.json нужно прописать список разрешенных моделей models и модель по умолчанию model. 
Использовать displayName из общего списка моделей.

### 3.6
В config.json обязательно каждому пользователю прописать собственную папку для чатов, чтоб никто не мог получить доступ к чужим данным.
Например, создать подпапки в personal_gpt_bot/chats по ID пользователя.

### 3.7
Tts_model в config.json нужна для распознавания голосовых. Вот пример настройки для vsegpt:
```
  "tts_model": {
    "name": "stt-openai/whisper-1",
    "baseUrl": "https://api.vsegpt.ru/v1",
    "apiKey": "sk-и дальше API-ключ провайдера"
  },
```

### 3.8
Параметр obsidian_vault можно указать, если есть необходимость подгружать в контекст заметки из Obsidian через `[[ ]]`, 
как это сделано в плагине Obsidian Copilot.