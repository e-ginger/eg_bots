import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
from datetime import datetime
import os
import re
import json
from pydub import AudioSegment
from config import Config
from chat import Chat
from obsidian import Obsidian

"""
Команды бота
clear - Очистить контекст
info - Информация
get_model - Выбрать модель
load_chat - Загрузить чат
del - Удалить последнее
context - Посмотреть контекст 
"""


# Создаем экземпляр конфигурации
config = Config()
config.load_config()

# Создаем экземпляр бота
bot = telebot.TeleBot(config.get("bot_token"))

# Чаты для хранения контекста
chats = {}

# Экземпляр объекта для доступа к заметкам Obsidian
obsidian = Obsidian(config.get("obsidian_vault"))


# Проверяет, есть ли id пользователя в списке разрешенных и создает для него чат
def init_chat(chat_id):
    chat_id = str(chat_id)
    user = None
    users = config.get("users")
    if users:
        user = users.get(chat_id, None)
    if not user:
        return None

    if chat_id not in chats:
        model = user.get("model", "")
        model_config = config.get_model_config(model)
        if not model_config:
            return None

        print("user", user)
        chat = Chat(
            chat_id=chat_id,
            models=user.get("models", []),
            chats_dir=user.get("chats_dir", ""),
            max_context=user.get("max_context")
        )
        chat.set_model(model, model_config)
        chats[chat_id] = chat
    else:
        chat = chats[chat_id]
    print("init_chat", chat)
    return chat


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    chat.clear()
    bot.send_message(chat.chat_id, "Привет! Я простой чат-бот :)")


# Обработчик команды /clear (добавим для удобства)
@bot.message_handler(commands=['clear'])
def handle_clear(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    chat.clear()
    bot.send_message(chat.chat_id, "🗑")


# Обработчик команды /info
@bot.message_handler(commands=['info'])
def handle_info(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    response = f"ℹ️\nМодель: {chat.model}\n"\
               f"Контекст: {chat.get_turn_count()} из {chat.max_context}"
    if chat.preview_context():
        response += "\n\n" + chat.preview_context()

    bot.send_message(chat.chat_id, response)


# Обработчик команды /context
@bot.message_handler(commands=['context'])
def handle_context(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    response = f"Контекст: {chat.get_turn_count()} из {chat.max_context}"
    if chat.view_context():
        response += "\n\n" + chat.view_context()

    bot.send_message(chat.chat_id, response)


# Обработчик команды /get_model
@bot.message_handler(commands=['get_model'])
def handle_get_model(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    if not chat.models:
        bot.send_message(chat.chat_id, "Нет моделей для выбора!")
        return

    send_models_page(chat.chat_id, chat.models, chat.model)


def send_models_page(chat_id, models, current_model, page=0, message_to_edit=None):
    models_per_page = config.get("models_per_page")
    total_pages = (len(models) + models_per_page - 1) // models_per_page
    page = max(0, min(page, total_pages - 1))

    # Выбираем модели для текущей страницы
    start_idx = page * models_per_page
    end_idx = start_idx + models_per_page
    page_models = models[start_idx:end_idx]

    # Создаем клавиатуру с кнопками для моделей текущей страницы
    keyboard = InlineKeyboardMarkup()

    for model in page_models:
        prefix = "✅ " if model == current_model else ""
        keyboard.add(InlineKeyboardButton(
            text=f"{prefix}{model}",
            callback_data=f"set_model:{model}"
        ))

    nav_buttons = []
    if total_pages > 1 and page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅",
            callback_data=f"models_page:{page - 1}"
        ))

    if total_pages > 1 and page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"models_page:{page + 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text="❌",
        callback_data="close_models"
    ))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    text = f"Выберите модель (Страница {page + 1}/{total_pages}):"

    # Отправляем или обновляем сообщение
    if message_to_edit:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_to_edit.message_id,
                text=text,
                reply_markup=keyboard
            )
            return message_to_edit
        except Exception as e:
            # Если не удалось отредактировать, отправляем новое
            print(f"Ошибка при редактировании сообщения: {e}")
            # Перед отправкой нового удалить старое
            try:
                bot.delete_message(chat_id, message_to_edit.message_id)
            except:
                pass
            return bot.send_message(chat_id, text, reply_markup=keyboard)
    else:
        return bot.send_message(chat_id, text, reply_markup=keyboard)


