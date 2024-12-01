import sqlite3
import telebot
from telebot import types
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота
bot = telebot.TeleBot('7754918991:AAGcSof33WVG-GTUy97GZVGCH7qPMYLDZnE')

# Подключение к базе данных SQLite
conn = sqlite3.connect('profiles.db', check_same_thread=False)
cursor = conn.cursor()


# Создание таблицы для хранения анкет
cursor.execute('''
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    rooms INTEGER,
    geolocation TEXT,
    photos TEXT,
    description TEXT
)
''')
conn.commit()

# Глобальная переменная для хранения состояния пользователя
user_state = {}
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    logging.info(f'User {message.chat.id} started the bot')
    bot.send_message(message.chat.id, 'Привет! гищдылах')

@bot.message_handler(commands=['myprofile'])
def myprofile(message):
    logging.info(f'User {message.chat.id} requested myprofile')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Создать анкету')
    btn2 = types.KeyboardButton('Удалить анкету')
    btn3 = types.KeyboardButton('Пожаловаться')
    markup.row(btn1)
    markup.row(btn2, btn3)
    bot.send_message(message.chat.id, 'Выберите функцию', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Создать анкету')
def fill_profile(message):
    logging.info(f'User {message.chat.id} started creating a profile')
    bot.send_message(message.chat.id, 'Укажите свое имя')
    user_state[message.chat.id] = 'waiting_for_name'

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_name')
def handle_name(message):
    user_name = message.text
    user_id = message.chat.id
    user_data[user_id] = {'user_name': user_name, 'photos': []}
    user_state[message.chat.id] = None
    logging.info(f'User {user_id} entered name: {user_name}')
    bot.send_message(message.chat.id, f'Ваше имя: {user_name}. Теперь укажите количество комнат.')
    user_state[message.chat.id] = 'waiting_for_rooms'

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_rooms')
def handle_room(message):
    rooms = message.text
    user_id = message.chat.id
    user_data[user_id]['rooms'] = rooms
    user_state[message.chat.id] = None
    logging.info(f'User {user_id} entered rooms: {rooms}')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_location = types.KeyboardButton('Отправить геолокацию', request_location=True)
    markup.add(btn_location)
    bot.send_message(message.chat.id, f'Количество комнат: {rooms}. Теперь добавьте местоположение.', reply_markup=markup)
    user_state[message.chat.id] = 'waiting_for_geolocation'

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_geolocation', content_types=['location'])
def handle_geolocation(message):
    location = message.location
    geolocation = f"{location.latitude},{location.longitude}"
    user_id = message.chat.id
    user_data[user_id]['geolocation'] = geolocation
    user_state[message.chat.id] = None
    logging.info(f'User {user_id} entered geolocation: {geolocation}')
    bot.send_message(message.chat.id, f'Местоположение: {geolocation}. Теперь отправьте фотографии.')
    user_state[message.chat.id] = 'waiting_for_photo_upload'

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_photo_upload', content_types=['photo'])
def handle_photo_upload(message):
    photo = message.photo[-1].file_id
    user_id = message.chat.id
    user_data[user_id]['photos'].append(photo)
    logging.info(f'User {user_id} uploaded photo with file_id: {photo}')
    bot.send_message(message.chat.id, 'Фотография добавлена. Добавьте еще фотографии или напишите "Готово", чтобы перейти к описанию.')
    user_state[message.chat.id] = 'waiting_for_photo_button'  # Возвращаемся к состоянию ожидания нажатия кнопки

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_photo_button' and message.text.lower() == 'готово')
def handle_photos_done(message):
    user_id = message.chat.id
    user_state[message.chat.id] = None
    bot.send_message(message.chat.id, 'Теперь добавьте описание.')
    user_state[message.chat.id] = 'waiting_for_description'

    
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_description')
def handle_description(message):
    description = message.text
    user_id = message.chat.id
    user_data[user_id]['description'] = description
    user_state[message.chat.id] = None
    logging.info(f'User {user_id} entered description: {description}')

    # Сохранение данных в базе данных
    photos = ', '.join(user_data[user_id]['photos'])
    cursor.execute('''
    INSERT INTO profiles (user_id, user_name, rooms, geolocation, photos, description)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_data[user_id]['user_name'], user_data[user_id]['rooms'], user_data[user_id]['geolocation'], photos, user_data[user_id]['description']))
    conn.commit()
    logging.info(f'User {user_id} profile saved to database')

    bot.send_message(message.chat.id, 'Ваша анкета сохранена!')

@bot.message_handler(func=lambda message: message.text == 'Пожаловаться')
def fill_profile(message):
    logging.info(f'User {message.chat.id} requested to complain')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Хочу снять')
    btn2 = types.KeyboardButton('Хочу сдать')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, 'Укажите причину жалобы', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Хочу снять')
def rent_appartment(message):
    logging.info(f'User {message.chat.id} wants to rent an apartment')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('1')
    btn2 = types.KeyboardButton('2')
    btn3 = types.KeyboardButton('3')
    btn4 = types.KeyboardButton('4')
    markup.row(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Количество комнат', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Хочу сдать')
def rentout_appartment(message):
    logging.info(f'User {message.chat.id} wants to rent out an apartment')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('1')
    btn2 = types.KeyboardButton('2')
    btn3 = types.KeyboardButton('3')
    btn4 = types.KeyboardButton('4')
    markup.row(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Количество комнат', reply_markup=markup)

# Запуск бота
logging.info('Starting bot polling...')
bot.polling()