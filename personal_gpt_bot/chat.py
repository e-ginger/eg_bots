import re
from datetime import datetime
import os


class Chat:

    def __init__(self, chat_id, models, chats_dir, max_context):
        self.chat_id = chat_id
        self.models = models
        self.chats_dir = chats_dir
        self.max_context = max_context
        self.model = ""
        self.model_config = None
        self.chat_file = None
        self.messages = []
        self.all_chat_files = []

    def __str__(self):
        msg_str = ""
        for message in self.messages:
            msg_str += '\n' + str(message)
        return (
            f"Chat(chat_id={self.chat_id}, "
            f"models={self.models}, "
            f"chats_dir={self.chats_dir}, "
            f"max_context={self.max_context}, "
            f"model={self.model}, "
            f"model_config={bool(self.model_config)}, "
            f"chat_file={self.chat_file}, "
            f"turn_count={self.get_turn_count()})" +
            msg_str
        )

    def set_model(self, model, model_config):
        """Устанавлиевает конфиг модели"""
        self.model = model
        self.model_config = model_config

    def clear(self):
        """Очищает историю чата"""
        self.messages = []
        self.chat_file = None

    def add_message(self, role, content):
        """Добавляет сообщение в историю чата"""

        self.messages.append({"role": role, "content": content})
        self.save_message_to_file(role, content)

        # Ограничиваем историю диалога в памяти
        if len(self.messages) > self.max_context * 2:
            self.messages = self.messages[-self.max_context * 2:]

    def get_turn_count(self):
        """Возвращает количество итераций беседы"""
        return int(len(self.messages) / 2)

    def create_file(self, title):
        """Создает пустой файл"""

        # Из первого сообщения можно сделать заголовок в имени файла
        title = title.strip()
        title = re.sub(r'\s+', '_', title)
        title = re.sub(r'[^\w]', '', title)
        title = title[:50]

        # Генерируем имя файла и заполняем свойство
        dtm = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_file = f"{dtm}_{title}.md"
        self.chat_file = os.path.join(self.chats_dir, self.chat_file)

        # frontmatter для файла
        epoch = int(datetime.now().timestamp() * 1000)
        if self.model_config:
            model_key = self.model_config.get("name", "") + "|" + self.model_config.get("provider", "")
        else:
            model_key = ""
        frontmatter = f"---\nepoch: {epoch}\nmodelKey: {model_key}\ntags:\n  - aichat\n---\n\n"

        # Создаем файл
        with open(self.chat_file, 'a', encoding='utf-8') as f:
            f.write(frontmatter)

    def save_message_to_file(self, role, content):
        """Сохраняет сообщение в файл"""
        if not self.chat_file:
            self.create_file(content)

        # Для совместимости с Obsidian Copilot нужно изменить имя роли ассистента
        role = "ai" if role == "assistant" else role

        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        with open(self.chat_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n**{role}**: {content}\n")
            f.write(f"[Timestamp: {timestamp}]")

    def load_all_chat_files(self):
        """Получает список чатов для загрузки"""
        self.all_chat_files = []
        for file in os.listdir(self.chats_dir):
            if os.path.isfile(os.path.join(self.chats_dir, file)):
                fname, fext = os.path.splitext(file)
                if fext == ".md":
                    self.all_chat_files.append(fname)
        self.all_chat_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.chats_dir, f + ".md")), reverse=True)

    def load_chat(self, new_chat):
        """Загружает чат из md-файла. Код взяла из плагина Copilot"""
        self.messages = []
        self.chat_file = os.path.join(self.chats_dir, new_chat + ".md")

        if not os.path.exists(self.chat_file):
            print(f"Файл чата не найден: {self.chat_file}")
            return

        with open(self.chat_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_sender = ""
        current_message = ""
        # current_timestamp = ""
        for line in lines:
            if line.startswith("**user**:") or line.startswith("**ai**:"):
                # Сохраняем предыдущее сообщение, если есть
                if current_sender and current_message:
                    self.messages.append({
                        'role': 'user' if current_sender == 'user' else 'assistant',
                        'content': current_message.strip()
                    })

                current_sender = 'user' if line.startswith("**user**:") else 'assistant'
                current_message = line.split(':', 1)[1].strip()
                # current_timestamp = ""
            elif line.startswith("[Timestamp:"):
                # Извлекаем временную метку
                # current_timestamp = line[11:-1].strip()
                pass
            else:
                # Добавляем строку к текущему сообщению
                current_message += '\n' + line

        # Добавляем последнее сообщение
        if current_sender and current_message:
            self.messages.append({
                'role': 'user' if current_sender == 'user' else 'assistant',
                'content': current_message.strip()
            })

    def remove_last_message(self):
        """Удаляет последнее сообщение в истории"""
        if not self.messages or len(self.messages) < 1:
            return

        self.messages = self.messages[:-1]

        if not self.chat_file or not os.path.exists(self.chat_file):
            return

        with open(self.chat_file, 'r', encoding='utf-8') as f:
            data = f.read()

        pattern = r'\*\*(user|ai)\*\*:.*?\[Timestamp: [^\]]+\](?:\s*\n)*'
        matches = list(re.finditer(pattern, data, flags=re.DOTALL))
        if not matches:
            return
        last_match = matches[-1]
        new_data = data[:last_match.start()] + data[last_match.end():]
        new_data = new_data.rstrip()
        with open(self.chat_file, 'w', encoding='utf-8') as f:
            f.write(new_data)

    def preview_context(self):
        result = ''
        for msg in self.messages[-4:]:
            role = "👤" if msg['role'] == "user" else "🤖"
            result += f"{role} {msg['content'][:20]}(...)\n"
        return result.strip()

    def view_context(self):
        result = ''
        for msg in self.messages[-4:]:
            role = "👤" if msg['role'] == "user" else "🤖"
            result += f"{role} {msg['content']}\n\n"
        return result.strip()