# Обработчик callback-запросов для пагинации и выбора модели
@bot.callback_query_handler(func=lambda call: call.data.startswith(('set_model:', 'models_page:', 'close_models')))
def handle_models_callback(call):
    chat = init_chat(call.message.chat.id)
    if not chat:
        bot.send_message(call.message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {call.message.chat.id} пытался получить доступ к боту")
        return
    data = call.data

    if data.startswith('models_page:'):
        page = int(data.replace('models_page:', ''))
        send_models_page(chat.chat_id, chat.models, chat.model, page, call.message)
        bot.answer_callback_query(call.id)

    elif data.startswith('set_model:'):
        current_model = data.replace('set_model:', '')

        if chat.model == current_model:
            bot.answer_callback_query(call.id, f"Модель уже установлена: {current_model}")
            return

        chat.set_model(current_model, config.get_model_config(current_model))

        # Находим текущую страницу, чтобы после обновления остаться на ней
        page = 0
        match = re.search(r'Страница (\d+)/(\d+)', call.message.text)
        if match:
            page = int(match.group(1)) - 1

        send_models_page(chat.chat_id, chat.models, current_model, page, call.message)
        bot.answer_callback_query(call.id, f"Модель изменена на: {current_model}")

    elif data == 'close_models':
        # Удаление сообщения с выбором модели
        try:
            bot.delete_message(chat.chat_id, call.message.message_id)
            bot.send_message(chat.chat_id, f"Модель: {chat.model}")
        except:
            print(f"Ошибка удаления сообщения")
            bot.answer_callback_query(call.id, "Не удалось закрыть меню")
        bot.answer_callback_query(call.id)


# Обработчик команды /load_chat
@bot.message_handler(commands=['load_chat'])
def handle_load_chat(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    # Получаем список всех чатов пользователя
    chat.load_all_chat_files()
    if not chat.all_chat_files:
        bot.send_message(chat.chat_id, "Нет сохраненных чатов для загрузки!")
        return

    send_chats_page(chat.chat_id, chat.all_chat_files, page=0)


def send_chats_page(chat_id, chat_files, page=0, message_to_edit=None):
    print("send_chats_page", chat_id, len(chat_files), page, message_to_edit)
    chats_per_page = config.get("models_per_page")  # Используем то же значение, что и для моделей
    total_pages = (len(chat_files) + chats_per_page - 1) // chats_per_page
    page = max(0, min(page, total_pages - 1))

    # Выбираем чаты для текущей страницы
    start_idx = page * chats_per_page
    end_idx = start_idx + chats_per_page
    page_chats = chat_files[start_idx:end_idx]
    print("page_chats", page_chats)

    # Создаем клавиатуру с кнопками для чатов текущей страницы
    keyboard = InlineKeyboardMarkup()

    for i in range(0, len(page_chats)):
        idx = page * chats_per_page + i
        keyboard.add(InlineKeyboardButton(
            text=page_chats[i],
            callback_data=f"load_chat:{idx}"
        ))

    nav_buttons = []
    if total_pages > 1 and page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅",
            callback_data=f"chats_page:{page - 1}"
        ))

    if total_pages > 1 and page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"chats_page:{page + 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text="❌",
        callback_data="close_chats"
    ))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    text = f"Выберите чат для загрузки (Страница {page + 1}/{total_pages}):"

    # Отправляем или обновляем сообщение
    if message_to_edit:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_to_edit.message_id,
                text=text,
                reply_markup=keyboard
            )
            return message_to_edit
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            try:
                bot.delete_message(chat_id, message_to_edit.message_id)
            except:
                pass
            return bot.send_message(chat_id, text, reply_markup=keyboard)
    else:
        return bot.send_message(chat_id, text, reply_markup=keyboard)


