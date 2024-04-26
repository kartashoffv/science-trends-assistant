import aiogram
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from arxiv_1 import ArxivPapers
from gigamodel import GigaModel

import os
import requests
from dotenv import load_dotenv
load_dotenv()

a = ArxivPapers()
model = GigaModel()
router = Router()
storage = MemoryStorage()


class FSMAdmin(StatesGroup):
    ft_get_query = State()
    ft_download_docs = State()
    ft_choose_doc_to_download = State()
    gt_get_query = State()
    add_doc = State()
    model = State()


# TODO: Написать приветственное сообщение с описанием (есть поиск статей, есть поиск статей+модель)
# TODO: Написать обработку resonse модели (сейчас возвращает словрь, который не отправляется в боте)
# TODO: Для минимально жизнеспособного решения: скачивание статей в папку - сборка раг по этой папке


TOKEN_TG = os.getenv('TOKEN_TG')
FOLDERPATH = os.getenv('FOLDERPATH')


def create_keyboard(values):
    kb = []
    for i in values:
        kb.append([types.KeyboardButton(text=i)])
    return kb


def download_paper_pdf(url, user_id):

    folder_path = f'{FOLDERPATH}/{user_id}'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_name = url.split("/")[-1] + '.pdf'
    file_path = os.path.join(folder_path, file_name)

    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)

        return f"Файл {file_name} успешно добавлен в базу"

    else:
        return "Ошибка при загрузке файла"


async def main():
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    bot = Bot(TOKEN_TG)
    await dp.start_polling(bot)


@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    start_message = """Приветствую! Я бот, основанный на модели Gigachat. Здесь вы можете использовать следующие команды:\n\n /get_papers_by_topic - для просмотра последних статей по выбранной теме.\n/find_trends_by_topic - для вывода ключевых идей из статей по выбранной теме и, при необходимости, сохранения их в базу знаний.\n/add_doc - чтобы добавить документ в базу знаний.\n\nКак я могу помочь вам сегодня?"""

    await message.answer(start_message)


@router.message(Command("get_papers_by_topic"))
async def get_papers_by_topic(message: types.Message, state: FSMContext):
    await message.answer('Введи запрос')
    await state.set_state(FSMAdmin.gt_get_query)


@router.message(FSMAdmin.gt_get_query)
async def get_p(message: types.Message, state: FSMContext):
    query = message.text

    papers = a.get_papers(query)[0]
    for paper in papers:
        await message.answer(paper)
    await state.clear()


@router.message(Command("find_trends_by_topic"))
async def find_trends(message: types.Message, state: FSMContext):
    await message.answer('Введи запрос')
    await state.set_state(FSMAdmin.ft_get_query)


@router.message(FSMAdmin.ft_get_query)
async def get_model_answer(message: types.Message, state: FSMContext):
    query = message.text
    papers = a.get_papers(query)
    paper_data = papers[0]
    paper_links = papers[1]

    kb = create_keyboard(paper_links.keys())
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    response = await model.answer(paper_data)
    response = str(response.content)
    await message.answer(response, reply_markup=keyboard)

    await state.set_state(FSMAdmin.ft_choose_doc_to_download)
    await state.update_data(papers_for_download=paper_links)


@router.message(FSMAdmin.ft_choose_doc_to_download)
async def choose_doc_to_download(message: types.Message, state: FSMContext):
    doc_name = message.text
    user_id = message.from_user.id

    data = await state.get_data()
    papers_for_download = data['papers_for_download']
    doc_url = papers_for_download[doc_name]

    status = download_paper_pdf(doc_url, user_id)
    await message.answer(status)
    await state.clear()


@router.message(Command("add_doc"))
async def get_doc(message: types.Message, state: FSMContext):
    await message.answer('Прикрепи файл, который нужно добавить в базу.')
    await state.set_state(FSMAdmin.add_doc)


@router.message(FSMAdmin.add_doc)
async def add_doc_to_base(message: types.Message, state: FSMContext, bot):
    doc = message.document
    print(doc.file_name)
    user_id = message.from_user.id
    folder_path = f'/Users/kartashoffv/Documents/gigachad/data/{user_id}/'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    else:
        if doc is not None:
            if (doc.mime_type == 'application/msword'
                or doc.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                or doc.mime_type == 'text/markdown'
                or doc.mime_type == 'text/plain'
                    or doc.mime_type == 'application/pdf'):

                file_id = doc.file_id
                file = await bot.get_file(file_id)
                await bot.download_file(file.file_path, folder_path+doc.file_name)
                await message.reply("Документ сохранен")
                await state.clear()
            else:
                await message.answer("Формат файла не поддерживается. Попробуйте, пожалуйста, еще раз с документом в формате .doc или .docx")
                await state.clear()


@router.message(Command("conversation"))
async def get_question(message: types.Message, state: FSMContext):
    await message.answer('Введите ваш запрос')
    await state.set_state(FSMAdmin.model)


@router.message(FSMAdmin.model)
async def answer_by_model(message: types.Message, state: FSMContext):
    question = message.text
    if '/clear' in question:
        await state.clear()
    response = await model.talk(question)
    await message.answer(str(response) + '\n\nДля выхода нажмите /clear')
    await state.set_state(FSMAdmin.model)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
