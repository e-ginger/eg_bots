import json
import os


class Config:
    """Класс для работы с конфигурацией бота."""

    # Значения по умолчанию
    default = {
        "bot_token": "",
        "ai_system": "Ты полезный ассистент. Отвечай кратко и по существу.",
        "models_per_page": 5,
        "users": {
            "0": {
                "name": "",
                "chats_dir": "./chats",
                "models": ["ollama tinyllama"],
                "model": "ollama tinyllama",
                "max_context": 15
            }
        },
        "tts_model": {
            "name": "",
            "baseUrl": "",
            "apiKey": ""
        },
        "ai_models_list": [
            {
                "name": "dummy",
                "provider": "dummy",
                "enabled": True,
                "baseUrl": "",
                "apiKey": "",
                "capabilities": [],
                "stream": True,
                "enableCors": True,
                "displayName": "dummy"
            }
        ],
        "obsidian_vault": ""
    }

    def __init__(self):
        self.data = self.default

    def load_config(self):
        """Загружает конфигурацию из config.json или создает файл с настройками по умолчанию."""

        # Если файла нет, создаем его с настройками по умолчанию
        if not os.path.exists('config.json'):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print("Создан config.json с настройками по умолчанию. Заполните его!")
        else:
            # Читаем существующий конфиг
            with open('config.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)

        # Проверяем, что обязательные ключи есть и их значения не пустые
        for key in ["bot_token"]:
            if key not in self.data or not self.data[key]:
                raise ValueError(f"Ключ '{key}' отсутствует в config.json! Заполните его и перезапустите бота.")

        # Проверяем пользователей, должен быть хоть один
        users = self.get("users")
        if not users or len(users) < 1:
            raise ValueError("Пользователи не настроены в config.json! Заполните его и перезапустите бота.")

        # Проверяем модели, должны быть
        active_models = [model["displayName"] for model in self.get("ai_models_list") if model.get("enabled", False)]
        if not active_models or len(active_models) < 1:
            raise ValueError("Модели не настроены в config.json! Заполните его и перезапустите бота.")

        # Проверяем модели
        for user_id, user in users.items():
            for model in user.get("models", []):
                if model not in active_models:
                    raise ValueError(f"У пользователя {user_id} неактивная модель '{model}' в config.json!")
            model = user.get("model", "")
            if model not in active_models:
                raise ValueError(f"У пользователя {user_id} неактивная модель '{model}' в config.json!")

        # Проверяем, что директория для чатов существует
        for user_id, user in users.items():
            chats_dir = user.get("chats_dir", "")
            if not os.path.exists(chats_dir):
                raise ValueError(f"Путь для чатов '{chats_dir}' у пользователя {user} не существует! Создайте его и перезапустите бота.")

    def get(self, key):
        """Возвращает значение конфигурации по ключу."""
        return self.data.get(key, self.default.get(key))

    def get_model_config(self, model_name):
        """Возвращает конфигурацию модели или None, если модель не найдена или отключена."""
        if not model_name:
            return None
        for model in self.get("ai_models_list"):
            if model["displayName"] == model_name and model.get("enabled", False):
                return model
        return None
