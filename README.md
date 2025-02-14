# 🎅 Telegram-бот "Тайный Санта" 🎁


Этот Telegram-бот поможет вам организовать игру "Тайный Санта" среди ваших друзей, коллег или в сообществе! ✨ Бот берет на себя рутину жеребьевки, делая процесс простым и анонимным.

## 🚀 Возможности:

* **Регистрация участников:** ✍️  Пользователи могут легко зарегистрироваться для участия в игре.
* **Создание вишлистов:** 📝 Участники могут добавить список желаемых подарков, чтобы облегчить задачу своим Тайным Сантам. (Опционально!)
* **Анонимная жеребьевка:** 🤫 Бот случайным образом распределяет дарителей и получателей, гарантируя, что никто не получит себя в качестве подопечного.
* **Уведомления о подопечном:** 💌 Каждый участник получает личное сообщение от бота с информацией о том, кому он дарит подарок.
* **Настройки игры для администратора:** ⚙️
    * Открытие и закрытие регистрации.
    * Просмотр списка участников.
    * Добавление и удаление участников вручную.
    * Установка даты обмена подарками. 🗓️
    * Установка даты окончания регистрации. ⏳
    * Установка рекомендуемого бюджета подарка. 💰
    * Рассылка сообщений всем участникам. 📢

## 💻 Технологии:

* **Python:** 🐍 Основной язык программирования.
* **PyTelegramBotApi:** 📚 Библиотека для работы с Telegram Bot API.
* **SQLite:** 🗄️ Легковесная база данных для хранения информации (используется in-memory для простоты прототипа).

## ⚙️ Как использовать:

1. **Получите токен бота:** 🤖 Создайте нового бота через [@BotFather](https://t.me/BotFather) в Telegram и получите его токен.
2. **Клонируйте репозиторий:** ⬇️ `git clone https://github.com/Firecoding0/Secret-Santa`
3. **Установите зависимости:** 📦 `pip install pyTelegramBotApi`
4. **Настройте бота:** ✏️ Откройте файл с кодом (`ваш_файл.py`) и замените `"YOUR_TELEGRAM_BOT_TOKEN"` на токен вашего бота.
5. **Запустите бота:** ▶️ `python ваш_файл.py`
6. **Начните игру:** 🎉 Попросите участников начать общение с ботом, отправив команду `/start`!

## 📜 Лицензия:

Этот проект распространяется под лицензией **GNU General Public License v3.0**. Подробности смотрите в файле [LICENSE](LICENSE).

[![Лицензия: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## ✍️ Автор:

**firecoding** 🔥

## 🙏 Вклад:

Приветствуются любые предложения по улучшению и исправления ошибок! 😊
