from datetime import datetime
import os
import platform
import sys
import logging
import asyncio
import tempfile
from threading import Thread
import zipfile
from datetime import datetime
import numpy as np
import rarfile
import zipfile
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from db import *
from datetime import time
import time
import signal
from datetime import datetime
import threading
import mimetypes
import time
import psutil
import codecs
import matplotlib.pyplot as plt
import traceback,shutil
from aiogram.types import BufferedInputFile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import pandas as pd
from aiogram.types import Message
from collections import defaultdict
from aiogram.types import FSInputFile 
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import subprocess
import os
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.types import InputFile 
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ContentType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
www = Path(f"users")
admin=[963729102,1624096187]
CHANNEL_ID = -1002707833409
www.mkdir(parents=True, exist_ok=True)
bot = Bot(token=API_TOKEN, request_timeout=300)
dp = Dispatcher()
y_n={}
count={}
libra={}
id_pip=1
user=1
channel_id=[]
user_variables = {}
active_processes = {}  # Храним активные процессы по user_id
log_queues = {}  
filr_ch=""

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Запустить'),
         KeyboardButton(text='Логи'),
        KeyboardButton(text='Профиль')],
        [KeyboardButton(text='Файлы'), 
         KeyboardButton(text='Библиотеки'), 
         KeyboardButton(text='Основной файл')]
    ],
    resize_keyboard=True
)

library_yes_no=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Скачать'),
         KeyboardButton(text='Удалить')],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)

yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Да'),
         KeyboardButton(text='Нет')],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Users'),
         KeyboardButton(text='Инфа'),
        KeyboardButton(text='Финансы'),
        KeyboardButton(text='БД')], 
        [KeyboardButton(text='Количество процессов'),
         KeyboardButton(text='file'),
         KeyboardButton(text='CPU'),
         KeyboardButton(text='Сообщения'),],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)

sms_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Рассылка'),
        KeyboardButton(text='Сообщение пользователю')], 
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)


chanel_keybord=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Подписаться на канал", 
                url="https://t.me/sever_host")],
            [InlineKeyboardButton(
            text="✅ Я подписался!", 
            callback_data="check_subscription")]])

notmain_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Стоп'),
         KeyboardButton(text='Логи'),
        KeyboardButton(text='Профиль')],
        [KeyboardButton(text='Файлы'), 
         KeyboardButton(text='Библиотеки'), 
         KeyboardButton(text='Основной файл')]
    ],
    resize_keyboard=True
)
otmena_keyboard= ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]],
    resize_keyboard=True
)
download=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Все'),
        KeyboardButton(text='По 1 файлу')], 
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)
download_id=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Все file'),
        KeyboardButton(text='По 1 file')], 
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)

file_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Без архива'),
        KeyboardButton(text='Все вместе,архивом')], 
        [KeyboardButton(text='Показать файлы'), 
        KeyboardButton(text='Удалить файлы'),
        KeyboardButton(text='Скачать')], 
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)
delete=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Удалить все'),
        KeyboardButton(text='Удалить 1 файл')],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)


class BroadcastState(StatesGroup):
    glav_file = State()
    shea_file = State()
    one_file = State()
    library=State()
    yes_no=State()
    delete_state=State()
    dow=State()
    sms=State()
    sms2=State()
    waiting_for_message=State()
    waiting_for_confirmation=State()
    Message_from_human=State()
    Message_from_human2=State()
    infostate=State()
    library_yes=State()
    file_chek=State()
    one_file_admin=State()
    


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if await check_subscription(user_id):
        await callback.message.delete()
        await bot.send_message(user_id, ("Добро пожаловать 👋\n"
        "Отправьте /start для начала использования") )
    else:
        await callback.answer("❌ Вы всё ещё не подписаны!", show_alert=True)

@dp.message(F.text == 'Отмена', StateFilter('*'))
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    if chek_start(i=user_id):
        await message.answer("Отмена",reply_markup=notmain_keyboard)
    else:
        await message.answer("Отмена",reply_markup=main_keyboard)
    await state.clear()


