import logging
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from config import Config

# Настройка логирования
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Создаем асинхронного бота
bot = AsyncTeleBot(Config.BOT_TOKEN, parse_mode='HTML')

# Хранение данных пользователей
user_data = {}

def create_start_keyboard():
    """Клавиатура для начала теста"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🌍 Пройти тест"))
    return markup

def create_answer_keyboard():
    """Клавиатура с вариантами ответов"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(types.KeyboardButton("а"), types.KeyboardButton("б"), types.KeyboardButton("в"))
    return markup

@bot.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start и /help"""
    await bot.send_message(
        message.chat.id,
        "🌍 <b>Тест: Подходит ли тебе удалённая работа?</b>\n\n"
        "Узнай, готова ли ты к новому уровню свободы, самореализации и дохода — прямо из дома.",
        reply_markup=create_start_keyboard(),
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == "🌍 Пройти тест")
async def start_test(message: types.Message):
    """Начало теста"""
    user_id = message.from_user.id
    user_data[user_id] = {
        'answers': [],
        'current_question': 0,
        'username': message.from_user.username,
        'full_name': message.from_user.full_name,
        'score': 0
    }
    
    await ask_question(message, user_id)

async def ask_question(message: types.Message, user_id: int):
    """Задаем следующий вопрос пользователю с кнопками ответов"""
    current_question = user_data[user_id]['current_question']
    
    if current_question < len(Config.TEST_QUESTIONS):
        await bot.send_message(
            message.chat.id,
            Config.TEST_QUESTIONS[current_question],
            reply_markup=create_answer_keyboard()
        )
    else:
        await finish_test(message, user_id)

@bot.message_handler(func=lambda message: message.text.lower() in Config.ANSWER_SCORES.keys())
async def process_answer(message: types.Message):
    """Обработка ответов пользователя"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        await bot.send_message(message.chat.id, "Нажмите '🌍 Пройти тест' чтобы начать.")
        return
    
    answer = message.text.lower()
    user_data[user_id]['score'] += Config.ANSWER_SCORES[answer]
    user_data[user_id]['answers'].append(answer)
    user_data[user_id]['current_question'] += 1
    
    await ask_question(message, user_id)

@bot.message_handler(func=lambda message: True)
async def handle_other_messages(message: types.Message):
    """Обработка других сообщений"""
    user_id = message.from_user.id
    
    # Если пользователь проходит тест
    if user_id in user_data and user_data[user_id]['current_question'] < len(Config.TEST_QUESTIONS):
        await bot.send_message(
            message.chat.id,
            "Пожалуйста, выберите один из вариантов ответа:",
            reply_markup=create_answer_keyboard()
        )
    # Если пользователь ввел "Начать опрос" вместо кнопки
    elif message.text.lower() in ["начать опрос", "опрос", "тест"]:
        await start_test(message)
    else:
        await bot.send_message(
            message.chat.id,
            "Нажмите '🌍 Пройти тест' чтобы начать тестирование.",
            reply_markup=create_start_keyboard()
        )

async def finish_test(message: types.Message, user_id: int):
    """Завершение теста и вывод результатов"""
    user_info = user_data[user_id]
    total_score = user_info['score']
    
    # Определяем результат
    result_text = "💫 <b>Результаты теста:</b>\n\n"
    
    for score_range, result_description in Config.TEST_RESULTS.items():
        if score_range[0] <= total_score <= score_range[1]:
            result_text += result_description + "\n\n"
            break
    
    result_text += f"📊 <b>Ваш результат: {total_score} баллов</b>\n\n"
    result_text += "💌 Готова к первому шагу?\n\n"
    result_text += Config.CONTACT_TEXT
    
    # Отправляем результаты пользователю
    await bot.send_message(
        message.chat.id,
        result_text,
        parse_mode='HTML',
        reply_markup=create_start_keyboard()
    )
    
    # Отправляем результаты админу
    try:
        admin_text = f"📊 Новый результат теста:\n\n"
        admin_text += f"👤 Пользователь: @{user_info['username'] or 'нет'}\n"
        admin_text += f"🆔 ID: {user_id}\n"
        admin_text += f"📛 Имя: {user_info['full_name']}\n"
        admin_text += f"🎯 Баллы: {total_score}\n"
        admin_text += f"📝 Ответы: {', '.join(user_info['answers'])}"
        
        await bot.send_message(Config.ADMIN_CHAT_ID, admin_text)
        logger.info(f"Результаты теста отправлены админу {Config.ADMIN_CHAT_ID}")
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
    
    # Очищаем данные пользователя
    del user_data[user_id]
    logger.info(f"Тест завершен для пользователя {user_id}")

def get_bot_instance():
    """Возвращает экземпляр бота для использования в main.py"""
    return bot