    #by @killerskype 2days

import os
import re
import json
import tempfile
import sqlite3
import logging
import uuid
import asyncio
import aiohttp
import random
import string
from datetime import datetime, timedelta
from aiogram.types import InputFile
from telethon import functions
from aiogram.utils.exceptions import TelegramAPIError
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonSpam, InputReportReasonViolence, InputReportReasonPornography, InputReportReasonChildAbuse, InputReportReasonOther
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiocryptopay import AioCryptoPay, Networks
from telethon.tl.types import InputReportReasonSpam, User, Channel, Chat
from logging.handlers import RotatingFileHandler
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.types import InputChannel
from telethon.sessions import SQLiteSession, StringSession
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
from telethon.tl.types import InputPeerChannel, Channel
CURRENT_DISCOUNT_PERCENT = 0.0  # скидка по умолчанию отключена

import sqlite3


# Монопатч для предотвращения интерактивного ввода
import builtins
original_input = builtins.input

def non_interactive_input(prompt=""):
    logging.warning(f"Попытка интерактивного ввода с промптом: {prompt}")
    if "phone" in prompt.lower() or "bot token" in prompt.lower():
        # Просто логируем, но не запрашиваем ввод
        raise RuntimeError(f"Попытка запросить интерактивный ввод: {prompt}")
    return original_input(prompt)

builtins.input = non_interactive_input

with open('config.json') as f:
    config = json.load(f)
API_TOKEN = config['bot_token']
API_ID = config['API_ID']
API_HASH = config['API_HASH']
ADMIN_IDS = config['admin_ids']
DB_NAME = 'subscriptions.db'
SESSIONS_DIR = 'sessions'
LOG_CHANNEL_ID = config['LOG_CHANNEL_ID']
BOT_USERNAME = config['bot_username']
MENU_PHOTO = config["menu_photo"]
image_path = "menu.jpg"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

send_reports_lock = asyncio.Lock()

def log_to_file(text: str):
    with open("report_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now().isoformat()} — {text}\n")

# Принудительная очистка старых обработчиков
root_logger = logging.getLogger()
root_logger.handlers = []

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ротирующий файловый обработчик
handler = RotatingFileHandler(
    'bot.log',
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=3,
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Вывод логов в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("🔄 Логгер инициализирован! Проверка записи...")

# Состояния FSM
class ReportStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_reason = State()

# Admin FSM States
class AdminStates(StatesGroup):
    waiting_for_sub_user_id = State()
    waiting_for_sub_days = State()
    waiting_for_unsub_user_id = State()
    waiting_for_balance_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_wl_user_id = State()
    waiting_for_remove_wl_user_id = State()
    waiting_for_bl_user_id = State()
    waiting_for_bl_reason = State()
    waiting_for_unbl_user_id = State()
    waiting_for_user_info_id = State()
    waiting_for_broadcast_message = State()
    waiting_for_discount_percent = State()
    waiting_for_promo_days = State()

class PaymentStates(StatesGroup):
    amount = State()
    confirm_payment = State()
    buy_subscription = State() 

# Состояния FSM для промокодов
class PromoStates(StatesGroup):
    waiting_for_code = State()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TEXT NOT NULL,
            subscription_end TEXT,
            referrer_id INTEGER,
            balance REAL DEFAULT 0.0,
            valid_referrals INTEGER DEFAULT 0,
            referral_cycles INTEGER DEFAULT 0,
            is_bot BOOLEAN DEFAULT FALSE,
            channel_subscription BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Таблица платежей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            invoice_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            message_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица белого списка
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whitelist (
            user_id INTEGER,
            group_id INTEGER,
            added_by INTEGER,
            added_at TEXT NOT NULL
        )
    ''')
    
    # Таблица логов (если требуется)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Таблица промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            days INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            used_by INTEGER,
            used_at TEXT
        )
    ''')
    
    # Таблица черного списка
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER NOT NULL,
            reason TEXT,
            added_at TEXT NOT NULL
        )
    ''')
    
    # Индексы для оптимизации
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_subscription 
        ON users(subscription_end)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_payments_user 
        ON payments(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_whitelist_group 
        ON whitelist(group_id)
    ''')
    
    conn.commit()
    conn.close()

def is_reporting_enabled():
    if not os.path.exists("reports_enabled.txt"):
        return True  # По умолчанию включено
    with open("reports_enabled.txt", "r") as f:
        return f.read().strip() == "1"

def check_channel_subscription_db(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_subscription FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def set_reporting_enabled(enabled: bool):
    with open("reports_enabled.txt", "w") as f:
        f.write("1" if enabled else "0")


async def save_payment_to_db(invoice_id: str, user_id: int, amount: float, message_id: int):
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO payments 
            (invoice_id, user_id, amount, created_at, message_id) 
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_id, user_id, amount, created_at, message_id))
        conn.commit()
    finally:
        conn.close()

def check_whitelist_table():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='whitelist'
        ''')
        if not cursor.fetchone():
            logging.critical("Whitelist table not found!")
            raise RuntimeError("Whitelist table missing")

def log_to_file(text: str):
    with open("report_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now().isoformat()} — {text}\n")

def check_db_schema():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    print("Структура таблицы users:")
    for column in cursor.fetchall():
        print(column)
    conn.close()

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user or [None] * 4  # Возвращает список с None, если пользователя нет

def safe_init_db():
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        raise

def migrate_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE whitelist ADD COLUMN group_id INTEGER')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def add_user(user_id: int, join_date: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, join_date) 
        VALUES (?, ?)
    ''', (user_id, join_date))
    conn.commit()
    conn.close()

