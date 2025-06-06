from datetime import datetime
import os
import platform
import sys
import logging
import asyncio
import tempfile
from threading import Thread
import zipfile
import pandas
from aiogram.filters import or_f
import zipfile
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from datetime import time
import time
import signal
from datetime import datetime
import threading
import mimetypes
import time
import codecs
import traceback,shutil
from aiogram.types import BufferedInputFile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from aiogram.types import Message
from collections import defaultdict
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import subprocess
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters import StateFilter
import pandas as pd
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.types import InputFile 
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ContentType
df = pd.read_csv("users.csv", sep=';')
# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Конфигурация
TOKEN = "8064787079:AAEeiUgA6T0aGBj2pX13x-KPysYfgmZfuQA"
admin=5143785189
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

id_from_user=1
sell_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить", callback_data="buyy")]
    ]
)

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Редактировать меню')],
        [KeyboardButton(text='Сообщение человеку'),
         KeyboardButton(text='Подписчики')],
        [KeyboardButton(text='Назад')]],
    resize_keyboard=True
)

otmena_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]],
    resize_keyboard=True)


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Меню'),
        KeyboardButton(text='О нас')]],
    resize_keyboard=True
)
many_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Полное меню')],
        [KeyboardButton(text='Рулет меренговый'),
         KeyboardButton(text='Десерт в стакане')],
        [KeyboardButton(text='Пирожное Анна Павлова'),
         KeyboardButton(text='')],
        [KeyboardButton(text='Назад')]],
    resize_keyboard=True
)



redukt_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Полное меню')],
        [KeyboardButton(text='Рулет меренговый'),
         KeyboardButton(text='Десерт в стакане')],
        [KeyboardButton(text='Пирожное Анна Павлова'),
         KeyboardButton(text='')],
        [KeyboardButton(text='Отмена')]],
    resize_keyboard=True
)

class BroadcastState(StatesGroup):
    zakaz = State()
    sms =State()
    sms1 =State()
    punkt=State()
    text_global=State()
    text1=State()
    text2=State()
    text3=State()
    text4=State()
    photo_global=State()
    photo1=State()
    photo2=State()
    photo3=State()
    photo4=State()
    

async def cek_photo(ph):
    df = pd.read_csv("post.csv", sep=';')
    y=(df[df['number'] == str(ph)])['photo'].iloc[0]
    return y

async def cek_info(clik):
    df = pd.read_csv("post.csv", sep=';')
    x=(df[df['number'] == str(clik)])['text'].iloc[0]
    return x

async def subscribers():
    t=[]
    df = pd.read_csv("users.csv", sep=';')
    id_list = df["ID"].tolist()
    user_list = df["Name"].tolist()
    for i in range(len(id_list)):
        us=f"{str(user_list[i])}"
        if us == "@None":
            us= "Нет"
        t.append(f'{i+1}) Имя: {us} ID: {id_list[i]}')
    return t

