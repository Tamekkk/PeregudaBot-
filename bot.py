import logging
import re
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from openai import AsyncOpenAI

# Загрузка переменных окружения из .env файла
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токенов из переменных окружения
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not OPENROUTER_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Необходимо указать OPENROUTER_API_KEY и TELEGRAM_TOKEN в .env файле")

client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
router = Router()
dp.include_router(router)

user_context = {}
HISTORY_LIMIT = 10

@router.message(Command('start'))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_context[user_id] = []
    await message.answer("Привет! Я готов ответить на твои вопросы.")

@router.message(Command('clear'))
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    user_context[user_id] = []
    await message.answer("История диалога очищена.")

@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text
    logger.info(f"Получено сообщение от пользователя {user_id}: {user_message}")

    if user_id not in user_context:
        user_context[user_id] = []

    user_context[user_id].append({"role": "user", "content": user_message})

    if len(user_context[user_id]) > HISTORY_LIMIT:
        user_context[user_id] = user_context[user_id][-HISTORY_LIMIT:]

    try:
        completion = await client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=user_context[user_id]
        )

        logger.info(f"LABA2: {completion}")

        if completion and hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            content = choice.message.content
            cleaned_content = re.sub(r'<.*?>', '', content).strip()

            if cleaned_content:
                bot_response = f"*LABA2:*\n\n{cleaned_content}"
                user_context[user_id].append({"role": "assistant", "content": cleaned_content})
            else:
                bot_response = "*LABA2 не содержит нужной информации.*"
                logger.error("Ответ LABA2 от нейросети пустой.")
        else:
            bot_response = "*Извините, я не получил корректный ответ от нейросети. Пожалуйста, попробуйте позже.*"

    except Exception as e:
        bot_response = f"*Произошла ошибка:* {str(e)}"
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")

    logger.info(f"Отправка сообщения пользователю {user_id}: {bot_response}")
    await message.answer(bot_response)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())