# Обработчик callback-запросов для пагинации и выбора чата
@bot.callback_query_handler(func=lambda call: call.data.startswith(('load_chat:', 'chats_page:', 'close_chats')))
def handle_chats_callback(call):
    chat = init_chat(call.message.chat.id)
    if not chat:
        bot.send_message(call.message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {call.message.chat.id} пытался получить доступ к боту")
        return
    data = call.data
    print("handle_chats_callback")

    if data.startswith('chats_page:'):
        page = int(data.replace('chats_page:', ''))
        send_chats_page(chat.chat_id, chat.all_chat_files, page, call.message)
        bot.answer_callback_query(call.id)

    elif data.startswith('load_chat:'):
        idx = int(data.replace('load_chat:', ''))
        selected_file = chat.all_chat_files[idx]
        chat.load_chat(selected_file)
        bot.answer_callback_query(call.id, f"Чат {selected_file} выбран для загрузки")

        # Удаляем сообщение с выбором чатов
        try:
            bot.delete_message(chat.chat_id, call.message.message_id)
        except:
            print("Ошибка удаления сообщения")

        print("chat after", chat)
        response = f"Чат '{selected_file}' загружен\n"\
                   f"Контекст: {chat.get_turn_count()} из {chat.max_context}"
        if chat.preview_context():
            response += "\n\n" + chat.preview_context()

        bot.send_message(chat.chat_id, response)

    elif data == 'close_chats':
        try:
            bot.delete_message(chat.chat_id, call.message.message_id)
        except:
            print(f"Ошибка удаления сообщения")
            bot.answer_callback_query(call.id, "Не удалось закрыть меню")
        bot.answer_callback_query(call.id)


# Обработчик команды /del
@bot.message_handler(commands=['del'])
def handle_del(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    chat.remove_last_message()
    if chat.preview_context():
        bot.send_message(chat.chat_id, f"{chat.preview_context()}")
    else:
        bot.send_message(chat.chat_id, f"🗑️")


# Если в промте есть указания на то, что можно подгрузить дополнительный контекст, это происходит здесь
# сейчас я хочу подгружать содержимое заметок из Obsidian c помощью [[ ]]
def expand_context(chat, prompt):
    # Найти в prompt все вхождения [[name]]
    # где name - имя заметки, может содержать любые символы, допустимые в именах файлов linux, windows, android и т.д.
    # для каждого вхождения вызвать data = obsidian.get_note_content(name)
    # если data не пустая, заменить в prompt "[[name]]" на "\n{data}\n"
    # хотя если заменять, потом неудобно повторно использовать эти промты
    matches = re.findall(r'\[\[(.*?)\]\]', prompt)
    for note_name in matches:
        note_content = obsidian.get_note_content(note_name.strip())
        if note_content:
            # prompt = prompt.replace(f'[[{note_name}]]', f'\n{note_content}\n')
            prompt = prompt + f"\n\n[[{note_name}]]:\n{note_content}"
    return prompt


# Вынесла обработку сообщения в отдельную функцию,
# чтобы вызывать его и из обработки текста, и после распознавания голосового
def process_prompt(chat, prompt):
    try:
        # Формируем сообщения: системный промпт + история диалога + новый запрос
        messages = [{"role": "system", "content": config.get("ai_system")}]
        messages.extend(chat.messages)
        messages.append({"role": "user", "content": prompt})
        # Сохраняем запрос сразу
        chat.add_message("user", prompt)

        # Проверяем параметры выбранной модели
        if not chat.model_config:
            raise ValueError("Выбранная модель не найдена или отключена")

        # Запрос к LLM
        answer = ""
        if chat.model == "dummy":
            answer = "..."
        else:
            client = OpenAI(
                api_key=chat.model_config.get("apiKey", ""),
                base_url=chat.model_config.get("baseUrl", None)
            )
            response = client.chat.completions.create(
                model=chat.model_config.get("name"),
                messages=messages,
                extra_headers={},
                temperature=0.7,
                n=1,
                max_tokens=3000
            )
            answer = response.choices[0].message.content
        # Сохраняем и ответ в историю диалога
        chat.add_message("assistant", answer)

        print(f"Вопрос ({chat.chat_id}): {prompt}")
        print(f"Ответ ({chat.chat_id}): {answer}")
        print("chat after", chat)
        bot.send_message(chat.chat_id, answer)
    except Exception as e:
        print(f"Ошибка ({chat.chat_id}):", e)
        bot.send_message(chat.chat_id, f"Произошла ошибка: {e}")


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    prompt = message.text
    prompt = expand_context(chat, prompt)
    if re.match("^(👤|🤖)", prompt, re.DOTALL):
        push_message(chat, prompt)
    else:
        process_prompt(chat, prompt)


# Обработчик голосовых сообщений
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat = init_chat(message.chat.id)
    if not chat:
        bot.send_message(message.chat.id, "Простите, ваш доступ к боту не настроен. Обратитесь к админу @evg-genia")
        print(f"Пользователь {message.chat.id} пытался получить доступ к боту")
        return

    try:
        file_info = bot.get_file(message.voice.file_id)
        file_data = bot.download_file(file_info.file_path)

        os.makedirs("voice_messages", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ogg_file_name = f"voice_messages/{timestamp}_{message.voice.file_unique_id}.ogg"
        mp3_file_name = f"voice_messages/{timestamp}_{message.voice.file_unique_id}.mp3"

        # Сохраняем оригинальный OGG файл
        with open(ogg_file_name, 'wb') as new_file:
            new_file.write(file_data)

        # Конвертируем в MP3 с помощью pydub
        audio = AudioSegment.from_ogg(ogg_file_name)
        audio.export(mp3_file_name, format="mp3")

        # Удаляем временный OGG файл
        os.remove(ogg_file_name)

        # Распознавание
        tts_model = config.get("tts_model")
        if not tts_model:
            raise ValueError("Модель TTS не настроена")

        client = OpenAI(
            api_key=tts_model.get("apiKey", ""),
            base_url=tts_model.get("baseUrl", "")
        )

        audio_file = open(mp3_file_name, "rb")
        transcript = client.audio.transcriptions.create(
            model=tts_model.get("name", ""),
            response_format="text",
            language="ru",
            file=audio_file
        )

        # Из полученного ответа надо извлечь текст
        prompt = ""
        if transcript:
            print(f"Распознано ({chat.chat_id}):", repr(transcript))
            prompt = json.loads(transcript).get("text", "")
        # Если текст извлечен, обрабатывается как голосовое сообщение
        if prompt:
            # bot.reply_to(message, prompt) # пока отключу отображение распознанного
            process_prompt(chat, prompt)

            # голосовое можно удалить
            # os.remove(mp3_file_name)
        else:
            bot.reply_to(message, "Не удалось распознать голосовое сообщение")

    except Exception as e:
        print(f"Ошибка при обработке голосового сообщения: {e}")
        bot.reply_to(message, f"Произошла ошибка при обработке голосового сообщения: {e}")


# Добавляет сообщение в контекст, не отправляя его в модель
def push_message(chat, prompt):
    print("push_message", prompt)
    role = ""
    if prompt.startswith("👤"):
        prompt = prompt.replace("👤", "", 1)
        role = "user"
    if prompt.startswith("🤖"):
        prompt = prompt.replace("🤖", "", 1)
        role = "assistant"
    prompt = prompt.lstrip()
    if role:
        chat.add_message(role, prompt)
        bot.send_message(chat.chat_id, "💾")


# Запускаем бота
print("Бот запущен и готов к работе!")
bot.infinity_polling()