@dp.message(F.text == '/start')
async def process_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(user_id)=="1624096187":
        pass
    else:
        return
    
    h="<b>🌌 Добро пожаловать в Sever ❄️</b>\nCервис для хостинга <b>Telegram ботов</b>, приложений и многого другого!\n\n▫️ Мгновенный деплой на <b>Python 3.12.3 </b>\n▫️ Интуитивный интерфейс управления \n▫️ Авто-масштабирование ресурсов \n▫️ 99.9% аптайм гарантия\n\n💬 <u>Нужна помощь? Поддержка 24/7 в шапке бота </u>🔝"
    try:
        if not(chek_start(i=user_id)):
            await message.answer_photo(
                    photo="AgACAgIAAxkDAAImBmf6iT_tvKFzSxhw4l_qFvUlIopLAAIP6jEbWQPRS8g8YSW0Mqp6AQADAgADdwADNgQ",
                    caption=h,
                    reply_markup=main_keyboard,
                    parse_mode='HTML'
                )
        else:
            await message.answer_photo(
                    photo="AgACAgIAAxkDAAImBmf6iT_tvKFzSxhw4l_qFvUlIopLAAIP6jEbWQPRS8g8YSW0Mqp6AQADAgADdwADNgQ",
                    caption=h,
                    reply_markup=notmain_keyboard,
                    parse_mode='HTML')
    except:
        if not(chek_start(i=user_id)):
            await message.answer_photo(
                    photo=FSInputFile("photo/start.jpg"),
                    caption=h,
                    reply_markup=main_keyboard,
                    parse_mode='HTML'
                )
        else:
            await message.answer_photo(
                    photo=FSInputFile("photo/start.jpg"),
                    caption=h,
                    reply_markup=notmain_keyboard,
                    parse_mode='HTML')
    try:
        user_id = message.from_user.id
        user_dir = Path(f"users/{user_id}")
        venv_path = user_dir / ".venv"
        
        # Создаем структуру каталогов
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Проверка и создание venv
        if not venv_path.exists():
            # Для Ubuntu используем явное указание python3
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "venv", str(venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = f"Ошибка 404 \n{stderr.decode()}\n\nПоддержка 24/7 в шапке бота 🔝"
                logger.error(error_msg)
                return await message.answer(error_msg[:3000])
            
            logger.info(f"Created venv for user {user_id}")

        # Устанавливаем права для безопасности
        await message.answer(
            "Выберите действие:")
        await new(message.from_user.id,message.from_user.username)


    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        await message.answer("⚠️ Ошибка доступа!\n\nПоддержка 24/7 в шапке бота 🔝")
        
    except Exception as e:
        logger.error(f"Start error: {traceback.format_exc()}")
        await message.answer("🔧 Временные неполадки. Попробуйте позже.")
    await state.clear()
    

async def new(id,us):
    global admin
    if new_piople(id,us):
        await bot.send_message(chat_id=admin,text=f"Зарегистрирован @{us}\nID: {id}")

async def send_message_to_user(user_id, message):
    user_id = str(user_id)
    try:
        # Для текстовых сообщений
        if message.text:
            await bot.send_message(
                chat_id=user_id,
                text=message.text,
                entities=message.entities,
                reply_markup=message.reply_markup
            )
        
        # Фото
        elif message.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Видео
        elif message.video:
            await bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Видео-заметка (кружок)
        elif message.video_note:
            await bot.send_video_note(
                chat_id=user_id,
                video_note=message.video_note.file_id,
                reply_markup=message.reply_markup
            )
        
        # Голосовые
        elif message.voice:
            await bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Документы
        elif message.document:
            await bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Аудио
        elif message.audio:
            await bot.send_audio(
                chat_id=user_id,
                audio=message.audio.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Стикеры
        elif message.sticker:
            await bot.send_sticker(
                chat_id=user_id,
                sticker=message.sticker.file_id,
                reply_markup=message.reply_markup
            )
        
        # Анимации
        elif message.animation:
            await bot.send_animation(
                chat_id=user_id,
                animation=message.animation.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Локация
        elif message.location:
            await bot.send_location(
                chat_id=user_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
                reply_markup=message.reply_markup
            )
        
        # Вену (место)
        elif message.venue:
            await bot.send_venue(
                chat_id=user_id,
                latitude=message.venue.location.latitude,
                longitude=message.venue.location.longitude,
                title=message.venue.title,
                address=message.venue.address,
                foursquare_id=message.venue.foursquare_id,
                reply_markup=message.reply_markup
            )
        
        # Контакты
        elif message.contact:
            await bot.send_contact(
                chat_id=user_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                reply_markup=message.reply_markup
            )
        
        # Опросы
        elif message.poll:
            await bot.send_poll(
                chat_id=user_id,
                question=message.poll.question,
                options=[opt.text for opt in message.poll.options],
                is_anonymous=message.poll.is_anonymous,
                type=message.poll.type,
                reply_markup=message.reply_markup
            )
        
        # Dice (игральные кости)
        elif message.dice:
            await bot.send_dice(
                chat_id=user_id,
                emoji=message.dice.emoji,
                reply_markup=message.reply_markup
            )
        
        # Неподдерживаемые типы
        else:
            await bot.send_message(
                chat_id=user_id,
                text='Данный тип сообщений не поддерживается'
            )

    except TelegramForbiddenError:
        await message.answer(f"Пользователь {user_id} заблокировал бота.")
    except TelegramBadRequest as e:
        await message.answer(f"Ошибка отправки пользователю {user_id}: {e}")
    except Exception as e:
        await message.answer(f"Неизвестная ошибка при отправке пользователю {user_id}: {e}")

@dp.message(F.text == 'Логи')
async def start(message: types.Message, state: FSMContext):
    try:
        await message.answer_document(types.FSInputFile(f"logs/{message.from_user.id}_logs.txt"))
    except:
        await message.answer(f"Скрипты не были запущены")


@dp.message(F.text == 'Профиль')
async def start(message: types.Message, state: FSMContext):
    print(chek_file(message.from_user.id))
    user_id = message.from_user.id
    df = one_user(user_id)
    fil = chek_file(user_id)
    if str(fil)=="None":
        pass
    else:
        fil=fil[0]

    print(df)
    if chek_start(i=user_id):
        start_program="Приложение запущено ✅"
    else:
        start_program="Приложение выключено ❌"
    now = datetime.now()
    time_serser=now.strftime("%H:%M %d.%m.%Y")
    h=f"Профиль 👤\n\nИмя: @{df[0][1]}\nID: {user_id}\nИмя основного файла: {fil}\nЗапуск программы: {start_program}\n\nХарактеристики сервера:\nOC: Ubuntu 24.04.2 LTS\nВремя: {time_serser}"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkBAAIsrGgCmI7Zbu02iRrKmTa__Ss3bD_6AALM6jEb9o4RSIDagA7Lb2_MAQADAgADeQADNgQ",
            caption=h,
            parse_mode='HTML')
    except:
        await message.answer_photo(
        photo=FSInputFile("photo/profil.jpg"),
        caption=h,
        parse_mode='HTML')


@dp.message(F.text == 'Сообщение пользователю')
async def start(message: types.Message, state: FSMContext):
    global admin
    user_id = message.from_user.id
    if not(user_id in admin):
        return
    await message.answer("Введи ID пользователя")
    await state.set_state(BroadcastState.Message_from_human)

@dp.message(StateFilter(BroadcastState.Message_from_human))
async def start(message: types.Message, state: FSMContext):
    global id_pip
    id_pip=message.text
    await message.answer("Введи текст который хочешь отправить пользователю")
    await state.clear()
    await state.set_state(BroadcastState.Message_from_human2)

@dp.message(StateFilter(BroadcastState.Message_from_human2))
async def start(message: types.Message, state: FSMContext):
    try:
        user_id=id_pip
        if message.text:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_message(
                chat_id=user_id,
                text=message.text,
                entities=message.entities,
                reply_markup=message.reply_markup
            )
        
        # Фото
        elif message.photo:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Видео
        elif message.video:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Видео-заметка (кружок)
        elif message.video_note:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_video_note(
                chat_id=user_id,
                video_note=message.video_note.file_id,
                reply_markup=message.reply_markup
            )
        
        # Голосовые
        elif message.voice:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Документы
        elif message.document:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Аудио
        elif message.audio:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_audio(
                chat_id=user_id,
                audio=message.audio.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Стикеры
        elif message.sticker:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_sticker(
                chat_id=user_id,
                sticker=message.sticker.file_id,
                reply_markup=message.reply_markup
            )
        
        # Анимации
        elif message.animation:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_animation(
                chat_id=user_id,
                animation=message.animation.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=message.reply_markup
            )
        
        # Локация
        elif message.location:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_location(
                chat_id=user_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
                reply_markup=message.reply_markup
            )
        
        # Вену (место)
        elif message.venue:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_venue(
                chat_id=user_id,
                latitude=message.venue.location.latitude,
                longitude=message.venue.location.longitude,
                title=message.venue.title,
                address=message.venue.address,
                foursquare_id=message.venue.foursquare_id,
                reply_markup=message.reply_markup
            )
        
        # Контакты
        elif message.contact:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_contact(
                chat_id=user_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                reply_markup=message.reply_markup
            )
        
        # Опросы
        elif message.poll:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_poll(
                chat_id=user_id,
                question=message.poll.question,
                options=[opt.text for opt in message.poll.options],
                is_anonymous=message.poll.is_anonymous,
                type=message.poll.type,
                reply_markup=message.reply_markup
            )
        
        # Dice (игральные кости)
        elif message.dice:
            await bot.send_message(id_pip,"Сообщение от Администратора:")
            await bot.send_dice(
                chat_id=user_id,
                emoji=message.dice.emoji,
                reply_markup=message.reply_markup
            )
        
        # Неподдерживаемые типы
        else:
            await bot.send_message(
                chat_id=963729102,
                text='Данный тип сообщений не поддерживается'
            )
        await message.answer("Сообщение отправленно")
    except TelegramForbiddenError:
        await message.answer(f"Пользователь {user_id} заблокировал бота.")
    except TelegramBadRequest as e:
        await message.answer(f"Ошибка отправки пользователю {user_id}: {e}")
    except Exception as e:
        await message.answer(f"Неизвестная ошибка при отправке пользователю {user_id}: {e}")
        await state.clear()

def activ_chek():
    count = 0
    users_info = []
    for user_id, processes in active_processes.items():
        if processes:
            user_count = len(processes)
            count += user_count
            users_info.append(user_id)
    return users_info


def get_system_info():
    try:
        # Температура CPU (кросс-платформенный способ)
        try:
            temp = f"{psutil.sensors_temperatures().get('coretemp', [{}])[0].current or 0:.1f}°C"
        except:
            temp = "N/A"

        # Загрузка CPU
        cpu_load = f"{psutil.cpu_percent(interval=1):.1f}%"

        # Использование памяти
        mem = psutil.virtual_memory()
        mem_percent = f"{mem.percent:.1f}%"
        mem_used = f"{mem.used // (1024 * 1024)} MB"

        # Дисковое пространство
        disk = f"{psutil.disk_usage('/').percent}%"

        # Время работы системы
        uptime = str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split('.')[0]

        return {
            "time": datetime.now().strftime("%H:%M"),
            "temp": temp,
            "cpu": cpu_load,
            "memory": f"{mem_used} ({mem_percent})",
            "disk": disk,
            "uptime": uptime,
            "os": f"{platform.system()} {platform.release()}"
        }
    except Exception as e:
        return {"error": f"System info unavailable: {str(e)}"}


async def send_stats(chat_id):
    info = get_system_info()
    message = (
        "📊 *Статистика системы*\n\n"
        f"🕒 *Время:* `{info['time']}`\n"
        f"🌡 *Температура CPU:* `{info['temp']}`\n"
        f"⚡ *Загрузка CPU:* `{info['cpu']}`\n"
        f"💾 *Память:* `{info['memory']}`\n"
        f"💽 *Диск (/):* `{info['disk']}`\n"
        f"⏱ *Аптайм:* `{info['uptime']}`\n"
        f"🖥 *ОС:* `{info['os']}`"
    )
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")


def test_aktivate():
    o=5
    time.sleep(29)
    while True:
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE bots SET program=0")
                conn.commit()
                for us in activ_chek():
                    cursor.execute(f"UPDATE bots SET program=1 WHERE id={us}")
                    conn.commit()
            print("Запуск")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        if o==5:
            info=get_system_info()
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                tt=datetime.now().strftime("%d.%m.%Y")
                cursor.execute(f"INSERT INTO pc_info (date,time,temperature ,cpu,ram ,work_time) VALUES ('{tt}','{str(info['time'])}','{str(info['temp'])}','{str(info['cpu'])}','{str(info['memory'])}','{str(info['uptime'])}')")
                conn.commit()
                o=0
        else:
            o=o+1
        time.sleep(29)

async def send_db_periodically():
    while True:
        try:
            now = datetime.now()
            await bot.send_document(CHANNEL_ID, FSInputFile("users.db"), caption=now.strftime("%d.%m.%Y %H:%M:%S"))
            await asyncio.sleep(1800)  # Асинхронный sleep (не time.sleep!)
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(10)


def chek_start(i):
    for user_id, processes in active_processes.items():
        if processes and str(i)==str(user_id):
            return True
    return False


async def deeeel(user_id, chat_id: int):
    base_path = Path(f"users/{user_id}")
    if not base_path.exists():
        await bot.send_message(chat_id, ("❌ Папка пользователя не найдена,обратитесь в поддержку") )
        return
    result = []
    exclude = {'.venv'}
    for root, dirs, files in os.walk(str(base_path)): 
        dirs[:] = [d for d in dirs if d not in exclude]
        level = root.replace(str(base_path), '').count(os.sep)
        indent = ' ' * 4 * level
        rel_path = os.path.relpath(root, str(base_path)) 
        
        if rel_path == '.':
            result.append(f"📁 {base_path.name}")
        else:
            result.append(f"{indent}📁 {os.path.basename(root)}")
            
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            result.append(f"{sub_indent}📄 {file}")
    
    structure = "\n".join(result) if result else "📂 Папка пуста"
    await bot.send_message(chat_id, (f"Структура файлов:\n\n{structure}") )

active_processes = defaultdict(list)

@dp.message(F.text == 'БД')
async def show_active_processes(message: types.Message):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    await message.answer_document(types.FSInputFile("users.db"))


@dp.message(F.text == 'CPU')
async def show_active_processes(message: types.Message):
    x=[]
    y=[]
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    await send_stats(message.chat.id)
    temp=(temperature())[::-1]
    tim=(timm())[::-1]
    if len(tim) >= 140:
        for i in range(140):
            y.append(int((temp[i][0])[:2]))
        for i in range(140):
            x.append(tim[i][0])
        plt.bar((x[::-1])[:-1],(y[::-1])[:-1])
        plt.xticks(rotation=90, fontsize=2)
    else:

        for i in range(len(temp)):
            y.append(int((temp[i][0])[:2]))
        for i in range(len(tim)):
            x.append(tim[i][0])
        plt.bar((x[::-1])[:-1],(y[::-1])[:-1])
        plt.xticks(rotation=90, fontsize=2)
    plt.savefig('temperature.jpg', dpi=1500, bbox_inches='tight')
    plt.close()  
    await message.answer_document(types.FSInputFile("temperature.jpg"))
    os.remove('temperature.jpg')
        
            



@dp.message(F.text == 'Количество процессов')
async def show_active_processes(message: types.Message):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    try:
        count = 0
        users_info = []
        for user_id, processes in active_processes.items():
            if processes:
                user_count = len(processes)
                count += user_count
                users_info.append(f"👤 Пользователь {user_id}: {user_count} процессов")
        
        # Формируем ответ
        if count == 0:
            await message.answer("🚫 Нет активных процессов")
            return
            
        report = [
            "📊 Активные процессы:",
            *users_info,
            "",
            f"✅ Всего процессов: {count}",
            f"👥 Пользователей с процессами: {len(users_info)}"
        ]
        
        await message.answer("\n".join(report))
        
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)} \n\nПоддержка 24/7 в шапке бота 🔝")

async def run_script_async(python_exec: str, file_path: str, user_id: int, bot: Bot, chat_id: int,qq):
    """Запускает скрипт с поддержкой вложенных папок и файлов"""
    print(python_exec, file_path, user_id, bot, chat_id,qq)
    try:
        os.remove(f'logs/{user_id}_logs.txt')
    except:
        pass
    open(f'logs/{user_id}_logs.txt', 'a').close()
    count[user_id]=0
    user_dir = os.path.abspath(f"users/{user_id}")
    global y_n
    print(y_n.get(chat_id, "Не введена"))

    process = await asyncio.create_subprocess_exec(
        python_exec,
        os.path.basename(file_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=user_dir,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    
    active_processes[user_id].append(process)
    
    async def read_output():
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        buffer = ""
        try:
            while True:
                chunk = await process.stdout.read(4096)
                if not chunk:
                    break
                decoded = decoder.decode(chunk)
                if decoded:
                    buffer += decoded
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        log_msg = f" [USER {user_id} LOG!!] {line.strip()}"
                        print(log_msg)  # В консоль
                        try:
                            if qq=="Да":
                                await bot.send_message(chat_id, log_msg)
                            with open(f'logs/{user_id}_logs.txt', 'a') as file:
                                file.write((datetime.now().strftime('%d.%m.%Y %H:%M'))+log_msg + '\n')
                                count[user_id] += 1
                            if count[user_id]>1000:
                                with open(f'logs/{user_id}_logs.txt', 'r', encoding='utf-8') as fin, \
                                    open(f'logs/{user_id}_logss.txt', 'w', encoding='utf-8') as fout:
                                    # пропускаем первую строку
                                    next(fin)
                                    # копируем остальные строки
                                    for line in fin:
                                        fout.write(line)
                                os.replace(f'logs/{user_id}_logss.txt', f'logs/{user_id}_logs.txt')
                        except:
                            pass
        finally:
            await process.wait()
            active_processes[user_id].remove(process)
            if buffer:
                log_msg = f"[USER {user_id} LOG!] {buffer.strip()}"
                print(log_msg)  # В консоль
                try:
                    if qq=="Да":
                        await bot.send_message(chat_id, log_msg)
                    with open(f'logs/{user_id}_logs.txt', 'a') as file:
                        file.write((datetime.now().strftime('%d.%m.%Y %H:%M'))+log_msg + '\n')
                        count[user_id] += 1
                    if count[user_id]>1000:
                        with open(f'logs/{user_id}_logs.txt', 'r', encoding='utf-8') as fin, \
                            open(f'logs/{user_id}_logss.txt', 'w', encoding='utf-8') as fout:
                            # пропускаем первую строку
                            next(fin)
                            # копируем остальные строки
                            for line in fin:
                                fout.write(line)
                        os.replace(f'logs/{user_id}_logss.txt', f'logs/{user_id}_logs.txt')
                except:
                    pass
    
    asyncio.create_task(read_output())
    return process




async def start2(i):
    all_info=file_info(i)
    name=(all_info)[2]
    yes_no=(all_info)[4]
    try:
        os.remove(f'logs/{i}_logs.txt')
    except:
        pass
    open(f'logs/{i}_logs.txt', 'a').close()
    user_dir = Path(f"users/{i}").resolve()
    venv_dir = Path(f"users/{i}/.venv").resolve()

    file_path = user_dir / name     
    python_exec = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python_exec.exists():
        python_exec = next((p for p in venv_dir.glob("bin/python*") if p.exists()), None)
    if not python_exec:
        raise FileNotFoundError("Интерпретатор Python не найден")
    process = await asyncio.create_subprocess_exec(
        python_exec,
        os.path.basename(file_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=user_dir,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    active_processes[i].append(process)
    async def read_output():
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        buffer = ""
        try:
            while True:
                chunk = await process.stdout.read(4096)
                if not chunk:
                    break
                decoded = decoder.decode(chunk)
                if decoded:
                    buffer += decoded
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        log_msg = f"[USER {i} LOG!!] {line.strip()}"
                        print(log_msg)  # В консоль
                        try:
                            if yes_no=="Да":
                                await bot.send_message(i, log_msg)
                            with open(f'logs/{i}_logs.txt', 'a') as file:
                                file.write((datetime.now().strftime('%d.%m.%Y %H:%M'))+log_msg + '\n')
                                count[i] += 1
                            if count[i]>1000:
                                with open(f'logs/{i}_logs.txt', 'r', encoding='utf-8') as fin, \
                                    open(f'logs/{i}_logss.txt', 'w', encoding='utf-8') as fout:
                                    # пропускаем первую строку
                                    next(fin)
                                    # копируем остальные строки
                                    for line in fin:
                                        fout.write(line)
                                os.replace(f'logs/{i}_logss.txt', f'logs/{i}_logs.txt')
                        except:
                            pass
        finally:
            await process.wait()
            active_processes[i].remove(process)
            if buffer:
                log_msg = f"[USER {i} LOG!] {buffer.strip()}"
                print(log_msg)  # В консоль
                try:
                    if yes_no=="Да":
                        await bot.send_message(i, log_msg)
                    with open(f'logs/{i}_logs.txt', 'a') as file:
                        file.write((datetime.now().strftime('%d.%m.%Y %H:%M'))+log_msg + '\n')
                        count[i] += 1
                    if count[i]>1000:
                        with open(f'logs/{i}_logs.txt', 'r', encoding='utf-8') as fin, \
                            open(f'logs/{i}_logss.txt', 'w', encoding='utf-8') as fout:
                            # пропускаем первую строку
                            next(fin)
                            # копируем остальные строки
                            for line in fin:
                                fout.write(line)
                        os.replace(f'logs/{i}_logss.txt', f'logs/{i}_logs.txt')
                except:
                    pass

    asyncio.create_task(read_output())
    return process


async def check_subscription(user_id):
    member = await bot.get_chat_member(chat_id="-1002535341751", user_id=user_id)
    if not(member.status in ["member", "administrator", "creator"]):
        await bot.send_message(user_id,
            "📢 Для использования бота необходимо подписаться на канал!\n"
            "После подписки нажмите кнопку ниже:",
            reply_markup=chanel_keybord)
        return False
    else:
        return True

async def start_csv():
    global channel_id
    stt=start_ckript()
    print(stt)
    for i in stt:
        await start2(i=i[0])


@dp.message(F.text.lower() == 'iluz')
async def stop_script(message: types.Message):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    await message.answer("Добро пожаловать Админ!",reply_markup=admin_keyboard)
    
@dp.message(F.text == 'Users')
async def stop_script(message: types.Message, state: FSMContext):
    global admin
    await message.answer(f"Пользователей {count_piple()[0][0]}")
    user_id = message.from_user.id
    if not(user_id in admin):
        return
    df = userss()
    with open("users.txt","a") as file:
        for i in df:
            file.write(f"@{i[1]} ID: {i[0]} Balance: {i[2]}₽\n")
    await message.answer_document(types.FSInputFile("users.txt"))
    os.remove('users.txt')



@dp.message(F.text == 'По 1 файлу')
async def create_zip_handler(message: types.Message, state: FSMContext):
    await state.set_state(BroadcastState.dow)
    user_id = message.from_user.id
    await deeeel(user_id=user_id,chat_id=message.chat.id)
    await message.answer("Выбери файл или папку",reply_markup=otmena_keyboard)


@dp.message(StateFilter(BroadcastState.dow))
async def create_zip_handler(message: types.Message):
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Отправить надо тестом!")
        return
    
    try:
        search_path = Path(f"users/{user_id}")
        target = message.text.strip()

        # Ищем все совпадения с фильтрацией
        found_files = [
            p for p in search_path.rglob(target) 
            if '.venv' not in p.parts and p.exists()
        ]

        if not found_files:
            await message.answer(f"❌ Файл/папка '{target}' не найдена или доступ запрещен!")
            return
        
        for file_path in found_files:
            # Пропускаем скрытые файлы и системные папки
            if file_path.name.startswith('.') or file_path.name == '__pycache__':
                continue

            # Дополнительная проверка для вложенных .venv
            if any(part == '.venv' for part in file_path.parts):
                continue

            if file_path.is_dir():
                # Создаем временный файл для архива
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                    zip_filename = tmp.name
                    
                    with zipfile.ZipFile(zip_filename, 'w') as zipf:
                        for root, dirs, files in os.walk(file_path):
                            # Исключаем папку .venv при обходе
                            dirs[:] = [d for d in dirs if d != '.venv']
                            
                            for file in files:
                                full_path = Path(root) / file
                                if '.venv' in full_path.parts:
                                    continue
                                
                                arcname = os.path.relpath(full_path, file_path)
                                zipf.write(full_path, arcname)

                    # Отправляем архив
                    with open(zip_filename, 'rb') as f:
                        await message.answer_document(
                            document=BufferedInputFile(
                                f.read(), 
                                filename=f"{file_path.name}.zip"
                            ),
                            caption=f"Архив папки: {file_path.name}"
                        )
            
            else:
                # Отправка отдельных файлов
                with open(file_path, 'rb') as f:
                    await message.answer_document(
                        document=BufferedInputFile(
                            f.read(),   
                            filename=file_path.name
                        ),
                        caption=f"Файл: {file_path.name}"
                    )

        await message.answer("✅ Все доступные файлы отправлены")

    except Exception as e:
        logger.error(f"File send error: {str(e)}")
        await message.answer(f"⚠️ Произошла ошибка: {str(e)}\n\nПоддержка 24/7 в шапке бота 🔝")

@dp.message(F.text == 'Все')
async def create_zip_handler(message: types.Message):
    await message.answer("Загрузка...",reply_markup=download)
    user_id = message.from_user.id
    user_dir = f"users/{user_id}"
    zip_filename = f"{user_id}.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(user_dir):
            if '.venv' in dirs:
                dirs.remove('.venv')
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, user_dir)
                zipf.write(file_path, arcname)
    with open(zip_filename, 'rb') as file:
        await message.answer_document(
            document=BufferedInputFile(file.read(), filename=zip_filename),
            caption="Ваши файлы:")
    os.remove(zip_filename)
    await new(message.from_user.id,message.from_user.username)




@dp.message(F.text == 'Все вместе,архивом')
async def stop_script(message: types.Message, state: FSMContext):
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    await state.set_state(BroadcastState.shea_file)
    await message.answer("Отправьте ZIP-архив со всеми необходимыми файлами и папками; он будет разархивирован и добавлен в основную директорию.\nВ архиве не должно быть виртуального окружения",reply_markup=otmena_keyboard)
    await new(message.from_user.id,message.from_user.username)

@dp.message(F.content_type.in_({'document'}), StateFilter(BroadcastState.shea_file))
async def handle_file(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        doc = message.document
        user_dir = f"users/{user_id}"
        file_path = os.path.join(user_dir, doc.file_name)
        await message.bot.download(doc, destination=file_path) 
        
        file_ext = doc.file_name.split('.')[-1].lower()
        
        if file_ext not in ('zip'):
            await message.answer("Пожалуйста, отправьте архив в формате ZIP")
            return
        if file_ext == 'zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Получаем список всех элементов в архиве
                namelist = zip_ref.namelist()
                
                # Проверяем, все ли файлы находятся внутри одной корневой директории
                root_dirs = {name.split('/')[0] for name in namelist if '/' in name}
                
                if len(root_dirs) == 1:
                    # Если есть одна корневая директория - извлекаем только её содержимое
                    root_dir = root_dirs.pop()
                    for member in namelist:
                        # Пропускаем саму корневую директорию
                        if member == root_dir + '/':
                            continue
                        
                        # Формируем новый путь без корневой директории
                        new_path = member[len(root_dir)+1:]
                        if not new_path:
                            continue
                        
                        # Создаём полный путь для извлечения
                        full_path = os.path.join(user_dir, new_path)
                        
                        # Создаём директории, если это папка
                        if member.endswith('/'):
                            os.makedirs(full_path, exist_ok=True)
                        else:
                            # Извлекаем файл
                            with zip_ref.open(member) as source, open(full_path, 'wb') as target:
                                target.write(source.read())
                else:
                    # Если нет единой корневой директории - извлекаем как обычно
                    zip_ref.extractall(user_dir)
                await message.answer("Готово") 
            os.remove(f"users/{user_id}/{doc.file_name}")
        await state.clear()
    except TelegramBadRequest as e:
        await message.answer("Файл слишком большой")
    except:
        await message.answer("Ошибка с файлом")

    
@dp.message(F.text == 'Показать файлы')
async def show_files(message: types.Message): 
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    user_id = message.from_user.id
    base_path = Path(f"users/{user_id}")
    
    if not base_path.exists():
        await message.answer("❌ Папка пользователя не найдена") 
        return
    
    result = []
    exclude = {'.venv'}
    
    for root, dirs, files in os.walk(str(base_path)): 
        dirs[:] = [d for d in dirs if d not in exclude]
        
        level = root.replace(str(base_path), '').count(os.sep)
        indent = ' ' * 4 * level
        rel_path = os.path.relpath(root, str(base_path)) 
        
        if rel_path == '.':
            result.append(f"📁 {base_path.name}")
        else:
            result.append(f"{indent}📁 {os.path.basename(root)}")
            
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            result.append(f"{sub_indent}📄 {file}")
    
    structure = "\n".join(result) if result else "📂 Папка пуста"
    if len(structure)>4000:
        with open(f"file_{user_id}" , "a") as file:
            file.write(structure)
            await message.answer_document(types.FSInputFile(f"file_{user_id}"))
            os.remove(f"file_{user_id}")
    else:
        await message.answer(f"Структура файлов:\n\n{structure}") 
    await new(message.from_user.id,message.from_user.username)

@dp.message(F.text == 'Удалить файлы')
async def stop_script(message: types.Message, state: FSMContext):
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    h="Выбери способ удаления:"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkDAAImWWf6kz3peHN3mu6_upRaJM0V1wxWAALn5DEbWQPZS6jLzurt0PIWAQADAgADdwADNgQ",
            caption=h,
            reply_markup=delete,
            parse_mode='HTML')
    except:
        await message.answer_photo(
        photo=FSInputFile("photo/delete.jpg"),
        caption=h,
        reply_markup=delete,
        parse_mode='HTML')


@dp.message(F.text=="Сообщения")
async def adminn(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    await message.answer("Выбри сообщения:",reply_markup=sms_keyboard)

@dp.message(F.text=="Инфа")
async def adminn(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    df = userss()
    with open("users.txt","a") as file:
        for i in df:
            file.write(f"@{i[1]} ID: {i[0]} Balance: {i[2]}₽\n")
    await message.answer_document(types.FSInputFile("users.txt"))
    os.remove('users.txt')
    await message.answer("Введи ID пользователя",reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.infostate)
    
@dp.message(StateFilter(BroadcastState.infostate))
async def stop_script(message: types.Message, state: FSMContext):
    try:
        id_inf=int(message.text)
    except:
        await message.answer("Нужно просто цифры")
        return
    info_from_id=one_user(id_inf)
    if info_from_id==[]:
        await message.answer("Нет человека с таким id")
        return
    info_from_id=info_from_id[0]
    skript=file_info(id_inf)
    print(skript)
    if skript == None:
        skript="Ни один скрипт не был запущен"
    else:
        print(skript)

        skript=f"Главный файл: {skript[2]}\nПрограмма: {skript[3]}\nЛоги: {skript[4]}"
    await message.answer(f"Юзер @{info_from_id[1]}\nID {info_from_id[0]}\nБаланс: {info_from_id[2]}₽\nДата регестрации {info_from_id[3]}\n"+skript)
    user_id = id_inf
    base_path = Path(f"users/{user_id}")
    
    if not base_path.exists():
        await message.answer("❌ Папка пользователя не найдена") 
        return
    
    result = []
    exclude = {'.venv'}
    
    for root, dirs, files in os.walk(str(base_path)): 
        dirs[:] = [d for d in dirs if d not in exclude]
        
        level = root.replace(str(base_path), '').count(os.sep)
        indent = ' ' * 4 * level
        rel_path = os.path.relpath(root, str(base_path)) 
        
        if rel_path == '.':
            result.append(f"📁 {base_path.name}")
        else:
            result.append(f"{indent}📁 {os.path.basename(root)}")
            
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            result.append(f"{sub_indent}📄 {file}")
    
    structure = "\n".join(result) if result else "📂 Папка пуста"
    if len(structure)>4000:
        with open(f"file_{user_id}" , "a") as file:
            file.write(structure)
            await message.answer_document(types.FSInputFile(f"file_{user_id}"))
            os.remove(f"file_{user_id}")
    else:
        await message.answer(f"Структура файлов:\n\n{structure}") 
    await message.answer(f"Готово",reply_markup=admin_keyboard) 
    await state.clear()

@dp.message(F.text=="Сообщение пользователю")
async def adminn(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global admin
    if not(user_id==admin):
        return
    await message.answer("Введи ID пользователя",reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.sms)

@dp.message(StateFilter(BroadcastState.sms))
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global us
    if not message.text:
        await message.answer("Отправить надо тестом!")
        return
    us=message.text
    await message.answer("Теперь отправь сообщение")
    await state.clear()
    await state.set_state(BroadcastState.sms2)

@dp.message(StateFilter(BroadcastState.sms2))
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global us

async def broadcast_message(message: types.Message, state: FSMContext, bot_message):
    """Рассылает сообщение всем пользователям"""
    await message.answer("Начинаю рассылку...")
    pol=all_id()
    for user_id in pol:
        await send_message_to_user(user_id[0], bot_message)
        await asyncio.sleep(0.2)  # Задержка что бы не заблочили бота
    await message.answer("Рассылка завершена!")

@dp.message(F.text == "file")
async def start_broadcast_handler(message: types.Message, state: FSMContext):
    global admin
    user_id = message.from_user.id
    if not(user_id in admin):
        return
    df = userss()
    with open("users.txt","a") as file:
        for i in df:
            file.write(f"@{i[1]} ID: {i[0]} Balance: {i[2]}₽\n")
    await message.answer_document(types.FSInputFile("users.txt"))
    os.remove('users.txt')
    await message.answer("Введи ID пользователя",reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.file_chek)


@dp.message(StateFilter(BroadcastState.file_chek))
async def create_zip_handler(message: types.Message, state: FSMContext):
    global filr_ch
    if not message.text:
        await message.answer("Отправить надо тестом!")
        return
    try:
        if one_user(message.text)==[]:
            await message.answer("Пользователь не найден")
            return
        filr_ch=message.text
    except:
        await message.answer("Ошибка")
        return
    h="Выбери пункт:"
    await message.answer(h,reply_markup=download_id)
    await state.clear()

@dp.message(F.text == 'Все file')
async def create_zip_handler(message: types.Message):
    global filr_ch
    await message.answer("Загрузка...",reply_markup=download)
    user_id = filr_ch
    user_dir = f"users/{user_id}"
    zip_filename = f"{user_id}.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(user_dir):
            if '.venv' in dirs:
                dirs.remove('.venv')
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, user_dir)
                zipf.write(file_path, arcname)
    with open(zip_filename, 'rb') as file:
        await message.answer_document(
            document=BufferedInputFile(file.read(), filename=zip_filename),
            caption="Ваши файлы:")
    os.remove(zip_filename)
    await new(message.from_user.id,message.from_user.username)

@dp.message(F.text == "По 1 file")
async def start_broadcast_handler(message: types.Message, state: FSMContext):
    
    await message.answer("Введи название файлв",reply_markup=otmena_keyboard)


@dp.message(F.text == "Рассылка")
async def start_broadcast_handler(message: types.Message, state: FSMContext):
    """Обработчик команды /send_broadcast"""
    global admin
    user_id = message.from_user.id
    if not(user_id in admin):
        return
    await message.answer("Отправьте мне сообщение, которое вы хотите разослать пользователям:")
    await state.set_state(BroadcastState.waiting_for_message)  # Переключаем бота в состояние ожидания сообщения для рассылки
@dp.message(StateFilter(BroadcastState.waiting_for_message))
async def get_broadcast_message_handler(message: types.Message, state: FSMContext):
    """Получение сообщения для рассылки"""
    global admin
    user_id = message.from_user.id
    if not(user_id in admin):
        return
    await state.update_data(message_to_broadcast=message)  # Сохраняем сообщение
    await message.answer(
        f"Вы хотите отправить следующее сообщение пользователям:\n{message.text if message.text else 'Фото или другой тип сообщения'}\n\nНажмите /confirm для подтверждения или отправьте другое сообщение, чтобы изменить")
    await state.set_state(BroadcastState.waiting_for_confirmation)  # Переключаем бота в состояние ожидания подтверждения


@dp.message(Command("confirm"), StateFilter(BroadcastState.waiting_for_confirmation))
async def confirm_broadcast_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    global admin
    if not(user_id in admin):
        return
    data = await state.get_data()
    message_to_broadcast = data.get("message_to_broadcast")
    await broadcast_message(message, state, message_to_broadcast)  # Вызываем функцию рассылки
    await state.clear()  # Очищаем состояние

@dp.message(F.text == 'Удалить 1 файл')
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    user_id = message.from_user.id
    base_path = Path(f"users/{user_id}")
    
    if not base_path.exists():
        await message.answer("❌ Папка пользователя не найдена") 
        return
    
    result = []
    exclude = {'.venv'}
    
    for root, dirs, files in os.walk(str(base_path)): 
        dirs[:] = [d for d in dirs if d not in exclude]
        
        level = root.replace(str(base_path), '').count(os.sep)
        indent = ' ' * 4 * level
        rel_path = os.path.relpath(root, str(base_path)) 
        
        if rel_path == '.':
            result.append(f"📁 {base_path.name}")
        else:
            result.append(f"{indent}📁 {os.path.basename(root)}")
            
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            result.append(f"{sub_indent}📄 {file}")
    
    structure = "\n".join(result) if result else "📂 Папка пуста"
    if len(structure)>4000:
        with open(f"file_{user_id}" , "a") as file:
            file.write(structure)
            await message.answer_document(types.FSInputFile(f"file_{user_id}"))
            os.remove(f"file_{user_id}")
    else:
        await message.answer(f"Структура файлов:\n\n{structure}") 
    await message.answer("Введи название файла вместе с его расширением (например, photo.jpg):",reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.delete_state)
    await new(message.from_user.id,message.from_user.username)

@dp.message(StateFilter(BroadcastState.delete_state))
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Отправить надо тестом!")
        return
    safe_filename = os.path.basename(message.text)  # Защита от path traversal
    user_dir = os.path.abspath(f"users/{user_id}")
    file_path = os.path.join(user_dir, safe_filename)
    if not os.path.exists(file_path):
        await message.answer(f"❌ Файл {safe_filename} не найден!")
        return
    protected = ['.venv', 'venv', '__pycache__']
    if any(part in protected for part in file_path.split(os.sep)):
        await message.answer("⛔ Удаление системных файлов запрещено!")
        return
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            msg = f"✅ Файл {safe_filename} успешно удален"
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            msg = f"✅ Папка {safe_filename} и ее содержимое удалены"
        await message.answer(msg)  # Удаляем подпапки и их содержимое
    except Exception as e:
        await message.answer(f"Ошибка при удалении {file_path}: {e}\n\nПоддержка 24/7 в шапке бота 🔝")
    await message.answer(f"Продолжайте отправлять названия файлов или нажмите отмена ↓")
    

    
    



@dp.message(F.text == 'Удалить все')
async def stop_script(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    folder_path = f"users/{user_id}"
    try:
        folder_path
        # Перебираем все элементы в папке
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if filename == ".venv":
                continue
                
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Удаляем файлы и симлинки
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Удаляем подпапки и их содержимое
            except Exception as e:
                await message.answer(f"Ошибка при удалении {file_path}: {e}\n\nПоддержка 24/7 в шапке бота 🔝")

        await message.answer(f"Основная директория успешно очищена")
        
    except Exception as e:
        await message.answer(f"Общая ошибка: {e}")

@dp.message(F.text == 'Библиотеки')
async def stop_script(message: types.Message, state: FSMContext):
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    h="Что вы хотите сделать с библиотекой: скачать или удалить?"
    # h="Введи название библиотеки одним словом (например, 'aiogram') и дождись завершения установки:"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkDAAImUmf6kqIaJiO978TprcGg1vzNXmV7AALe5DEbWQPZSwJZBc7J019HAQADAgADdwADNgQ",
            caption=h,
            reply_markup=library_yes_no,
            parse_mode='HTML'
        )
    except:
        await message.answer_photo(
            photo=FSInputFile("photo/library.jpg"),
            caption=h,
            reply_markup=library_yes_no,
            parse_mode='HTML')
    await state.set_state(BroadcastState.library)
    await new(message.from_user.id,message.from_user.username)

@dp.message(F.text=="Удалить", StateFilter(BroadcastState.library))
@dp.message(F.text=="Скачать", StateFilter(BroadcastState.library))
async def handle_file(message: types.Message, state: FSMContext):
    libra[message.from_user.id]=message.text
    if message.text=="Скачать":
        h="Введи название библиотеки одним словом (например, 'aiogram') и дождись завершения установки:"
    else:
        await message.answer("Загрузка...")
        try:
            user_id = message.from_user.id
            venv_dir = Path(f"users/{user_id}/.venv")
            venv_dir.mkdir(parents=True, exist_ok=True)
            pip_path = venv_dir / "Scripts" / "pip.exe" if sys.platform == "win32" else venv_dir / "bin" / "pip"
            h="Введи название библиотеки одним словом (например, 'aiogram') и дождись удаления библиотеки:"
            process =(subprocess.run(
                    [str(pip_path), "list"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=400))
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
            return
        await message.answer(process.stdout)
    await message.answer(h,reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.library_yes)

@dp.message(F.content_type.in_({'text'}), StateFilter(BroadcastState.library_yes))
async def handle_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Надо ввести текстом")
        return
    library_name = message.text.strip()
    venv_dir = Path(f"users/{user_id}/.venv")
    venv_dir.mkdir(parents=True, exist_ok=True)
    all_libraries = ["psutil","os","requests","http.client","pyautogui","selenium","exec","eval","subprocess","importlib","urllib","shutil","pickle","cryptography","pyCrypto","fake_useragent","requests-html","beautifulsoup4","scapy","pwn","paramiko","socket","fuzzywuzzy","pip"]
    for i in all_libraries:
        if str(message.text) in i:
            await message.answer(f"Библиотека {str(message.text)} запрещена")
            return
    pip_path = venv_dir / "Scripts" / "pip.exe" if sys.platform == "win32" else venv_dir / "bin" / "pip"
    try:
        if libra[message.from_user.id]=="Скачать":
            await message.answer("Загрузка...")
            process = subprocess.run(
                [str(pip_path), "install", library_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=400)
            await message.answer(f"✅ Успешное установлено:\n{process.stdout[:4000]}")
        else:
            await message.answer("Загрузка...")
            process = subprocess.run(
                [str(pip_path), "uninstall", "-y", library_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=400)
            if process=="":
                await message.answer("Данная библиотека не найдена")
                return
            await message.answer(f"✅ Библиотека удалена успешно:\n{process.stdout[:4000]}")
    except subprocess.CalledProcessError as e:
        await message.answer(f"❌ Ошибка установки/удаления:\n{e.stderr[:4000]}\n\nПоддержка 24/7 в шапке бота 🔝")
    except subprocess.TimeoutExpired:
        await message.answer("⌛ Превышено время ожидания")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}\n\nПоддержка 24/7 в шапке бота 🔝")
    

@dp.message(F.text == 'Стоп')
async def stop_script(message: types.Message):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(user_id)=="1624096187":
        pass
    else:
        return
    user_dir = Path(f"users/{user_id}").resolve()

    # Ищем все процессы пользователя
    processes = []
    for proc in psutil.process_iter():
        try:
            if proc.cwd() == str(user_dir) and "python" in proc.name().lower():
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not processes:
        await message.answer("Нет активных процессов!", reply_markup=main_keyboard)
        return

    killed = []
    for proc in processes:
        try:
            # Останавливаем процесс и всех потомков
            for child in proc.children(recursive=True):
                child.kill()
            proc.kill()
            killed.append(str(proc.pid))
        except Exception as e:
            logger.error(f"Ошибка остановки PID {proc.pid}: {e}\n\nПоддержка 24/7 в шапке бота 🔝")

    if killed:
        await message.answer(f"✅ Остановлены процессы: {', '.join(killed)}", reply_markup=main_keyboard)
    else:
        await message.answer("❌ Не удалось остановить процессы", reply_markup=main_keyboard)
    
@dp.message(F.text == 'Без архива')
async def stop_script(message: types.Message, state: FSMContext):
    if await check_subscription(message.from_user.id) or str(message.from_user.id)=="1624096187":
        pass
    else:
        return
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    await message.answer("Отправь файл в оригинальном формате без виртуального окружения (venv и тд.), без сжатия и архивации ❗️❗️❗️",reply_markup=otmena_keyboard)
    await state.set_state(BroadcastState.one_file)
    await new(message.from_user.id,message.from_user.username)

@dp.message(
    F.content_type.in_({
        ContentType.DOCUMENT,
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.AUDIO,
        ContentType.VOICE,
        ContentType.VIDEO_NOTE,
        ContentType.STICKER
    }),
    StateFilter(BroadcastState.one_file)
)
async def handle_file(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    SAVE_FOLDER = f"users/{user_id}"
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    try:
        # Определяем тип файла и получаем объект файла
        file_obj = None
        file_type = None
        mime_type = None

        if message.document:
            file_obj = message.document
            file_type = 'document'
            mime_type = file_obj.mime_type
        elif message.photo:
            file_obj = message.photo[-1]  # Берем фото максимального качества
            file_type = 'photo'
            mime_type = 'image/jpeg'
        elif message.video:
            file_obj = message.video
            file_type = 'video'
            mime_type = 'video/mp4'
        elif message.audio:
            file_obj = message.audio
            file_type = 'audio'
            mime_type = 'audio/mpeg'
        elif message.voice:
            file_obj = message.voice
            file_type = 'voice'
            mime_type = 'audio/ogg'
        elif message.video_note:
            file_obj = message.video_note
            file_type = 'video_note'
            mime_type = 'video/mp4'
        elif message.sticker:
            file_obj = message.sticker
            file_type = 'sticker'
            mime_type = 'image/webp' if message.sticker.is_animated else 'image/webp'

        if not file_obj:
            await message.answer("Формат файла не поддерживается")
            return

        # Генерируем имя файла
        timestamp = int(time.time())
        ext = mimetypes.guess_extension(mime_type) or '.bin'
        
        if file_type == 'document' and file_obj.file_name:
            file_name = file_obj.file_name
        else:
            # Убираем точку в расширении если есть
            ext = ext.lstrip('.')
            file_name = f"{file_type}_{timestamp}.{ext}"

        # Получаем file_id и скачиваем файл
        file_id = file_obj.file_id
        tg_file = await bot.get_file(file_id)
        file_path = os.path.join(SAVE_FOLDER, file_name)

        await bot.download_file(tg_file.file_path, destination=file_path)
        await message.answer(f"Файл {file_name} успешно сохранен!")
        
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}\n\nПоддержка 24/7 в шапке бота 🔝")
        await state.clear()

@dp.message(F.text == 'Запустить')
async def process_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await check_subscription(message.from_user.id) or str(user_id)=="1624096187":
        pass
    else:
        return
    if chek_start(i=user_id):
        await message.answer("Ваш процесс уже запущен!")
        return
    h="Хотите получать информацию от скрипта (логи) в чат? Обратите внимание, что логи в любом будут сохраняться в разделе 'Логи'"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkDAAImVGf6krJoxdXQsStOmoBjgvTqvgOWAALf5DEbWQPZS8WmCDLRHc5_AQADAgADdwADNgQ",
            caption=h,
            reply_markup=yes_no_keyboard,
            parse_mode='HTML')
    except:
        await message.answer_photo(
                photo=FSInputFile("photo/global_file.jpg"),
                caption=h,
                reply_markup=yes_no_keyboard,
                parse_mode='HTML')
    await state.set_state(BroadcastState.yes_no)


@dp.message(F.text.in_(['Да','Нет']), StateFilter(BroadcastState.yes_no))
async def process_start(message: types.Message, state: FSMContext):
    await message.answer("Загрузка...")
    user_id = message.from_user.id
    
    async def check_forbidden_code(directory):
        forbidden = {
        # Базовые опасные функции
        "eval(", "exec(", "os.system(", "subprocess.Popen(", "shutil.rmtree(",
        
        # Обфускация выполнения кода
        ".decode('base64')", "String.fromCharCode(",  # JS-специфично
        "b64decode(", "getattr(sys.modules['os'], 'sy'",
        "f'os.system({user_input})'",  # f-строки с прямым вызовом
        
        # Подозрительные вызовы с shell
        "shell=True", "subprocess.run(..., shell=True)",
        
        # Опасные модули/импорты
        "import os; os.system(", "from os import system",
        "__import__('os').system(", "ctypes.WinDLL(",
        
        # Файловые операции с удалением        
        # Сетевые операции с динамическими параметрами
        "requests.get(unsafe_input)", "urllib.urlopen(UNTRUSTED_URL)",
        "socket.create_connection((HOST, PORT))",
        
        # Инъекции через форматирование (явные случаи)
        "execute(f\"DROP TABLE {var}\")",  # SQL-инъекция в строке
        "eval(f'os.system({user_input})')",
        
        # Подозрительная рефлексия
        "sys._getframe(", "inspect.currentframe()",
        
        # Обход через Unicode (явные homoglyph)
        "оs.system",  # кириллическая 'о'
        "sуstem("     # Unicode-замена символов
        
        # Опасные десериализаторы
        "pickle.load(", "marshal.loads(", "yaml.unsafe_load(",
        
        # Шифрование/пакеты (в опасном контексте)
        "zlib.decompress(", "tarfile.extractall()",
        
        # Контейнеры/вредоносные API
        "docker.from_env().containers.run(", "kubernetes.client.CoreV1Api",
        
        # JS-специфичные опасности (если контекст включает веб)
        "eval(request.cookies)", "document.write(UNSAFE_HTML)", "subprocess.run(","os.system(","os.popen("
    }
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = Path(root) / filename
                if '.venv' in file_path.parts:  # Правильно проверяем наличие каталога .venv в пути
                    continue
                    
                try:
                    with open(file_path, "r", encoding='utf-8') as f:
                        for line in f:
                            if any(s in line for s in forbidden):
                                await message.answer(
                                    f"Файл: {file_path.name}\n\n"
                                    f"⛔️Запрещенные символы в строке⛔️\n{(str(line))[:3000]}"
                                )
                                return False
                except Exception as e:
                    logger.error(f"Ошибка чтения файла {file_path}: {e}")
        return True

    try:
        if not(str(user_id) == str(admin) or str(user_id) == "6523058852" or str(user_id) == "7765076958"):
            if not await check_forbidden_code(f"users/{user_id}"):
                return



        # Проверка основного файла
        current_file = chek_file(user_id)
        if str(current_file)=="None":
            await message.answer("Сначала выберите основной файл!")
            return
        else:
            current_file=current_file[0]
        yes(user_id,message.text)
        qq=message.text
        user_dir = Path(f"users/{user_id}").resolve()
        file_path = user_dir / current_file
        
        if not file_path.exists():
            await message.answer("Основной файл не найден!")
            return

        # Настройка виртуального окружения
        venv_dir = user_dir / ".venv"
        python_exec = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        
        if not python_exec.exists():
            python_exec = next((p for p in venv_dir.glob("bin/python*") if p.exists()), None)
            if not python_exec:
                raise FileNotFoundError("Интерпретатор Python не найден")

        if not os.access(python_exec, os.X_OK):
            python_exec.chmod(0o755)
        process = await run_script_async(
            python_exec, 
            file_path, 
            user_id,
            qq=qq,
            bot=message.bot,
            chat_id=message.chat.id,
        )
        
        await message.answer(f"🚀 Скрипт запущен! PID: {process.pid}", reply_markup=notmain_keyboard)

    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}\n\nПоддержка 24/7 в шапке бота 🔝"
        logger.exception(error_msg)
        await message.answer(error_msg)


@dp.message(F.text == 'Файлы')
async def process_start(message: types.Message, state: FSMContext):
    await state.set_state(BroadcastState.shea_file)
    h=f"Выбери пункт для упаравления файлами:"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkDAAIm6Gf6nYM-SrjXQTmAxPwTvm_IYQZhAAJD5TEbWQPZS58os2iltGUYAQADAgADdwADNgQ",
            caption=h,
            reply_markup=file_keyboard,
            parse_mode='HTML')
    except:
        await message.answer_photo(
            photo=FSInputFile("photo/file_global.jpg"),
            caption=h,
            reply_markup=file_keyboard,
            parse_mode='HTML')
    await new(message.from_user.id,message.from_user.username)



@dp.message(F.text == 'Основной файл')
async def process_main_file(message: types.Message, state: FSMContext):
    current_file = chek_file(message.from_user.id)
    if message.from_user.id in activ_chek():
        await message.answer("Эта функция недоступна, пока выполняется запущенный скрипт")
        return
    await state.set_state(BroadcastState.glav_file)
    try:
        if not(str(current_file)=="None"):
            h=f"Текущee имя основного файла: {current_file[0]}\nВведите новое имя для файла:"
            await message.answer_photo(
                photo="AgACAgIAAxkDAAImWGf6kzxeRE-yYhLsE_UUvzb4Lm2CAALm5DEbWQPZSx_cRnCxbXrzAQADAgADdwADNgQ",
                caption=h,
                reply_markup=otmena_keyboard,
                parse_mode='HTML'
            )
        else:
            h="Введите название основного файла (например main.py):"
            await message.answer_photo(
                photo="AgACAgIAAxkDAAImWGf6kzxeRE-yYhLsE_UUvzb4Lm2CAALm5DEbWQPZSx_cRnCxbXrzAQADAgADdwADNgQ",
                caption=h,
                reply_markup=otmena_keyboard,
                parse_mode='HTML'
            )
    except Exception as e:
        try:
            if not(str(current_file)=="nan"):
                h=f"Текущee имя основного файла: {current_file}\nВведите новое имя для файла:"
                await message.answer_photo(
                    photo=FSInputFile("photo/file.jpg"),
                    caption=h,
                    reply_markup=otmena_keyboard,
                    parse_mode='HTML'
                )
            else:
                h="Введите название основного файла (например main.py):"
                await message.answer_photo(
                    photo=FSInputFile("photo/file.jpg"),
                    caption=h,
                    reply_markup=otmena_keyboard,
                    parse_mode='HTML'
                )
        except:
            logger.error(f"Main file error: {e}")
            await message.answer("Ошибка!\n\nПоддержка 24/7 в шапке бота 🔝")
    await new(message.from_user.id,message.from_user.username)

@dp.message(F.text == 'Скачать')
async def stop_script(message: types.Message, state: FSMContext):
    h="Выбери пункт:"
    try:
        await message.answer_photo(
            photo="AgACAgIAAxkDAAImi2f6lgNlOt2x9H9NQw4XmN6p8mjtAAID5TEbWQPZS33uugROgYKyAQADAgADdwADNgQ",
            caption=h,
            reply_markup=download,
            parse_mode='HTML')
    except:
        await message.answer_photo(
        photo=FSInputFile("photo/download.jpg"),
        caption=h,
        reply_markup=download,
        parse_mode='HTML')

@dp.message(StateFilter(BroadcastState.glav_file))
async def handle_main_file(message: types.Message, state: FSMContext):
    
    try:
        new_file = message.text.strip() 
        if not new_file.endswith('.py'):
            await message.answer("Файл должен иметь расширение .py!")
            return  
        if '/' in new_file or '\\' in new_file:
            await message.answer("Недопустимые символы в имени файла!")
            return
        user_id=str(message.from_user.id)
        if chek_file(user_id) == None:
            nev_file(message.from_user.username,user_id,new_file,0,"Нет")
        else:
            replase_file(user_id,new_file)
        if active_processes.get(user_id):
            await message.answer(f"✅ Основной файл установлен: {new_file}",reply_markup=notmain_keyboard)
        else:
            await message.answer(f"✅ Основной файл установлен: {new_file}",reply_markup=main_keyboard)
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"File handling error: {e}")
        await message.answer("Произошла ошибка!\n\nПоддержка 24/7 в шапке бота 🔝")
        await state.clear()
    await new(message.from_user.id,message.from_user.username)

@dp.message()
async def process_main_file(message: types.Message, state: FSMContext):
    await message.answer("Не понимаю тебя, напиши /start")
    await new(message.from_user.id,message.from_user.username)

async def on_startup():
    """Запускается при старте бота"""
    asyncio.create_task(send_db_periodically())  # Запускаем в фоне
    print("✅ Бот запущен, фоновая отправка базы данных активирована")

async def main():
    await start_csv()
    dp.startup.register(on_startup)
    r=Thread(target=test_aktivate)
    r.start()
    await dp.start_polling(bot)



if __name__ == "__main__":
    try:
        logger.info("Запуск бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        
        logger.info("Бот остановлен")
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