async def BZ(username,ID):
    df = pd.read_csv("users.csv", sep=';')
    l=df["ID"].tolist()
    if not(ID in l):
        new_row = pd.DataFrame([{'Name': f'@{username}', 'ID': ID}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("users.csv", sep=';', index=False)
        await bot.send_message(chat_id=str(admin),text=f"Зарегистрирован новый пользователь \n @{username}\nID: {ID}")
    else:
        df.loc[df[df['ID'] == ID].index,"Name"]=str(f"@{username}")
        df.to_csv("users.csv", sep=';', index=False)

@dp.message(F.text == 'Отмена', StateFilter('*'))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo="AgACAgIAAxkBAAMIaBD51DXYPWbHQEUgz6qXCMd4Y7YAAjb1MRvAfIhIBLsTl99B6XABAAMCAAN5AAM2BA",
        caption="Добро пожаловать в мой телеграм-магазин пирожных! 🎂✨ \n\nПредлагаю вам небольшой ассортимент свежих и вкусных пирожных, приготовленных с любовью и только из качественных ингредиентов. Здесь вы найдете классические рецепты, которые порадуют вас и ваших близких.\nПриятные цены!\nТолько самовывоз!\n\nПрисоединяйтесь к нам и наслаждайтесь сладкими моментами каждый день 🍰❤️",
        reply_markup=main_keyboard,
        
        parse_mode='HTML')
    await state.clear()


@dp.message(F.text == 'Назад')
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer_photo(
        photo="AgACAgIAAxkBAAMIaBD51DXYPWbHQEUgz6qXCMd4Y7YAAjb1MRvAfIhIBLsTl99B6XABAAMCAAN5AAM2BA",
        caption="Добро пожаловать в мой телеграм-магазин пирожных! 🎂✨ \n\nПредлагаю вам небольшой ассортимент свежих и вкусных пирожных, приготовленных с любовью и только из качественных ингредиентов. Здесь вы найдете классические рецепты, которые порадуют вас и ваших близких.\nПриятные цены!\nТолько самовывоз!\n\nПрисоединяйтесь к нам и наслаждайтесь сладкими моментами каждый день 🍰❤️",
        reply_markup=main_keyboard,
        
        parse_mode='HTML')
    await state.clear()


@dp.message((F.text).lower() == 'админ')
async def cmd_start(message: types.Message, state: FSMContext):
    global admin
    if not(str(message.from_user.id) == str(admin)):
        return
    await message.answer("Добро подаловать в админ панель", reply_markup=admin_keyboard)

@dp.message(F.text == 'Сообщение человеку')
async def cmd_start(message: types.Message, state: FSMContext):
    global admin
    if not(str(message.from_user.id) == str(admin)):
        return
    t=await subscribers()
    cht=len(t)
    while True:
        await message.answer('\n'.join(t[:70]))
        if cht >= 70:
            del t[:70]
            cht=cht-70
        else:
            break

    await message.answer("Введите ID человека которому хотите отправить сообщение:")
    await state.set_state(BroadcastState.sms)

@dp.message(F.text == 'Редактировать меню')
async def cmd_start(message: types.Message, state: FSMContext):
    global admin
    if not(str(message.from_user.id) == str(admin)):
        return
    await message.answer("Выбери пункт который хотите отредактировать", reply_markup=redukt_keyboard)
    await state.set_state(BroadcastState.punkt)


@dp.message((lambda message: message.text in ['Полное меню', 'Капкейки', 'Пирожное Анна Павлова', 'Рулет меренговый', 'Десерт в стакане']) and StateFilter(BroadcastState.punkt))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if str(message.text) == 'Полное меню':
        await state.set_state(BroadcastState.text_global)
    elif str(message.text) == 'Рулет меренговый':
        await state.set_state(BroadcastState.text1)
    elif str(message.text) == 'Десерт в стакане':
        await state.set_state(BroadcastState.text2)
    elif str(message.text) == 'Пирожное Анна Павлова':
        await state.set_state(BroadcastState.text3)
    elif str(message.text) == 'Капкейки':
        await state.set_state(BroadcastState.text4)  
    await message.answer("Введите текст который будет отображаться в этом пункте:",reply_markup=otmena_keyboard)


@dp.message(
    or_f(
        BroadcastState.text_global,
        BroadcastState.text1,
        BroadcastState.text2,
        BroadcastState.text3,
        BroadcastState.text4
    ),
    F.text
)
async def cmd_start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    mess = message.text.replace('\n', '<br>')
    
    try:
        df = pd.read_csv("post.csv", sep=';')
        
        # Определяем условие через текущее состояние
        state_mapping = {
            BroadcastState.text_global.state: 'menu',
            BroadcastState.text1.state: 'cake',
            BroadcastState.text2.state: 'cookie',
            BroadcastState.text3.state: 'muffins',
            BroadcastState.text4.state: 'cupcakes'
        }
        
        condition = state_mapping.get(current_state)
        if not condition:
            await message.answer("Неизвестное состояние", reply_markup=otmena_keyboard)
            return
        df.loc[df['number'] == condition, 'text'] = mess
        df.to_csv("post.csv", sep=';', index=False)
        
        await message.answer("Теперь отправьте фотографию(если фотография не нужна просто напишите 'Нет')", reply_markup=redukt_keyboard)
        await state.clear()
        if condition == "menu":
            await state.set_state(BroadcastState.photo_global) 
        elif condition == 'cake':
            await state.set_state(BroadcastState.photo1)
        elif condition == 'cookie':
            await state.set_state(BroadcastState.photo2) 
        elif condition == 'muffins':
            await state.set_state(BroadcastState.photo3) 
        elif condition == 'cupcakes':
            await state.set_state(BroadcastState.photo4) 

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("Ошибка при обработке данных")




@dp.message(
    or_f(
        BroadcastState.photo_global,
        BroadcastState.photo1,
        BroadcastState.photo2,
        BroadcastState.photo3,
        BroadcastState.photo4
    )
)
async def cmd_start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    df = pd.read_csv("post.csv", sep=';')
    state_mapping = {
            BroadcastState.photo_global.state: 'menu',
            BroadcastState.photo1.state: 'cake',
            BroadcastState.photo2.state: 'cookie',
            BroadcastState.photo3.state: 'muffins',
            BroadcastState.photo4.state: 'cupcakes'
        }
    condition = state_mapping.get(current_state)
    if (str(message.text)).lower() == "нет":
        df.loc[df['number'] == str(condition), 'photo'] = "None"
        df.to_csv("post.csv", sep=';', index=False)
        await message.answer('Отлчно, фотография не добавлена', reply_markup=redukt_keyboard)
        await state.set_state(BroadcastState.punkt)
        return
    else:
        if message.text:
            await message.answer("Неизвестный ответ", reply_markup=otmena_keyboard)
            return
    photo_id = message.photo[-1].file_id
    df.loc[df['number'] == condition, 'photo'] = photo_id
    df.to_csv("post.csv", sep=';', index=False)
    await message.answer('Отлчно, фотография была добавлена', reply_markup=redukt_keyboard)
    await state.set_state(BroadcastState.punkt)




@dp.message(StateFilter(BroadcastState.sms))
async def cmd_start(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше все таки текстом")
        return
    global id_from_user
    id_from_user=message.text
    await message.answer("Введите текст который надо отправить человеку:")
    await state.clear()
    await state.set_state(BroadcastState.sms1)

@dp.message(StateFilter(BroadcastState.sms1))
async def cmd_start(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Лучше все таки текстом")
        return
    global id_from_user
    await bot.send_message(chat_id=id_from_user, text=f'Сообщение от администратора\n\n{message.text}')
    await message.answer("Сообщение отправлено")
    await state.clear()



@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await BZ(username=(message.from_user.username),ID=(message.from_user.id))
    await message.answer_photo(
        photo="AgACAgIAAxkBAAMIaBD51DXYPWbHQEUgz6qXCMd4Y7YAAjb1MRvAfIhIBLsTl99B6XABAAMCAAN5AAM2BA",
        caption="Добро пожаловать в мой телеграм-магазин пирожных! 🎂✨ \n\nПредлагаю вам небольшой ассортимент свежих и вкусных пирожных, приготовленных с любовью и только из качественных ингредиентов. Здесь вы найдете классические рецепты, которые порадуют вас и ваших близких.\nПриятные цены!\nТолько самовывоз!\n\nПрисоединяйтесь к нам и наслаждайтесь сладкими моментами каждый день 🍰❤️",
        reply_markup=main_keyboard,
        parse_mode='HTML')
    await state.clear()

@dp.message(F.text == 'Подписчики')
async def cmd_start(message: types.Message, state: FSMContext):
    global admin
    if not(str(message.from_user.id) == str(admin)):
        return
    t=await subscribers()
    cht=len(t)
    while True:
        await message.answer('\n'.join(t[:70]))
        if cht >= 70:
            del t[:70]
            cht=cht-70
        else:
            return
        
        
    



@dp.message(F.text == 'О нас')
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("О нас\nДобро пожаловать в наш магазин сладостей! Мы специализируемся на продаже разнообразных кексиков, печенек и других вкусных десертов, которые порадуют вас и ваших близких. Наша продукция изготавливается только из качественных ингредиентов с любовью и вниманием к каждой детали. Мы предлагаем как классические рецепты, так и уникальные авторские изделия, чтобы каждый мог найти что-то по своему вкусу. У нас вы найдете идеальные сладости для любого повода — от уютного чаепития до праздничного стола. Присоединяйтесь к нам и наслаждайтесь сладкими моментами каждый день!")
    await state.clear()
@dp.message(F.text == 'Меню')
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Выбери что именно ты хочешь увидеть:", reply_markup=many_keyboard)
    await state.clear()



@router.callback_query(F.data == "cancel")
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Удаляем оригинальное сообщение с фото
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Отправляем новое текстовое сообщение
    await callback.message.answer(
        text="Отмена\nВыберите пункт:",
        parse_mode="HTML",
        reply_markup=main_keyboard
    )
    await callback.answer()
    await state.clear()




@router.callback_query(F.data == "buyy")
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Удаляем оригинальное сообщение с фото
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Отправляем новое текстовое сообщение
    await callback.message.answer(
        text="📝 <b>Введите данные для заказа:</b>\n\n"
             "┌ Имя\n"
             "├ Номер телефона\n"
             "├ Список товаров (название × количество)\n"
             "└ Адрес доставки\n\n"
             "<i>Пример:</i>\n"
             "Анна Петрова\n"
             "+79161234567\n"
             "Кекс ванильный ×2, Капкейк клубничный ×1\n"
             "Москва, ул. Сладкая, д. 15, кв. 76",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel")]
        ])
    )
    await callback.answer()
    await state.set_state(BroadcastState.zakaz)



@dp.message(F.text == 'Десерт в стакане')
async def show_cookies(message: types.Message, state: FSMContext):
    y=str(await cek_photo("cookie"))
    x=(str(await cek_info("cookie"))).replace("<br>","\n")
    if y == "nan":
        await message.answer(x,reply_markup=sell_keyboard)
    else:
        await message.answer_photo(
            photo=y,
            caption=x,
            reply_markup=sell_keyboard,
            parse_mode=None,
        )
    await state.clear()

@dp.message(F.text == 'Рулет меренговый')
async def show_cupcakes(message: types.Message, state: FSMContext):
    y=str(await cek_photo("cake"))
    x=(str(await cek_info("cake"))).replace("<br>","\n")
    if y == "nan":
        await message.answer(x,reply_markup=sell_keyboard)
    else:
        await message.answer_photo(
            photo=y,
            caption=x,
            reply_markup=sell_keyboard,
            parse_mode=None,
        )
    await state.clear()


@dp.message(F.text == 'Пирожное Анна Павлова')
async def show_muffins(message: types.Message, state: FSMContext):
    y=str(await cek_photo("muffins"))
    x=(str(await cek_info("muffins"))).replace("<br>","\n")
    if y == "nan":
        await message.answer(x,reply_markup=sell_keyboard)
    else:
        await message.answer_photo(
            photo=y,
            caption=x,
            reply_markup=sell_keyboard,
            parse_mode=None,
        )
    await state.clear()

@dp.message(F.text == 'Капкейки')
async def show_cupcakes(message: types.Message, state: FSMContext):
    y=str(await cek_photo("cupcakes"))
    x=(str(await cek_info("cupcakes"))).replace("<br>","\n")
    if y == "nan":
        await message.answer(x,reply_markup=sell_keyboard)
    else:
        await message.answer_photo(
            photo=y,
            caption=x,
            reply_markup=sell_keyboard,
            parse_mode=None,
        )
    await state.clear()


@dp.message(F.text == 'Полное меню')
async def cmd_start(message: types.Message, state: FSMContext):
    y=str(await cek_photo("menu"))
    x=(str(await cek_info("menu"))).replace("<br>","\n")
    if y == "nan":
        await message.answer(x,reply_markup=sell_keyboard)
    else:
        await message.answer_photo(
            photo=y,
            caption=x,
            reply_markup=sell_keyboard,
            parse_mode=None,
        )
    await state.clear()

@dp.message(StateFilter(BroadcastState.zakaz))
async def cmd_start(message: types.Message, state: FSMContext):
    global admin
    user_id = message.from_user.id
    if str(f'@{message.from_user.username}') == "@None":
        uz="Отсутствует"
    else:
        uz=str(f'@{message.from_user.username}')

    await bot.send_message(admin,f'Новый заказ \nЧеловек: {uz}\nID: {message.from_user.id}\n\nТекст человека:\n{message.text}')
    await message.answer("Спасибо за заказ скоро вам напишет менеджер ")
    await state.clear()




@dp.message()
async def wrong_command(message: types.Message, state: FSMContext):
    await message.answer("Не понимаю тея напиши /start")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logger.info("Запуск бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        
        logger.info("Бот остановлен")
        
    except Exception as e:
        logger.error(f"Critical error: {e}")