def check_subscription(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT subscription_end FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result[0]:
        return False

    subscription_end = datetime.fromisoformat(result[0])
    return datetime.now() < subscription_end

@dp.message_handler(commands=['debug_group'])
async def debug_group(message: types.Message):
    try:
        group_id = int(config["LOG_CHANNEL_ID"])
        chat = await bot.get_chat(group_id)
        await message.answer(f"""
            🧰 Информация о группе:
            ID: {chat.id}
            Тип: {chat.type}
            Название: {chat.title}
            Права бота: {chat.permissions.can_send_messages}
        """)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

def update_subscription(user_id: int, subscription_end: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET subscription_end = ?
        WHERE user_id = ?
    ''', (subscription_end, user_id))
    conn.commit()
    conn.close()

def setup_crypto() -> AioCryptoPay:
    return AioCryptoPay(
        token=config['crypto_pay_token'],
        network=Networks.MAIN_NET,
        session=aiohttp.ClientSession()
    )


def get_main_menu_keyboard(user_id=None):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🧸 | заказать пиццу", callback_data="cn0c"),
        types.InlineKeyboardButton("👤 | Профиль", callback_data="profile"),
        types.InlineKeyboardButton("👥 | Реферал", callback_data="referral"),
        types.InlineKeyboardButton("💳 | купить шоколад ", callback_data="topup_start"),
        types.InlineKeyboardButton("ℹ️ | fobio pizza info", callback_data="info"),
        types.InlineKeyboardButton("🎁 | Промокод", callback_data="promo_activate")
    ]
    
    # Add admin menu button if user is admin
    if user_id and user_id in ADMIN_IDS:
        buttons.append(types.InlineKeyboardButton("🔧 | Админ меню", callback_data="admin_menu"))
    
    keyboard.add(*buttons[:2])
    keyboard.add(buttons[2])
    keyboard.add(buttons[3])
    keyboard.add(buttons[4])
    keyboard.add(buttons[5])
    if len(buttons) > 6:  # Add admin button if present
        keyboard.add(buttons[6])
    return keyboard

def is_in_whitelist(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM whitelist WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_in_blacklist(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM blacklist WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("✖️ Отмена", callback_data="cancel_payment")
    )
    return keyboard

def get_subscription_plans_keyboard():
    global CURRENT_DISCOUNT_PERCENT

    PRICES = {
        '1': {'days': 1, 'price': 2},
        '7': {'days': 7, 'price': 5},
        '30': {'days': 30, 'price': 9},
        'lifetime': {'days': 36500, 'price': 20},
        'channel': {'days': 36500, 'price': 3}
    }

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for key, plan in PRICES.items():
        price = plan['price']
        if key != '1' and CURRENT_DISCOUNT_PERCENT > 0:
            discount = price * (CURRENT_DISCOUNT_PERCENT / 100)
            price -= discount
            price = round(price, 2)
        label = ""
        if key == '1':
            label = f"1️⃣ 1 день - {price}$"
        elif key == '7':
            label = f"7️⃣ 7 дней - {price}$"
        elif key == '30':
            label = f"3️⃣0️⃣ 30 дней - {price}$"
        elif key == 'lifetime':
            label = f"♾️ Lifetime - {price}$"
        elif key == 'channel':
            label = f"💥 пицца для каналов (навсегда) - {price}$"

        keyboard.add(types.InlineKeyboardButton(label, callback_data=f"sub_{key}"))

    keyboard.add(types.InlineKeyboardButton("🔰 | Назад", callback_data="back_to_menu"))
    return keyboard

def get_admin_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🔧 Управление подписками", callback_data="admin_subscriptions"),
        types.InlineKeyboardButton("💰 Управление балансом", callback_data="admin_balance"),
        types.InlineKeyboardButton("📋 Whitelist/Blacklist", callback_data="admin_wl_bl"),
        types.InlineKeyboardButton("🧮 Скидки", callback_data="admin_discounts"),
        types.InlineKeyboardButton("📬 Рассылка и отладка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("📄 Инфо по пользователям", callback_data="admin_user_info"),
        types.InlineKeyboardButton("🔄 Управление репортами", callback_data="admin_reports"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="back_to_menu")
    )
    return keyboard

def get_subscriptions_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📅 Выдать подписку", callback_data="admin_sub_grant"),
        types.InlineKeyboardButton("❌ Отменить подписку", callback_data="admin_sub_revoke"),
        types.InlineKeyboardButton("📋 Выгрузить всех с подпиской", callback_data="admin_sub_list"),
        types.InlineKeyboardButton("🎁 Создать промокод", callback_data="admin_promo_create"),
        types.InlineKeyboardButton("📜 Список всех промокодов", callback_data="admin_promo_list"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="admin_menu")
    )
    return keyboard

def get_balance_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("➕ Увеличить баланс", callback_data="admin_balance_add"),
        types.InlineKeyboardButton("➖ Уменьшить баланс", callback_data="admin_balance_sub"),
        types.InlineKeyboardButton("📊 Баланс всех", callback_data="admin_balance_list"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="admin_menu")
    )
    return keyboard

def get_wl_bl_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("➕ Добавить в whitelist", callback_data="admin_wl_add"),
        types.InlineKeyboardButton("➖ Удалить из whitelist", callback_data="admin_wl_remove"),
        types.InlineKeyboardButton("⛔ Добавить в blacklist", callback_data="admin_bl_add"),
        types.InlineKeyboardButton("✅ Удалить из blacklist", callback_data="admin_bl_remove"),
        types.InlineKeyboardButton("📋 Список всех в blacklist", callback_data="admin_bl_list"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="admin_menu")
    )
    return keyboard

def get_broadcast_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📢 рассылка", callback_data="admin_broadcast_send"),
        types.InlineKeyboardButton("📝 Тест лог-сообщения", callback_data="admin_test_log"),
        types.InlineKeyboardButton("🛠 Проверить лог-группу", callback_data="admin_debug_group"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="admin_menu")
    )
    return keyboard

def get_discounts_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("♻️ Убрать все скидки", callback_data="discount_reset"),
        InlineKeyboardButton("📉 Старт скидки", callback_data="discount_start"),
        InlineKeyboardButton("🔰 Назад", callback_data="admin_menu")
    )
    return keyboard

def get_reports_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("❌ Отключить репорты", callback_data="admin_reports_stop"),
        types.InlineKeyboardButton("✅ Включить репорты", callback_data="admin_reports_go"),
        types.InlineKeyboardButton("🔰 | Назад", callback_data="admin_menu")
    )
    return keyboard

async def check_channel_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=config['CHANNEL_ID'],
            user_id=user_id
        )
        return member.status not in ['left', 'kicked']
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {str(e)}")
        return False

from datetime import datetime, timedelta

@dp.callback_query_handler(lambda c: c.data == 'admin_discounts')
async def show_discount_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ Нет доступа", show_alert=True)
        return
    await bot.send_message(
        callback_query.from_user.id,
        "🧮 Управление скидками",
        reply_markup=get_discounts_menu_keyboard()
    )
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'discount_reset')
async def discount_reset(callback_query: types.CallbackQuery):
    global CURRENT_DISCOUNT_PERCENT
    CURRENT_DISCOUNT_PERCENT = 0.0
    await bot.send_message(callback_query.from_user.id, "✅ Все скидки отключены.")
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'discount_start')
async def discount_start(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "📉 Введите размер скидки (например, 12.5):")
    await AdminStates.waiting_for_discount_percent.set()
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_discount_percent)
async def set_discount_percent(message: types.Message, state: FSMContext):
    global CURRENT_DISCOUNT_PERCENT
    try:
        percent = float(message.text)
        if 0 <= percent <= 100:
            CURRENT_DISCOUNT_PERCENT = percent
            await message.answer(f"✅ Скидка {percent:.1f}% применена ко всем тарифам (кроме 1 дня).")
        else:
            await message.answer("❌ Введите число от 0 до 100.")
    except ValueError:
        await message.answer("❌ Введите корректное число.")
    await state.finish()


@dp.message_handler(commands=['send'])
async def broadcast_message(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return

    text = message.get_args()
    if not text:
        await message.answer("⚠️ Используйте: /send текст_рассылки")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users")
        user_ids = cursor.fetchall()
        sent_count = 0
        for user_id_tuple in user_ids:
            user_id = user_id_tuple[0]
            try:
                await bot.send_message(user_id, text)
                sent_count += 1
                await asyncio.sleep(0.05)  # чтобы не словить FloodWait
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {str(e)}")

        await message.answer(f"📤 Рассылка завершена. Отправлено {sent_count} сообщений.")
    except Exception as e:
        logging.error(f"Ошибка при рассылке: {str(e)}")
        await message.answer("❌ Произошла ошибка при рассылке.")
    finally:
        conn.close()


@dp.callback_query_handler(lambda c: c.data == "check_channel")
async def process_check_channel(callback_query: types.CallbackQuery):
    CHANNEL_ID = '-1002555772717'
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=callback_query.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            await callback_query.message.edit_text("✅ Подписка подтверждена! Теперь нажмите /start.")
        else:
            await callback_query.answer("❗ Вы всё ещё не подписаны.", show_alert=True)
    except:
        await callback_query.answer("⚠️ Ошибка проверки. Попробуйте позже.", show_alert=True)


@dp.callback_query_handler(lambda c: c.data == 'buy_channel_sub')
async def handle_buy_channel_sub(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    await bot.send_message(
        user_id,
        "💥 Навсегда разблокирует возможность заказывать пиццу для каналов.\n"
        "💳 Стоимость: $.\n\n"
        "Нажмите кнопку ниже, чтобы оплатить:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("💰 Оплатить", url="https://pay.lava.ru/your_link")
        )
    )
    await bot.answer_callback_query(callback_query.id)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 🔒 Проверка на чёрный список
    if is_in_blacklist(user.id):
        await message.answer(
            f"⛔ Вы были внесены в чёрный список проекта. Вопросы? @{config.get('admin_contact', 'teppupvp')}"
        )
        return

    CHANNEL_ID = '-1002641582538'  # ← свой канал

    # 🔒 Проверка подписки
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("🔗 Подписаться", url="https://t.me/+WWshbrP-ZGA0ZTcx")
            )
            await message.answer(
                "Чтобы использовать бота, подпишитесь на наш канал.\nЗатем нажмите /start ещё раз.",
                reply_markup=markup
            )
            return
    except Exception:
        await message.answer("⚠️ Ошибка при проверке подписки. Попробуйте позже.")
        return

    try:
        # 📌 Реферальная система
        referrer_id = None
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            if ref_code.startswith('ref_'):
                try:
                    referrer_id = int(ref_code.split('_')[1])
                    if referrer_id == user.id:
                        referrer_id = None
                except:
                    pass

        # 🔍 Проверка существующего пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user.id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # 📅 Регистрация нового пользователя
            join_date = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, join_date, referrer_id, is_bot) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user.id, user.username, join_date, referrer_id, user.is_bot))
            conn.commit()

            # 📣 Уведомление админам
            try:
                ref_text = "без реферала"
                if referrer_id:
                    ref_text = f"реферал от: <code>{referrer_id}</code>"

                for admin_id in ADMIN_IDS:
                    await bot.send_message(
                        admin_id,
                        f"🆕 Новый пользователь:\n"
                        f"👤 ID: <code>{user.id}</code>\n"
                        f"📛 Имя: @{user.username}\n"
                        f"📅 Регистрация: {join_date}\n"
                        f"👥 Реферал: {ref_text}",
                        parse_mode="HTML"
                    )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления админам: {e}")

            # 🙋 Уведомление рефереру
            if referrer_id:
                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 По вашей ссылке зарегистрирован новый пользователь: @{user.username}!"
                    )
                except:
                    pass  # возможно реферер удалил бота

        # 📷 Отправка главного меню
        try:
            await message.answer_photo(
                photo=InputFile(config['menu_photo']),
                caption="<b>👋 | Приветствуем в FOBIO PIZZA! Выберите действие:</b>",
                reply_markup=get_main_menu_keyboard(user_id=message.from_user.id),
                parse_mode="HTML"
            )
        except FileNotFoundError:
            await message.answer(
                "<b>👋 | Приветствуем в FOBIO PIZZA! Выберите действие:</b>",
                reply_markup=get_main_menu_keyboard(user_id=message.from_user.id),
                parse_mode="HTML"
            )

    except sqlite3.Error as e:
        logging.error(f"Ошибка БД: {str(e)}")
    finally:
        conn.close()

@dp.callback_query_handler(lambda c: c.data == 'info')
async def show_info(callback_query: types.CallbackQuery):
    info_text = (
        "<b>ℹ️ Информация о боте</b>\n\n"
        "Добро пожаловать в Fobio — мощный инструмент для заказа пиццы\n\n"
        "🔹 <b>Основные функции:</b>\n"
        "- 💣 заказать пиццу: Отправка пиццы при помощи телеграмма на агрес с выбором начинки .\n"
        "- 💰 купить шоколадки: Пополнение шоколадок через криптобота или карту .\n"
        "- 🎟 доставка: Покупка доставки для доступа к заказам.\n"
        "- 👥 Рефералка: Приглашайте друзей и получайте подписку.\n"
        "- 👤 Профиль: Просмотр шоколадок, статуса подписки и даты регистрации.\n\n"
        "🔹 <b>Как работает реферальная система?</b>\n"
        "Поделитесь своей уникальной ссылкой с друзьями. Когда 20 человек зарегистрируются по вашей ссылке, вы получите подписку.\n\n"
        "🔹 <b>Контакты и поддержка:</b>\n"
        "Если у вас есть вопросы или проблемы, свяжитесь с поддержкой — @teppupvp\n\n"
        "🚀 <b>Создатель:</b> @piramonov"
        "🚀 <b>тутор как правильно отправлять пиццу:</b> https://telegra.ph/Na-chto-otpravlyat-reporty-06-06 "
    )

    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=info_text,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔰 | Назад", callback_data="back_to_menu")
        ),
        parse_mode="HTML"
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'topup_start')
async def topup_method_selection(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Пополнить через CryptoBot", callback_data="topup_crypto"),
        InlineKeyboardButton("💳 Пополнить картой", callback_data="topup_card"),
        InlineKeyboardButton("🔰 Назад", callback_data="back_to_menu")
    )
    await bot.send_message(
        callback_query.from_user.id,
        "💸 Выберите способ пополнения:",
        reply_markup=keyboard
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'topup_crypto')
async def topup_crypto_handler(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "💸 Введите сумму пополнения от 1 до 999 USDT:")
    await PaymentStates.amount.set()
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'topup_card')
async def topup_card_handler(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "💳 Для оплаты картой напишите: @piramonov",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Назад", callback_data="topup_start")
        )
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('check_'))
async def check_payment(callback_query: types.CallbackQuery):
    invoice_id = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    async with AioCryptoPay(
        token=config['crypto_pay_token'],
        network=Networks.MAIN_NET
    ) as crypto:
        try:
            invoices = await crypto.get_invoices(invoice_ids=invoice_id)
            
            if not invoices:
                await bot.send_message(user_id, "❌ Счет не найден")
                return

            invoice = invoices[0]

            if invoice.status == "paid":
                conn = sqlite3.connect(DB_NAME)
                try:
                    cursor = conn.cursor()
                    cursor.execute('SELECT message_id, amount FROM payments WHERE invoice_id = ?', (invoice_id,))
                    message_id, amount = cursor.fetchone()

                    if message_id:
                        try:
                            await bot.delete_message(user_id, message_id)
                        except Exception as e:
                            logging.error(f"Ошибка удаления сообщения: {str(e)}")

                    cursor.execute('''
                        UPDATE payments 
                        SET 
                            status = 'paid', 
                            updated_at = ?
                        WHERE invoice_id = ?
                    ''', (datetime.now().isoformat(), invoice_id))

                    cursor.execute('''
                        UPDATE users 
                        SET balance = balance + ? 
                        WHERE user_id = ?
                    ''', (amount, user_id))
                    conn.commit()

                    # Отправка фото с подтверждением оплаты
                    try:
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=InputFile(config['menu_photo']),  # Путь к main.jpg
                            caption=f"✅ Оплата {amount} USDT подтверждена!",
                            reply_markup=get_main_menu_keyboard()
                        )
                    except FileNotFoundError:
                        await bot.send_message(
                            user_id,
                            f"✅ Оплата {amount} USDT подтверждена!",
                            reply_markup=get_main_menu_keyboard()
                        )

                except sqlite3.Error as e:
                    logging.error(f"Ошибка БД: {str(e)}")
                    await bot.send_message(user_id, "⚠️ Ошибка обработки платежа")
                finally:
                    conn.close()

            else:
                await bot.send_message(
                    user_id,
                    "⌛ Платеж еще не подтвержден",
                )

        except Exception as e:
            logging.error(f"Check payment error: {str(e)}", exc_info=True)
            await bot.send_message(user_id, "⚠️ Ошибка при проверке платежа")

    await bot.answer_callback_query(callback_query.id)


async def create_payment(user_id: int, amount: float):
    async with AioCryptoPay(
        token=config['crypto_pay_token'],
        network=Networks.MAIN_NET
    ) as crypto:
        try:
            invoice = await crypto.create_invoice(asset='USDT', amount=round(amount, 2))
            message = await bot.send_message( 
                user_id,
                f"💸 Ссылка для оплаты: {invoice.bot_invoice_url}",
                reply_markup=payment_check_keyboard(invoice.invoice_id)
            )
            
            await save_payment_to_db(
                invoice_id=invoice.invoice_id,
                user_id=user_id,
                amount=amount,
                message_id=message.message_id 
            )
            
        except Exception as e:
            logging.error(f"Payment error: {str(e)}")
            await bot.send_message(user_id, "❌ Ошибка создания платежа")



@dp.message_handler(state=PaymentStates.amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if 1 <= amount <= 999:
            await state.update_data(amount=amount)
            await PaymentStates.confirm_payment.set()
            await message.answer(
                f"Подтвердите пополнение на {amount} USDT",
                reply_markup=confirm_keyboard()  
            )
        else:
            await message.answer("❌ Сумма должна быть от 1 до 999 USDT!")
            await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число!")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'confirm', state=PaymentStates.confirm_payment)
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await create_payment(callback_query.from_user.id, data['amount'])
    await state.finish()
    await bot.answer_callback_query(callback_query.id, "✅ Платеж создан!")

def payment_check_keyboard(invoice_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_{invoice_id}")
    )





@dp.callback_query_handler(lambda c: c.data == 'profile')
async def show_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем данные пользователя
    cursor.execute('''
        SELECT join_date, subscription_end, balance 
        FROM users 
        WHERE user_id = ?
    ''', (user_id,))
    user_data = cursor.fetchone()
    
    # Проверяем наличие в белом списке
    cursor.execute('''
        SELECT 1 
        FROM whitelist 
        WHERE user_id = ?
    ''', (user_id,))
    in_whitelist = "🪬 Да" if cursor.fetchone() else "✖️ Нет"
    
    conn.close()

    # Формируем текст профиля
    if user_data:
        join_date = datetime.fromisoformat(user_data[0]).strftime("%d.%m.%Y %H:%M")
        subscription_status = (
            "🪬 Активна до " + datetime.fromisoformat(user_data[1]).strftime("%d.%m.%Y %H:%M")
            if user_data[1] and datetime.now() < datetime.fromisoformat(user_data[1])
            else "✖️ Неактивна"
        )
        balance = f"{user_data[2]:.2f}$" if user_data[2] else "0.00$"


        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_subscription FROM users WHERE user_id = ?", (user_id,))
        ch_sub = cursor.fetchone()
        conn.close()

        channel_status = "✅ Активна" if ch_sub and ch_sub[0] else "✖️ Неактивна"
        
        profile_text = (
            f"👤 <b>| Ваш профиль</b>\n\n"
            f"🆔 <b>| ID</b>: <code>{user_id}</code>\n"
            f"📅 <b>| Дата регистрации</b>: <code>{join_date}</code>\n"
            f"🛡️ <b>| Вайтлист</b>: <code>{in_whitelist}</code>\n"
            f"💎 <b>| Доставка</b>: <code>{subscription_status}</code>\n"
            f"💸 <b>| шоколадки</b>: <code>{balance}</code>"
            f"📣 <b>| заказы на каналы</b>: <code>{channel_status}</code>\n"
        )
    else:
        profile_text = "❌ Профиль не найден, /start напишите ещё раз."

    # Отправка сообщения с фото
    try:
        photo = InputFile(config['profile_photo'])
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=photo,
            caption=profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode="HTML"
        )
    
    # Удаляем предыдущее сообщение
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )

def get_profile_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🛒 | Купить доставку", callback_data="buy_subscription"),
        types.InlineKeyboardButton("🔰 | Назад ", callback_data="back_to_menu")
    )
    return keyboard

@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def back_to_menu(callback_query: types.CallbackQuery):
    try:
        photo = InputFile(config['menu_photo'])
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=photo,
            caption="<b>🚀 | Вы вернулись в главное меню FOBIO PIZZA</b>",
            reply_markup=get_main_menu_keyboard(user_id=callback_query.from_user.id),
            parse_mode="HTML"
        )
    except FileNotFoundError:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )

@dp.callback_query_handler(lambda c: c.data == 'buy_subscription')
async def show_subscription_plans(callback_query: types.CallbackQuery):
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="💰 Выберите тарифный план:",
        reply_markup=get_subscription_plans_keyboard()
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('sub_'))
async def process_subscription_purchase(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    plan_type = callback_query.data.split('_')[1]
    
    PRICES = {
        '1': {'days': 1, 'price': 2},
        '7': {'days': 7, 'price': 5},
        '30': {'days': 30, 'price': 9},
        'lifetime': {'days': 36500, 'price': 20},
        'channel': {'days': 36500, 'price': 3}
    }

    user = get_user(user_id)
    if not user:
        await bot.answer_callback_query(callback_query.id, "❌ Ошибка профиля")
        return

    plan = PRICES.get(plan_type)
    if not plan:
        await bot.answer_callback_query(callback_query.id, "❌ Неверный тариф")
        return

    # ✅ Применяем скидку (кроме тарифа на 1 день)
    global CURRENT_DISCOUNT_PERCENT
    if plan_type != '1' and CURRENT_DISCOUNT_PERCENT > 0:
        discount = plan['price'] * (CURRENT_DISCOUNT_PERCENT / 100)
        plan['price'] -= discount
        plan['price'] = round(plan['price'], 2)

    # ✅ Проверка баланса
    if float(user[5]) < plan['price']:
        await bot.answer_callback_query(
            callback_query.id,
            f"❌ Недостаточно средств. Нужно {plan['price']}$",
            show_alert=True
        )
        return

    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()

        if plan_type == 'channel':
            cursor.execute('''
                UPDATE users 
                SET 
                    channel_subscription = 1,
                    balance = balance - ?
                WHERE user_id = ?
            ''', (plan['price'], user_id))
            conn.commit()

            await bot.send_message(
                user_id,
                f"✅ доставка на заказ каналов активирована навсегда!\n"
                f"💸 Списано: {plan['price']}$",
                reply_markup=get_main_menu_keyboard()
            )

        else:
            new_end = datetime.now()
            if user[2]: 
                current_end = datetime.fromisoformat(user[2])
                if current_end > datetime.now():
                    new_end = current_end

            new_end += timedelta(days=plan['days'])

            cursor.execute('''
                UPDATE users 
                SET 
                    subscription_end = ?,
                    balance = balance - ?
                WHERE user_id = ?
            ''', (new_end.isoformat(), plan['price'], user_id))
            conn.commit()

            await bot.send_photo(
                chat_id=user_id,
                photo=InputFile(config['menu_photo']),
                caption=(
                    f"✅ доставка активирована!\n"
                    f"📅 Окончание: {new_end.strftime('%d.%m.%Y %H:%M')}\n"
                    f"💸 Списано: {plan['price']}$"
                ),
                reply_markup=get_main_menu_keyboard()
            )

    except Exception as e:
        logging.error(f"Ошибка при покупке подписки ({plan_type}): {str(e)}")
        await bot.answer_callback_query(callback_query.id, "❌ Ошибка транзакции")
    finally:
        conn.close()

    await bot.answer_callback_query(callback_query.id)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS



@dp.callback_query_handler(lambda c: c.data == 'cn0c')
async def cn0c_start(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Показываем выбор: человек или канал
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 Человек", callback_data="cn0c_person"),
        InlineKeyboardButton("📣 Канал", callback_data="cn0c_channel")
    )
    await bot.send_message(
        user_id,
        "<b>💥 заказ: выберите, кому вы хотите заказать пиццу:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'referral')
async def handle_referral(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT valid_referrals, referral_cycles 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()

    valid = row[0] if row else 0
    cycles = row[1] if row else 0

    await bot.send_message(
        user_id,
        f"<b>👥 Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"👤 Приглашено: <b>{valid}/20</b>\n"
        f"🔁 Бонусов получено: <b>{cycles}</b>\n\n"
        f"📌 За каждые 20 друзей — +1 день подписки!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔰 Назад", callback_data="back_to_menu")
        )
    )
    await bot.answer_callback_query(callback_query.id)

def get_reason_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚫 пицца со Спамом", callback_data="reason_spam"),
        InlineKeyboardButton("👊 пицца с Насил.", callback_data="reason_violence"),
        InlineKeyboardButton("🔞 пицца с 18+", callback_data="reason_pornography"),
        InlineKeyboardButton("🔒 пицца с Личныеми данными", callback_data="reason_private_data"),
        InlineKeyboardButton("💣 пицца с Террор.", callback_data="reason_terrorism"),
        InlineKeyboardButton("👶 пицца с ЦП", callback_data="reason_child_abuse")
    )
    return keyboard

@dp.message_handler(state=ReportStates.waiting_for_link, content_types=types.ContentTypes.TEXT)
async def handle_link(message: types.Message, state: FSMContext):
    chatlink = message.text.strip()
    if not chatlink.startswith("https://t.me/"):
        await message.answer("♦️ Неверный формат адреса.")
        return

    parts = chatlink.split("/")
    if len(parts) < 5:
        await message.answer("♦️ Неверный формат адреса.")
        return

    chat_id = parts[3]
    try:
        msg_id = int(parts[4])
    except ValueError:
        await message.answer("♦️ Неверный формат ID сообщения.")
        return
    
    # Сохраняем данные сообщения в состоянии
    await state.update_data(chat_id=chat_id, msg_id=msg_id, link=chatlink)
    
    # Предлагаем выбрать причину жалобы
    await message.answer("⚡ Выберите причину заказа:", reply_markup=get_reason_keyboard())
    await ReportStates.waiting_for_reason.set()

@dp.callback_query_handler(lambda c: c.data.startswith('reason_'), state=ReportStates.waiting_for_reason)
async def handle_reason_selection(callback_query: types.CallbackQuery, state: FSMContext):
    async with send_reports_lock:
        if not is_reporting_enabled():
            await callback_query.message.answer("❌ Отправка заказов сейчас отключена администратором.")
            await state.finish()
            await bot.answer_callback_query(callback_query.id)
            return

        reason_type = callback_query.data[len("reason_"):]
        user_data = await state.get_data()
        chat_id = user_data['chat_id']
        msg_id = user_data['msg_id']
        chatlink = user_data['link']

        # Определяем тип и текст жалобы в зависимости от выбранной причины
        reason_mapping = {
            'spam': {
                'class': InputReportReasonSpam(),
                'text': "This account is sending spam messages. Please take action against this spammer."
            },
            'violence': {
                'class': InputReportReasonViolence(),
                'text': "This content promotes violence and dangerous behavior. It should be removed immediately."
            },
            'pornography': {
                'class': InputReportReasonPornography(),
                'text': "This message contains explicit pornographic content which is inappropriate and against community rules."
            },
            'private_data': {
                'class': InputReportReasonOther(),
                'text': "This message contains private personal information that's being shared without consent. This is doxxing."
            },
            'terrorism': {
                'class': InputReportReasonOther(),
                'text': "This content promotes terrorism or extremist activities. It should be removed as it threatens public safety."
            },
            'child_abuse': {
                'class': InputReportReasonChildAbuse(),
                'text': "This content appears to contain child sexual abuse material. Please remove it and investigate this account."
            }
        }

        reason_data = reason_mapping.get(reason_type)
        if not reason_data:
            await callback_query.message.answer("❌ Неизвестная причина заказа.")
            await state.finish()
            await bot.answer_callback_query(callback_query.id)
            return

        reason_class = reason_data['class']
        report_text = reason_data['text']
        reason_display_name = reason_type.replace('_', ' ').title()

        api_id = config.get("API_ID")
        api_hash = config.get("API_HASH")
        if not api_id or not api_hash:
            await callback_query.message.answer("🔸 Конфигурация не настроена. Проверьте config.json.")
            await state.finish()
            await bot.answer_callback_query(callback_query.id)
            return

        # Получаем список всех сессий
        session_files = [f for f in os.listdir('sessions') if f.endswith('.session')]
        
        # Добавляем стандартную сессию в начало списка
        if 'temp_checker.session' in session_files:
            session_files.remove('temp_checker.session')
        session_files.insert(0, 'temp_checker.session')
        
        sender_id = None
        session_used = None
        
        # Перебираем сессии, пока не найдем работающую
        for session_file in session_files:
            session_name = session_file[:-8]  # Убираем расширение .session
            
            try:
                # Пробуем получить сообщение через текущую сессию
                async with TelegramClient(f'sessions/{session_name}', api_id, api_hash, connection_retries=0) as client:
                    try:
                        message_data = await client.get_messages(chat_id, ids=msg_id)
                        if message_data and message_data.sender_id:
                            sender_id = message_data.sender_id
                            session_used = session_file
                            log_to_file(f"✅ Отправитель найден через сессию {session_file}: {sender_id}")
                            break
                    except Exception as e:
                        log_to_file(f"❌ Ошибка при получении сообщения через сессию {session_file}: {e}")
                        continue
            except Exception as e:
                log_to_file(f"❌ Ошибка при использовании сессии {session_file}: {e}")
                continue
        
        if not sender_id:
            await callback_query.message.answer("♦️ Не удалось найти отправителя через доступных курьеров.")
            await state.finish()
            await bot.answer_callback_query(callback_query.id)
            return

        if is_in_whitelist(sender_id):
            await callback_query.message.answer("♦️ Этот пользователь в whitelist.")
            await state.finish()
            await bot.answer_callback_query(callback_query.id)
            return

        complainant_id = callback_query.from_user.id

        done = 0
        err = 0
        invalid_sessions = []

        session_files = [f for f in os.listdir('sessions') if f.endswith('.session')]

        async def report_from_session(session_file):
            nonlocal done, err, invalid_sessions
            session_path = f'sessions/{session_file}'

            if not os.path.exists(session_path):
                log_to_file(f"❌ {session_file}: файл отсутствует.")
                return

            try:
                session = SQLiteSession(session_path)
                async with TelegramClient(session, api_id, api_hash, connection_retries=0) as client:
                    try:
                        if not await client.is_user_authorized():
                            log_to_file(f"❌ {session_file}: не авторизована.")
                            invalid_sessions.append(session_file)
                            return
                    except PhoneNumberInvalidError:
                        log_to_file(f"❌ {session_file}: битая сессия, номер недействителен.")
                        invalid_sessions.append(session_file)
                        return
                    except SessionPasswordNeededError:
                        log_to_file(f"❌ {session_file}: сессия требует 2FA пароль — пропускаем.")
                        invalid_sessions.append(session_file)
                        return
                    except Exception as e:
                        log_to_file(f"❌ {session_file}: ошибка проверки авторизации: {e}")
                        invalid_sessions.append(session_file)
                        return

                    try:
                        peer = await client.get_input_entity(chat_id)
                        await client(functions.messages.ReportRequest(
                            peer=peer,
                            id=[msg_id],
                            reason=reason_class,
                            message=report_text
                        ))
                        done += 1
                    except Exception as e:
                        log_to_file(f"❌ {session_file}: ошибка при отправке репорта: {e}")
                        err += 1

            except Exception as e:
                log_to_file(f"❌ {session_file}: глобальная ошибка: {e}")
                err += 1

        await asyncio.gather(*(report_from_session(f) for f in session_files))

        # Отображаем название причины на русском языке
        reason_ru_names = {
            'spam': 'пицца со спамом',
            'violence': 'пицца с насил.',
            'pornography': 'пица с проно',
            'private_data': 'пицца с данными',
            'terrorism': 'пицца с терро',
            'child_abuse': 'пицца с дп'
        }
        reason_display = reason_ru_names.get(reason_type, reason_type.upper())

        log_entry = (
            f"[ ⚠️ Жалоба ]\n"
            f"👤 От пользователя: <code>{complainant_id}</code>\n"
            f"🔗 Ссылка: {chatlink}\n"
            f"🎯 Цель (sender_id): <code>{sender_id}</code>\n"
            f"🗣 Причина: {reason_display}\n"
            f"📝 Текст: {report_text}\n"
            f"📊 Итоги: Успешно: {done} | Ошибки: {err}\n"
        )

        log_to_file(log_entry)
        await bot.send_message(LOG_CHANNEL_ID, log_entry, parse_mode="HTML")

        await callback_query.message.answer(
            f"[ ✔️ ] пицца отправлена\n\n"
            f"🗣 начинка: {reason_display}\n"
            f"🔱 Успешно: {done}\n"
            f"✖️ Ошибки: {err}"
        )

        try:
            photo = InputFile(image_path)
            await callback_query.message.answer_photo(
                photo,
                caption="🚀 <b>| Вы вернулись в главное меню FOBIO PIZZA</b>",
                reply_markup=get_main_menu_keyboard(user_id=callback_query.from_user.id),
                parse_mode="HTML"
            )
        except Exception:
            await callback_query.message.answer(
                "⚡ пиццы успешно отправлены! Выберите следующее действие:",
                reply_markup=get_main_menu_keyboard(user_id=callback_query.from_user.id)
            )

        await state.finish()
        await bot.answer_callback_query(callback_query.id)

@dp.message_handler(commands=["s"])
async def cmd_user_info(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Формат: /s [user_id]")
            return
        user_id = int(parts[1])
    except Exception:
        await message.reply("Формат: /s [user_id]")
        return

    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT join_date, balance, subscription_end FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            await message.reply("❌ Пользователь не найден")
            return
        join_date, balance, subscription_end = row
        balance_str = f"{balance:.2f}$" if balance is not None else "0.00$"
        if subscription_end:
            try:
                sub_end_dt = datetime.fromisoformat(subscription_end)
                if datetime.now() < sub_end_dt:
                    sub_status = f"🪬 Активна до {sub_end_dt.strftime('%d.%m.%Y %H:%M')}"
                else:
                    sub_status = "✖️ Неактивна (истекла)"
            except Exception:
                sub_status = f"✖️ Неактивна (ошибка даты: {subscription_end})"
        else:
            sub_status = "✖️ Неактивна"
        # Проверка вайтлиста
        cursor.execute('SELECT 1 FROM whitelist WHERE user_id = ?', (user_id,))
        in_whitelist = "🪬 Да" if cursor.fetchone() else "✖️ Нет"
        # Дата регистрации
        if join_date:
            try:
                join_date_str = datetime.fromisoformat(join_date).strftime("%d.%m.%Y %H:%M")
            except Exception:
                join_date_str = join_date
        else:
            join_date_str = "-"
        text = (
            f"👤 <b>Информация о пользователе {user_id}</b>\n"
            f"📅 Дата регистрации: <code>{join_date_str}</code>\n"
            f"🛡️ Вайтлист: <code>{in_whitelist}</code>\n"
            f"💎 Доставка: <code>{sub_status}</code>\n"
            f"💸 Шоколадки: <code>{balance_str}</code>"
        )
        await message.reply(text, parse_mode="HTML")
    finally:
        conn.close()


# ───────────────────────────────────────────────────────────────────
# 1) Если пользователь выбрал «Человек»
# ───────────────────────────────────────────────────────────────────
@dp.callback_query_handler(lambda c: c.data == 'cn0c_person')
async def cn0c_person_start(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    # Проверка подписки (дополнительно)
    if not check_subscription(user_id):
        await bot.answer_callback_query(
            callback_query.id,
            "❌ Требуется активная подписка!",
            show_alert=True
        )
        await bot.send_message(
            user_id,
            "🔒 Для доступа к этому функционалу приобретите подписку:",
            reply_markup=get_profile_keyboard()
        )
        return

    # Сохраняем в state, что жалоба будет «на человека»
    await state.update_data(report_type='person')

    # Просим ссылку на сообщение пользователя
    await bot.send_message(
        user_id,
        "<b>☂️ Пожалуйста, введите адрес пользователя:</b>\n",
        parse_mode="HTML"
    )
    # Устанавливаем состояние ожидания ссылки
    await ReportStates.waiting_for_link.set()

    # Убираем «крутилку» в интерфейсе
    await bot.answer_callback_query(callback_query.id)


# ───────────────────────────────────────────────────────────────────
# 2) Если пользователь выбрал «Канал»
# ───────────────────────────────────────────────────────────────────
@dp.callback_query_handler(lambda c: c.data == 'cn0c_channel')
async def cn0c_channel_start(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    if not check_channel_subscription_db(user_id):
        await bot.answer_callback_query(
            callback_query.id,
            "❌ У вас нет доступа к заказу каналов.",
            show_alert=True
        )
        await bot.send_message(
            user_id,
            "🔒 Чтобы жаловаться на каналы, купите подписку:",
            reply_markup=get_subscription_plans_keyboard()  # 🔄 заменим несуществующую
        )
        return

    await state.update_data(report_type='channel')
    await bot.send_message(
        user_id,
        "<b>☂️ Пожалуйста, введите адрес на канал:</b>\n",
        parse_mode="HTML"
    )
    await ReportStates.waiting_for_link.set()
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'promo_activate')
async def activate_promo_start(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.from_user.id,
        "🎁 Введите промокод для активации:"
    )
    await PromoStates.waiting_for_code.set()
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=PromoStates.waiting_for_code)
async def process_promo_code(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    promo_code = message.text.strip().upper()
    
    # Проверяем промокод
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о промокоде
        cursor.execute('SELECT days, used_by FROM promo_codes WHERE code = ?', (promo_code,))
        promo = cursor.fetchone()
        
        if not promo:
            await message.answer("❌ Промокод не найден.")
            await state.finish()
            conn.close()
            return
        
        days, used_by = promo
        
        # Проверяем, не был ли промокод уже использован
        if used_by:
            await message.answer("❌ Этот промокод уже был использован.")
            await state.finish()
            conn.close()
            return
        
        # Обновляем информацию о промокоде
        cursor.execute('''
            UPDATE promo_codes 
            SET used_by = ?, used_at = ? 
            WHERE code = ?
        ''', (user_id, datetime.now().isoformat(), promo_code))
        
        # Обновляем подписку пользователя
        # Сначала проверяем, есть ли у пользователя действующая подписка
        cursor.execute('SELECT subscription_end FROM users WHERE user_id = ?', (user_id,))
        current_sub = cursor.fetchone()
        
        if current_sub and current_sub[0]:
            current_end = datetime.fromisoformat(current_sub[0])
            # Если подписка активна, продлеваем её
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
        else:
            new_end = datetime.now() + timedelta(days=days)
        
        # Обновляем дату окончания подписки
        cursor.execute('''
            UPDATE users 
            SET subscription_end = ? 
            WHERE user_id = ?
        ''', (new_end.isoformat(), user_id))
        
        conn.commit()
        
        # Отправляем подтверждение
        await message.answer(
            f"✅ Промокод активирован!\n"
            f"📅 Подписка продлена на {days} дней.\n"
            f"📆 Новая дата окончания: {new_end.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Логируем активацию для админов
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"🎁 Пользователь {user_id} активировал промокод {promo_code} на {days} дней!"
            )
        
    except Exception as e:
        logging.error(f"Ошибка активации промокода: {str(e)}")
        await message.answer("❌ Произошла ошибка при активации промокода.")
    finally:
        conn.close()
        await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'admin_menu')
async def show_admin_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>🔧 Админ меню</b>",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_subscriptions')
async def show_subscriptions_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>🔧 Управление подписками</b>",
        reply_markup=get_subscriptions_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_balance')
async def show_balance_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>💰 Управление балансом</b>",
        reply_markup=get_balance_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_wl_bl')
async def show_wl_bl_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>📋 Whitelist/Blacklist</b>",
        reply_markup=get_wl_bl_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast')
async def show_broadcast_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>📬 Рассылка и отладка</b>",
        reply_markup=get_broadcast_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_reports')
async def show_reports_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="<b>🔄 Управление репортами</b>",
        reply_markup=get_reports_menu_keyboard(),
        parse_mode="HTML"
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_sub_grant')
async def admin_sub_grant(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="📅 Введите ID пользователя для выдачи подписки:"
    )
    await AdminStates.waiting_for_sub_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_sub_user_id)
async def process_sub_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer("📅 Введите количество дней для подписки:")
        await AdminStates.waiting_for_sub_days.set()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_sub_days)
async def process_sub_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days <= 0:
            await message.answer("❌ Количество дней должно быть положительным числом.")
            await state.finish()
            return
        
        data = await state.get_data()
        user_id = data['user_id']
        
        subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET subscription_end = ? 
                WHERE user_id = ?
            ''', (subscription_end, user_id))
            conn.commit()
            await message.answer(f"✅ Пользователю {user_id} выдана подписка на {days} дней.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            conn.close()
        
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное целое число дней.")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_sub_revoke')
async def admin_sub_revoke(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="❌ Введите ID пользователя для отмены подписки:"
    )
    await AdminStates.waiting_for_unsub_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_unsub_user_id)
async def process_unsub_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        update_subscription(user_id, None)
        await message.answer(f"✅ Подписка пользователя {user_id} отменена.")
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_sub_list')
async def admin_sub_list(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    filename = None
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, subscription_end 
            FROM users 
            WHERE subscription_end IS NOT NULL
            ORDER BY subscription_end DESC
        ''')
        users = cursor.fetchall()

        with tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.txt', 
            delete=False, 
            encoding='utf-8'
        ) as tmp_file:
            filename = tmp_file.name
            tmp_file.write("📅 Список всех подписок\n")
            tmp_file.write(f"Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            tmp_file.write("="*40 + "\n")
            
            if not users:
                tmp_file.write("❌ Активных подписок не найдено\n")
            else:
                for user in users:
                    status = "✅ Активна" if datetime.now() < datetime.fromisoformat(user[1]) else "❌ Истекла"
                    end_date = datetime.fromisoformat(user[1]).strftime('%d.%m.%Y %H:%M')
                    tmp_file.write(
                        f"👤 User ID: {user[0]}\n"
                        f"Статус: {status}\n"
                        f"Окончание: {end_date}\n"
                        f"{'-'*30}\n"
                    )

        with open(filename, 'rb') as file:
            await bot.send_document(
                chat_id=callback_query.from_user.id,
                document=file,
                caption="📊 Полный список подписок",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            
    except Exception as e:
        logging.error(f"Ошибка формирования отчета: {str(e)}")
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="❌ Ошибка генерации отчета",
            reply_markup=get_subscriptions_menu_keyboard()
        )
    finally:
        conn.close()
        if filename and os.path.exists(filename):
            os.unlink(filename)
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_promo_create')
async def admin_promo_create(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="🎁 Введите количество дней для промокода:"
    )
    await AdminStates.waiting_for_promo_days.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_promo_days)
async def process_promo_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days <= 0:
            await message.answer("❌ Количество дней должно быть положительным числом.")
            await state.finish()
            return
        
        code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO promo_codes 
            (code, days, created_by, created_at) 
            VALUES (?, ?, ?, ?)
        ''', (code, days, message.from_user.id, created_at))
        
        conn.commit()
        conn.close()
        
        await message.answer(
            f"✅ Промокод создан!\n\n"
            f"📋 Код: <code>{code}</code>\n"
            f"📅 Дней: {days}\n\n"
            f"Пользователи могут активировать его через меню.",
            parse_mode="HTML",
            reply_markup=get_subscriptions_menu_keyboard()
        )
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное целое число дней.")
    except Exception as e:
        logging.error(f"Ошибка создания промокода: {str(e)}")
        await message.answer("❌ Произошла ошибка при создании промокода.")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_promo_list')
async def admin_promo_list(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT code, days, created_at, used_by, used_at 
            FROM promo_codes 
            ORDER BY created_at DESC
        ''')
        promos = cursor.fetchall()
        
        if not promos:
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="📋 Промокоды не найдены.",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            return
        
        with tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.txt', 
            delete=False, 
            encoding='utf-8'
        ) as tmp_file:
            filename = tmp_file.name
            tmp_file.write("📋 Список всех промокодов\n")
            tmp_file.write(f"Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            tmp_file.write("="*40 + "\n\n")
            
            for promo in promos:
                code, days, created_at, used_by, used_at = promo
                status = "✅ Использован" if used_by else "⏳ Активен"
                created_date = datetime.fromisoformat(created_at).strftime('%d.%m.%Y %H:%M')
                
                tmp_file.write(f"Код: {code}\n")
                tmp_file.write(f"Дней: {days}\n")
                tmp_file.write(f"Создан: {created_date}\n")
                tmp_file.write(f"Статус: {status}\n")
                
                if used_by:
                    used_date = datetime.fromisoformat(used_at).strftime('%d.%m.%Y %H:%M')
                    tmp_file.write(f"Использован пользователем: {used_by}\n")
                    tmp_file.write(f"Дата активации: {used_date}\n")
                
                tmp_file.write("-"*30 + "\n\n")
        
        with open(filename, 'rb') as file:
            await bot.send_document(
                chat_id=callback_query.from_user.id,
                document=file,
                caption="📊 Полный список промокодов",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            
    except Exception as e:
        logging.error(f"Ошибка при просмотре промокодов: {str(e)}")
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="❌ Произошла ошибка при получении списка промокодов.",
            reply_markup=get_subscriptions_menu_keyboard()
        )
    finally:
        conn.close()
        if filename and os.path.exists(filename):
            os.unlink(filename)
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_balance_add')
async def admin_balance_add(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="➕ Введите ID пользователя для увеличения баланса:"
    )
    await AdminStates.waiting_for_balance_user_id.set()
    await state.update_data(action='add')
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_balance_sub')
async def admin_balance_sub(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="➖ Введите ID пользователя для уменьшения баланса:"
    )
    await AdminStates.waiting_for_balance_user_id.set()
    await state.update_data(action='sub')
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_balance_user_id)
async def process_balance_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer("💰 Введите сумму для изменения баланса:")
        await AdminStates.waiting_for_balance_amount.set()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_balance_amount)
async def process_balance_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 0:
            await message.answer("❌ Сумма должна быть положительной.")
            await state.finish()
            return
        
        data = await state.get_data()
        user_id = data['user_id']
        action = data['action']
        
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            if action == 'add':
                cursor.execute('''
                    UPDATE users 
                    SET balance = round(balance + ?, 2)
                    WHERE user_id = ?
                ''', (amount, user_id))
                await message.answer(f"✅ Баланс пользователя {user_id} увеличен на {amount}$.")
            else:
                cursor.execute('''
                    UPDATE users 
                    SET balance = round(balance - ?, 2)
                    WHERE user_id = ?
                ''', (amount, user_id))
                await message.answer(f"✅ Баланс пользователя {user_id} уменьшен на {amount}$.")
            conn.commit()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            conn.close()
        
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_balance_list')
async def admin_balance_list(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    filename = None
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, balance 
            FROM users 
            WHERE balance > 0
            ORDER BY balance DESC
        ''')
        users = cursor.fetchall()

        with tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.txt', 
            delete=False, 
            encoding='utf-8'  
        ) as tmp_file:
            filename = tmp_file.name
            tmp_file.write("💰 Список всех балансов\n")
            tmp_file.write(f"Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            tmp_file.write("="*40 + "\n")
            
            if not users:
                tmp_file.write("❌ Нет пользователей с балансом\n")
            else:
                for user in users:
                    tmp_file.write(
                        f"👤 User ID: {user[0]}\n"
                        f"Баланс: {user[1]:.2f}$\n"
                        f"{'-'*30}\n"
                    )

        with open(filename, 'rb') as file:
            await bot.send_document(
                chat_id=callback_query.from_user.id,
                document=file,
                caption="📊 Полный список балансов",
                reply_markup=get_balance_menu_keyboard()
            )
            
    except Exception as e:
        logging.error(f"Ошибка формирования отчета: {str(e)}")
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="❌ Ошибка генерации отчета",
            reply_markup=get_balance_menu_keyboard()
        )
    finally:
        conn.close()
        if filename and os.path.exists(filename):
            os.unlink(filename)
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_wl_add')
async def admin_wl_add(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="➕ Введите ID пользователя для добавления в whitelist:"
    )
    await AdminStates.waiting_for_wl_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_wl_user_id)
