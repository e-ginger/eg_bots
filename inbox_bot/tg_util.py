# tg_utils
# Some useful staff for working with Telegram
from datetime import datetime, timezone, timedelta


# Вспомогательная функция для даты
def dtm_from_timestamp(ts):
    dtm = datetime.fromtimestamp(ts, tz=None)
    dtm = dtm.astimezone(tz=timezone(offset=timedelta(hours=3)))
    return dtm


# Класс для сообщения
class TgMsg:

    def __init__(self, message, bot, known_users):
        # print("message", message)
        self.known_users = known_users
        self.message = message
        self.dtm = None
        self.text = ''
        self.files = {}
        self.user = ""

        if not message:
            return

        # дата
        if message.date:
            self.dtm = dtm_from_timestamp(message.date)

        # текст
        if message.text:
            self.text += message.text + '\n'
        if message.caption:
            self.text += message.caption + '\n'
        self.text = self.text.rstrip('\n ')

        # от кого сообщение
        self.user = self.parse_sender(message)

        # вложения
        if message.photo:
            # print('photo')
            best_photo = None
            for photo in message.photo:
                if not best_photo:
                    best_photo = photo
                else:
                    if photo.file_size > best_photo.file_size:
                        best_photo = photo
            if best_photo:
                file_info = bot.get_file(best_photo.file_id)
                filename = file_info.file_path.rsplit('_', 1)[1]
                file_data = bot.download_file(file_info.file_path)
                self.files[filename] = file_data

        if message.animation:
            # print('animation')
            file_info = bot.get_file(message.animation.file_id)
            filename = file_info.file_path.rsplit('_', 1)[1]
            file_data = bot.download_file(file_info.file_path)
            self.files[filename] = file_data

        if message.video:
            # print('video')
            file_info = bot.get_file(message.video.file_id)
            filename = file_info.file_path.rsplit('_', 1)[1]
            file_data = bot.download_file(file_info.file_path)
            self.files[filename] = file_data

        if message.voice:
            # print('voice')
            file_info = bot.get_file(message.voice.file_id)
            filename = file_info.file_path.rsplit('_', 1)[1]
            file_data = bot.download_file(file_info.file_path)
            self.files[filename] = file_data

        if message.video_note:
            # print('video_note')
            file_info = bot.get_file(message.video_note.file_id)
            filename = file_info.file_path.rsplit('_', 1)[1]
            file_data = bot.download_file(file_info.file_path)
            self.files[filename] = file_data

        if message.document:
            # print('document')
            file_info = bot.get_file(message.document.file_id)
            filename = message.document.file_name
            if filename:
                file_data = bot.download_file(file_info.file_path)
                self.files[filename] = file_data

    def parse_sender(self, message):
        if hasattr(message, 'forward_sender_name') and message.forward_sender_name:
            return message.forward_sender_name

        user = None
        if message.forward_from:
            user = message.forward_from
        elif message.forward_from_chat:
            user = message.forward_from_chat
        elif message.from_user:
            user = message.from_user

        if user and user.id and user.id in self.known_users:
            return self.known_users[user.id]

        if user:
            # print(user)
            result = ''
            if hasattr(user, 'username') and user.username:
                result += user.username
            if hasattr(user, 'firstname') and user.firstname:
                result += ' ' + user.firstname
            if hasattr(user, 'first_name') and user.first_name:
                result += ' ' + user.first_name
            if hasattr(user, 'lastname') and user.lastname:
                result += ' ' + user.lastname
            if hasattr(user, 'title') and user.title:
                result += ' ' + user.title
            result = result.lstrip(' ')
            if result and hasattr(user, 'username') and user.username:
                result = '[' + result + '](https://t.me/' + user.username + ')'

            if not result and user.id:
                result = str(user.id)
            return result

        return 'unknown sender'

    def __str__(self):
        result = '------- TgMsg --------\n'
        result += 'dtm: {}'.format(self.dtm) + '\n'
        result += 'text:{}'.format(self.text) + '\n'
        result += 'files: {}'.format(self.files.keys()) + '\n'
        result += 'user: {}'.format(self.user) + '\n'
        return result

