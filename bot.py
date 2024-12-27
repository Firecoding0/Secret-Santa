import telebot
from telebot import types
import sqlite3
import random
from datetime import datetime
import logging

BOT_TOKEN = "bot token"
ADMIN_USER_ID = None

REGISTRATION_OPEN = False
GAME_STARTED = False
GIFT_EXCHANGE_DATE = None
END_REGISTRATION_DATE = None
GIFT_BUDGET = None

logging.basicConfig(filename='santa_bot_inline.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_NAME = 'santa_bot_inline.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None

def create_tables():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wishlists (
                    user_id INTEGER PRIMARY KEY,
                    wishlist TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()
            logging.info("Таблицы базы данных созданы или уже существуют.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при создании таблиц: {e}")
        finally:
            conn.close()

def get_game_setting(key):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM game_settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении настройки {key}: {e}")
        finally:
            conn.close()
    return None

def set_game_setting(key, value):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO game_settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
            logging.info(f"Настройка {key} установлена в {value}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка при установке настройки {key}: {e}")
        finally:
            conn.close()
    return False

def is_registered(user_id):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM participants WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return bool(result)
        except sqlite3.Error as e:
            logging.error(f"Ошибка при проверке регистрации пользователя {user_id}: {e}")
        finally:
            conn.close()
    return False

def register_participant(user_id, username):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO participants (user_id, username) VALUES (?, ?)", (user_id, username))
            conn.commit()
            logging.info(f"Пользователь {username} ({user_id}) зарегистрирован.")
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            logging.error(f"Ошибка при регистрации пользователя {username} ({user_id}): {e}")
        finally:
            conn.close()
    return False

def remove_participant(username):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM participants WHERE username = ?", (username,))
            conn.commit()
            logging.info(f"Пользователь {username} удален из списка участников.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка при удалении пользователя {username}: {e}")
        finally:
            conn.close()
    return False

def get_wishlist(user_id):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT wishlist FROM wishlists WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении списка желаний пользователя {user_id}: {e}")
        finally:
            conn.close()
    return None

def set_wishlist(user_id, wishlist):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO wishlists (user_id, wishlist) VALUES (?, ?)", (user_id, wishlist))
            conn.commit()
            logging.info(f"Список желаний пользователя {user_id} обновлен.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка при обновлении списка желаний пользователя {user_id}: {e}")
        finally:
            conn.close()
    return False

def get_participants():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, username FROM participants")
            participants = cursor.fetchall()
            return participants
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении списка участников: {e}")
        finally:
            conn.close()
    return []

def perform_drawing():
    participants = get_participants()
    if len(participants) < 2:
        return False

    givers = list(participants)
    receivers = list(participants)
    random.shuffle(receivers)

    for i in range(len(givers)):
        while givers[i][0] == receivers[i][0]:
            random.shuffle(receivers)

    drawing_results = dict(zip([giver[0] for giver in givers], [receiver[0] for receiver in receivers]))
    logging.info("Жеребьевка проведена успешно.")
    return drawing_results

def send_gift_assignments(bot, drawing_results):
    for giver_id, receiver_id in drawing_results.items():
        receiver_info = bot.get_chat(receiver_id)
        receiver_username = receiver_info.username if receiver_info.username else receiver_info.first_name

        wishlist = get_wishlist(receiver_id)
        message_text = f"🎅 Ты даришь подарок пользователю @{receiver_username}."
        if wishlist:
            message_text += f"\n\n🎁 Его/ее пожелания:\n{wishlist}"
        else:
            message_text += "\n\n🎁 У этого пользователя пока нет списка пожеланий."
        if GIFT_BUDGET:
            message_text += f"\n\n💰 Рекомендуемый бюджет подарка: {GIFT_BUDGET}."
        try:
            bot.send_message(giver_id, message_text)
            logging.info(f"Отправлено сообщение пользователю {giver_id} о его подопечном.")
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(f"Ошибка отправки сообщения пользователю {giver_id}: {e}")

def create_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    item_register = types.InlineKeyboardButton("🎁 Зарегистрироваться", callback_data='register')
    item_wishlist = types.InlineKeyboardButton("📝 Мой вишлист", callback_data='wishlist')
    item_help = types.InlineKeyboardButton("❓ Помощь", callback_data='help')
    markup.add(item_register, item_wishlist, item_help)
    return markup

def create_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    item_start_reg = types.InlineKeyboardButton("▶️ Начать регистрацию", callback_data='admin_start_registration')
    item_end_reg = types.InlineKeyboardButton("⏹️ Завершить регистрацию", callback_data='admin_end_registration')
    item_list_part = types.InlineKeyboardButton("👥 Список участников", callback_data='admin_list_participants')
    item_add_part = types.InlineKeyboardButton("➕ Добавить участника", callback_data='admin_add_participant')
    item_remove_part = types.InlineKeyboardButton("➖ Удалить участника", callback_data='admin_remove_participant')
    item_set_gift_date = types.InlineKeyboardButton("📅 Дата подарков", callback_data='admin_set_gift_date')
    item_set_end_reg_date = types.InlineKeyboardButton("📅 Окончание рег.", callback_data='admin_set_end_registration_date')
    item_set_budget = types.InlineKeyboardButton("💰 Бюджет", callback_data='admin_set_budget')
    item_broadcast = types.InlineKeyboardButton("📢 Сообщение", callback_data='admin_broadcast')
    markup.add(item_start_reg, item_end_reg, item_list_part, item_add_part, item_remove_part,
               item_set_gift_date, item_set_end_reg_date, item_set_budget, item_broadcast)
    return markup

bot = telebot.TeleBot(BOT_TOKEN)
user_wishlist_input = {}

@bot.message_handler(commands=['start'])
def start(message):
    global ADMIN_USER_ID
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name

    if ADMIN_USER_ID is None:
        ADMIN_USER_ID = user_id
        bot.send_message(message.chat.id, f"Привет, {username}! Ты первый запустил бота, поэтому ты стал администратором!", reply_markup=create_admin_keyboard())
        logging.info(f"Администратор установлен: {username} ({user_id})")
    else:
        bot.send_message(message.chat.id, f"Привет, {username}! Это бот для проведения Тайного Санты.", reply_markup=create_main_keyboard())

    status_message = "Текущий статус игры:\n"
    if not REGISTRATION_OPEN:
        status_message += "- Регистрация закрыта.\n"
    else:
        status_message += "- Регистрация открыта. Успейте зарегистрироваться!\n"

    if GIFT_EXCHANGE_DATE:
        status_message += f"- Дата обмена подарками: {GIFT_EXCHANGE_DATE.strftime('%Y-%m-%d')}\n"
    if GIFT_BUDGET:
        status_message += f"- Рекомендуемый бюджет подарка: {GIFT_BUDGET}\n"

    bot.send_message(message.chat.id, status_message)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global REGISTRATION_OPEN, GAME_STARTED, GIFT_EXCHANGE_DATE, END_REGISTRATION_DATE, GIFT_BUDGET, user_wishlist_input
    user_id = call.from_user.id

    if call.data == 'register':
        if not REGISTRATION_OPEN:
            bot.answer_callback_query(call.id, "Регистрация пока закрыта.")
        elif is_registered(user_id):
            bot.answer_callback_query(call.id, "Вы уже зарегистрированы.")
        else:
            username = call.from_user.username if call.from_user.username else call.from_user.first_name
            if register_participant(user_id, username):
                bot.answer_callback_query(call.id, "Вы успешно зарегистрированы!", show_alert=True)
                bot.send_message(user_id, "Вы успешно зарегистрированы для участия в Тайном Санте!", reply_markup=create_main_keyboard())
            else:
                bot.answer_callback_query(call.id, "Ошибка регистрации. Попробуйте позже.")

    elif call.data == 'wishlist':
        if not is_registered(user_id):
            bot.answer_callback_query(call.id, "Сначала зарегистрируйтесь.")
            return
        bot.send_message(call.message.chat.id, "Введите ваш список желаний (каждый пункт с новой строки):")
        user_wishlist_input[user_id] = True
        bot.register_next_step_handler(call.message, process_wishlist_input)

    elif call.data == 'help':
        help_text = """
Привет! Этот бот поможет организовать игру "Тайный Санта".

**Доступные действия:**
🎁 **Зарегистрироваться:**  Принять участие в игре.
📝 **Мой вишлист:**  Указать список желаемых подарков.
❓ **Помощь:**  Вывести это сообщение.
        """
        if call.from_user.id == ADMIN_USER_ID:
            help_text += "\n\n**Административные действия:**"
            help_text += "\n▶️ **Начать регистрацию:** Открыть регистрацию для участников."
            help_text += "\n⏹️ **Завершить регистрацию:** Закрыть регистрацию и провести жеребьевку."
            help_text += "\n👥 **Список участников:** Показать список зарегистрированных пользователей."
            help_text += "\n➕ **Добавить участника:** Добавить пользователя в список участников."
            help_text += "\n➖ **Удалить участника:** Удалить пользователя из списка участников."
            help_text += "\n📅 **Дата подарков:** Установить дату обмена подарками."
            help_text += "\n📅 **Окончание рег.:** Установить дату окончания регистрации."
            help_text += "\n💰 **Бюджет:** Установить рекомендуемый бюджет подарка."
            help_text += "\n📢 **Сообщение:** Отправить сообщение всем участникам."
        bot.send_message(user_id, help_text)

    elif call.data.startswith('admin_'):
        if call.from_user.id != ADMIN_USER_ID:
            bot.answer_callback_query(call.id, "Вы не администратор.")
            return

        if call.data == 'admin_start_registration':
            if REGISTRATION_OPEN:
                bot.answer_callback_query(call.id, "Регистрация уже открыта.")
            else:
                REGISTRATION_OPEN = True
                bot.answer_callback_query(call.id, "Регистрация открыта!", show_alert=True)
                bot.send_message(call.message.chat.id, "Регистрация на участие в Тайном Санте открыта!")
                logging.info("Администратор открыл регистрацию.")
        elif call.data == 'admin_end_registration':
            if not REGISTRATION_OPEN:
                bot.answer_callback_query(call.id, "Регистрация еще не была открыта.")
            elif GAME_STARTED:
                bot.answer_callback_query(call.id, "Игра уже началась.")
            else:
                REGISTRATION_OPEN = False
                GAME_STARTED = True
                drawing_results = perform_drawing()
                if drawing_results:
                    send_gift_assignments(bot, drawing_results)
                    bot.answer_callback_query(call.id, "Жеребьевка проведена!", show_alert=True)
                    bot.send_message(call.message.chat.id, "Регистрация закрыта, и участники получили информацию о том, кому дарят подарки!")
                    logging.info("Администратор закрыл регистрацию и провел жеребьевку.")
                else:
                    GAME_STARTED = False
                    bot.answer_callback_query(call.id, "Недостаточно участников.")
                    bot.send_message(call.message.chat.id, "Недостаточно участников для проведения жеребьевки.")
                    logging.warning("Недостаточно участников для жеребьевки.")
        elif call.data == 'admin_list_participants':
            participants = get_participants()
            if participants:
                participants_list = "\n".join([f"- @{p[1]}" for p in participants])
                bot.send_message(call.message.chat.id, f"Список участников:\n{participants_list}")
            else:
                bot.send_message(call.message.chat.id, "Еще нет зарегистрированных участников.")
        elif call.data == 'admin_add_participant':
            bot.send_message(call.message.chat.id, "Введите имя пользователя для добавления:")
            bot.register_next_step_handler(call.message, process_add_participant)
        elif call.data == 'admin_remove_participant':
            bot.send_message(call.message.chat.id, "Введите имя пользователя для удаления:")
            bot.register_next_step_handler(call.message, process_remove_participant)
        elif call.data == 'admin_set_gift_date':
            bot.send_message(call.message.chat.id, "Введите дату обмена подарками в формате ГГГГ-ММ-ДД:")
            bot.register_next_step_handler(call.message, process_set_gift_date)
        elif call.data == 'admin_set_end_registration_date':
            bot.send_message(call.message.chat.id, "Введите дату окончания регистрации в формате ГГГГ-ММ-ДД:")
            bot.register_next_step_handler(call.message, process_set_end_registration_date)
        elif call.data == 'admin_set_budget':
            bot.send_message(call.message.chat.id, "Введите рекомендуемый бюджет подарка:")
            bot.register_next_step_handler(call.message, process_set_budget)
        elif call.data == 'admin_broadcast':
            bot.send_message(call.message.chat.id, "Введите сообщение для рассылки:")
            bot.register_next_step_handler(call.message, process_broadcast_message)

        bot.answer_callback_query(call.id)

def process_wishlist_input(message):
    user_id = message.from_user.id
    if user_id in user_wishlist_input and user_wishlist_input[user_id]:
        wishlist = message.text
        if set_wishlist(user_id, wishlist):
            bot.send_message(message.chat.id, "Ваш список пожеланий сохранен!", reply_markup=create_main_keyboard())
        else:
            bot.send_message(message.chat.id, "Произошла ошибка при сохранении списка пожеланий.")
        del user_wishlist_input[user_id]

def process_add_participant(message):
    username_to_add = message.text
    if register_participant(None, username_to_add):
        bot.send_message(message.chat.id, f"Участник @{username_to_add} добавлен.", reply_markup=create_admin_keyboard())
    else:
        bot.send_message(message.chat.id, f"Не удалось добавить участника @{username_to_add}.", reply_markup=create_admin_keyboard())

def process_remove_participant(message):
    username_to_remove = message.text
    if remove_participant(username_to_remove):
        bot.send_message(message.chat.id, f"Участник @{username_to_remove} удален.", reply_markup=create_admin_keyboard())
    else:
        bot.send_message(message.chat.id, f"Не удалось удалить участника @{username_to_remove}.", reply_markup=create_admin_keyboard())

def process_set_gift_date(message):
    try:
        date_str = message.text
        global GIFT_EXCHANGE_DATE
        GIFT_EXCHANGE_DATE = datetime.strptime(date_str, '%Y-%m-%d').date()
        if set_game_setting('gift_exchange_date', str(GIFT_EXCHANGE_DATE)):
            bot.send_message(message.chat.id, f"Дата обмена подарками установлена на {GIFT_EXCHANGE_DATE.strftime('%Y-%m-%d')}.", reply_markup=create_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "Ошибка сохранения даты.", reply_markup=create_admin_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты.", reply_markup=create_admin_keyboard())

def process_set_end_registration_date(message):
    try:
        date_str = message.text
        global END_REGISTRATION_DATE
        END_REGISTRATION_DATE = datetime.strptime(date_str, '%Y-%m-%d').date()
        if set_game_setting('end_registration_date', str(END_REGISTRATION_DATE)):
            bot.send_message(message.chat.id, f"Дата окончания регистрации установлена на {END_REGISTRATION_DATE.strftime('%Y-%m-%d')}.", reply_markup=create_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "Ошибка сохранения даты.", reply_markup=create_admin_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты.", reply_markup=create_admin_keyboard())

def process_set_budget(message):
    try:
        budget = int(message.text)
        global GIFT_BUDGET
        GIFT_BUDGET = budget
        if set_game_setting('gift_budget', str(GIFT_BUDGET)):
            bot.send_message(message.chat.id, f"Бюджет установлен на {GIFT_BUDGET}.", reply_markup=create_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "Ошибка сохранения бюджета.", reply_markup=create_admin_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат бюджета.", reply_markup=create_admin_keyboard())

def process_broadcast_message(message):
    message_to_send = message.text
    participants = get_participants()
    for user_id, username in participants:
        try:
            bot.send_message(user_id, f"📢 Сообщение от администратора:\n{message_to_send}")
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(message.chat.id, f"Не удалось отправить сообщение пользователю {username} ({user_id}).", reply_markup=create_admin_keyboard())
    bot.send_message(message.chat.id, "Сообщение отправлено всем участникам.", reply_markup=create_admin_keyboard())

if __name__ == '__main__':
    create_tables()
    print("Бот запущен...")
    logging.info("Бот запущен.")
    bot.polling(none_stop=True)