async def process_wl_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO whitelist 
                (user_id, added_by, added_at)
                VALUES (?, ?, ?)
            ''', (user_id, message.from_user.id, datetime.now().isoformat()))
            conn.commit()
            await message.answer(f"✅ Пользователь {user_id} добавлен в белый список.", reply_markup=get_wl_bl_menu_keyboard())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            conn.close()
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_wl_remove')
async def admin_wl_remove(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="➖ Введите ID пользователя для удаления из whitelist:"
    )
    await AdminStates.waiting_for_remove_wl_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_remove_wl_user_id)
async def process_remove_wl_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM whitelist WHERE user_id = ?', (user_id,))
            conn.commit()
            await message.answer(f"✅ Пользователь {user_id} удален из белого списка.", reply_markup=get_wl_bl_menu_keyboard())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            conn.close()
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_bl_add')
async def admin_bl_add(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="⛔ Введите ID пользователя для добавления в blacklist:"
    )
    await AdminStates.waiting_for_bl_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_bl_user_id)
async def process_bl_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        if user_id in ADMIN_IDS:
            await message.answer("⚠️ Невозможно добавить администратора в черный список.")
            await state.finish()
            return
        await state.update_data(user_id=user_id)
        await message.answer("⛔ Введите причину для добавления в blacklist (или '-' для пропуска):")
        await AdminStates.waiting_for_bl_reason.set()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_bl_reason)
async def process_bl_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip() if message.text.strip() != '-' else "Не указана"
    data = await state.get_data()
    user_id = data['user_id']
    
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO blacklist 
            (user_id, added_by, reason, added_at) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, message.from_user.id, reason, datetime.now().isoformat()))
        conn.commit()
        
        await message.answer(
            f"✅ Пользователь {user_id} добавлен в черный список.\nПричина: {reason}",
            reply_markup=get_wl_bl_menu_keyboard()
        )
        
        try:
            admin_contact = config.get('admin_contact', 'teppupvp')
            await bot.send_message(
                user_id,
                f"⛔ Вы были внесены в черный список проекта. Вопросы? @{admin_contact}"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {str(e)}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    finally:
        conn.close()
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_bl_remove')
async def admin_bl_remove(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="✅ Введите ID пользователя для удаления из blacklist:"
    )
    await AdminStates.waiting_for_unbl_user_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_unbl_user_id)
async def process_unbl_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM blacklist WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                await message.answer(f"⚠️ Пользователь {user_id} не найден в черном списке.")
                conn.close()
                await state.finish()
                return
            
            cursor.execute('DELETE FROM blacklist WHERE user_id = ?', (user_id,))
            conn.commit()
            
            await message.answer(f"✅ Пользователь {user_id} удален из черного списка.", reply_markup=get_wl_bl_menu_keyboard())
            
            try:
                await bot.send_message(
                    user_id,
                    "✅ Вы были удалены из черного списка проекта."
                )
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {str(e)}")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        finally:
            conn.close()
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_bl_list')
async def admin_bl_list(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT blacklist.user_id, reason, added_at, username 
            FROM blacklist 
            LEFT JOIN users ON blacklist.user_id = users.user_id 
            ORDER BY added_at DESC
        ''')
        blacklisted = cursor.fetchall()
        
        if not blacklisted:
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="📋 Черный список пуст.",
                reply_markup=get_wl_bl_menu_keyboard()
            )
            return
        
        with tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.txt', 
            delete=False, 
            encoding='utf-8'
        ) as tmp_file:
            filename = tmp_file.name
            tmp_file.write("⛔ Черный список пользователей\n")
            tmp_file.write(f"Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            tmp_file.write("="*40 + "\n\n")
            
            for user in blacklisted:
                user_id, reason, added_at, username = user
                added_date = datetime.fromisoformat(added_at).strftime('%d.%m.%Y %H:%M')
                
                tmp_file.write(f"ID: {user_id}\n")
                if username:
                    tmp_file.write(f"Юзернейм: @{username}\n")
                tmp_file.write(f"Причина: {reason}\n")
                tmp_file.write(f"Добавлен: {added_date}\n")
                tmp_file.write("-"*30 + "\n\n")
        
        with open(filename, 'rb') as file:
            await bot.send_document(
                chat_id=callback_query.from_user.id,
                document=file,
                caption="📊 Черный список пользователей",
                reply_markup=get_wl_bl_menu_keyboard()
            )
            
    except Exception as e:
        logging.error(f"Ошибка при просмотре черного списка: {str(e)}")
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="❌ Произошла ошибка при получении черного списка.",
            reply_markup=get_wl_bl_menu_keyboard()
        )
    finally:
        conn.close()
        if filename and os.path.exists(filename):
            os.unlink(filename)
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast_send')
async def admin_broadcast_send(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="📢 Введите сообщение для массовой рассылки:"
    )
    await AdminStates.waiting_for_broadcast_message.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Сообщение не может быть пустым.")
        await state.finish()
        return
    
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        user_ids = cursor.fetchall()
        sent_count = 0
        for user_id_tuple in user_ids:
            user_id = user_id_tuple[0]
            try:
                await bot.send_message(user_id, text)
                sent_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {str(e)}")

        await message.answer(
            f"📤 Рассылка завершена. Отправлено {sent_count} сообщений.",
            reply_markup=get_broadcast_menu_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка при рассылке: {str(e)}")
        await message.answer("❌ Произошла ошибка при рассылке.")
    finally:
        conn.close()
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin_test_log')
async def admin_test_log(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text="✅ Тестовое сообщение в лог-группу!"
        )
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Лог отправлен!",
            reply_markup=get_broadcast_menu_keyboard()
        )
    except Exception as e:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=get_broadcast_menu_keyboard()
        )
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_debug_group')
async def admin_debug_group(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    try:
        group_id = int(config["LOG_CHANNEL_ID"])
        chat = await bot.get_chat(group_id)
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"""
🧰 Информация о группе:
ID: {chat.id}
Тип: {chat.type}
Название: {chat.title}
Права бота: {chat.permissions.can_send_messages}
            """,
            reply_markup=get_broadcast_menu_keyboard()
        )
    except Exception as e:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=get_broadcast_menu_keyboard()
        )
    
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_reports_stop')
async def admin_reports_stop(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    set_reporting_enabled(False)
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="❌ Отправка пиццы отключена.",
        reply_markup=get_reports_menu_keyboard()
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_reports_go')
async def admin_reports_go(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    set_reporting_enabled(True)
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="✅ Отправка пиццы включена.",
        reply_markup=get_reports_menu_keyboard()
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'admin_user_info')
async def admin_user_info(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, "⛔ У вас нет прав.", show_alert=True)
        return
    
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="📄 Введите ID пользователя для просмотра информации:"
    )
    await AdminStates.waiting_for_user_info_id.set()
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminStates.waiting_for_user_info_id)
async def process_user_info_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT join_date, balance, subscription_end FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                await message.answer("❌ Пользователь не найден")
                await state.finish()
                return
            
            join_date, balance, subscription_end = row
            balance_str = f"{balance:.2f}$" if balance is not None else "0.00$"
            if subscription_end:
                try:
                    sub_end_dt = datetime.fromisoformat(subscription_end)
                    if datetime.now() < sub_end_dt:
                        sub_status = f"🪬 Активна до {sub_end_dt.strftime('%d.%m.%Y %H:%M')}"
                    else:
                        sub_status = "✖️ Неактивна (истекла)"
                except Exception:
                    sub_status = f"✖️ Неактивна (ошибка даты: {subscription_end})"
            else:
                sub_status = "✖️ Неактивна"
            
            cursor.execute('SELECT 1 FROM whitelist WHERE user_id = ?', (user_id,))
            in_whitelist = "🪬 Да" if cursor.fetchone() else "✖️ Нет"
            
            if join_date:
                try:
                    join_date_str = datetime.fromisoformat(join_date).strftime("%d.%m.%Y %H:%M")
                except Exception:
                    join_date_str = join_date
            else:
                join_date_str = "-"
            
            text = (
                f"👤 <b>Информация о пользователе {user_id}</b>\n"
                f"📅 Дата регистрации: <code>{join_date_str}</code>\n"
                f"🛡️ Вайтлист: <code>{in_whitelist}</code>\n"
                f"💎 Подписка: <code>{sub_status}</code>\n"
                f"💸 шоколадки: <code>{balance_str}</code>"
            )
            await message.answer(text, parse_mode="HTML", reply_markup=get_admin_menu_keyboard())
        finally:
            conn.close()
        await state.finish()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID пользователя (целое число).")
        await state.finish()
          

# Добавляем проверку черного списка для всех callback_query
@dp.callback_query_handler(lambda c: True, state="*")
async def process_callback_blacklist_check(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверка на черный список
    if is_in_blacklist(user_id):
        admin_contact = config.get('admin_contact', 'killerskype')
        await bot.answer_callback_query(
            callback_query.id,
            f"⛔ Вы в черном списке проекта. Вопросы? @{admin_contact}",
            show_alert=True
        )
        return
    
    # Очищаем текущее состояние FSM, чтобы основной хендлер мог принять запрос
    await dp.current_state().reset_state(with_data=False)
    return  # Больше не нужно бросать CancelHandler


if __name__ == '__main__':
    init_db()
    check_whitelist_table() 
    migrate_db() 
    safe_init_db()
    executor.start_polling(dp, skip_updates=True)
    
#by @killerskype
