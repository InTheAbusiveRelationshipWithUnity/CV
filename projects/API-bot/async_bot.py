import os
from dotenv import load_dotenv
import asyncio
from aiohttp import ClientSession
from sync_bot import get_daily_quote  # type: ignore
import scraps  # type: ignore
from typing import Any, Union


load_dotenv()
TOKEN = os.getenv("TOKEN")

user_states: dict[int, str] = {}


async def get_updates(session: ClientSession,
                      offset: Union[Any, None] = None)\
                      -> list[dict[str, Any]]:
    """
    Получение обновлений
    """
    paramets = {"timeout": 30}
    if offset:
        paramets["offset"] = offset
    if TOKEN:
        async with session.get("https://api.telegram.org/bot"
                               + TOKEN + "/getUpdates", params=paramets)\
                                as reply:
            json = await reply.json()
            result = json.get("result", [])
            if isinstance(result, list):
                return result
    return []


async def send_message(session: ClientSession,
                       chat_id: int, text: str) -> None:
    """
    Отправка сообщения пользователю
    """

    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if TOKEN:
        async with session.post("https://api.telegram.org/bot" +
                                TOKEN + "/sendMessage", json=payload):
            print("Message sent")


async def get_daily_quote_async() -> str:
    return await asyncio.to_thread(get_daily_quote)


async def get_daily_news_async() -> str:
    return await asyncio.to_thread(scraps.get_daily_news)


async def get_count_for_summer_async() -> str:
    return await asyncio.to_thread(scraps.get_count_for_summer)


async def get_radiotapok_concert_date() -> str:
    return await asyncio.to_thread(scraps.get_radiotapok_concert_date)


async def headline() -> str:
    """
    Функция для одновременного запуска
    скраперов
    """
    result = await asyncio.gather(
        get_daily_news_async(),
        get_count_for_summer_async(),
        get_radiotapok_concert_date()
    )

    message = "Текущее положение дел:\n"
    number = 0
    for i in result:
        number += 1
        message += f"{number}. {i}\n"

    return message


async def get_weather(city: str) -> str:
    """
    С помощью wttr api получаем информацию о погоде
    """
    url = f"https://wttr.in/{city}?format=3"
    async with ClientSession() as session:
        async with session.get(url) as reply:
            if reply.status == 200:
                return await reply.text()
            else:
                return f"Погода в {city} хуже юзера"


async def main() -> None:
    """
    Основной цикл работы бота
    """
    offset = None

    async with ClientSession() as session:
        while True:
            updates = await get_updates(session, offset)

            if not updates:
                continue

            for update in updates:
                update_id = update.get("update_id")
                message = update.get("message")
                if not isinstance(update_id, int) or not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message["text"]
                user_id = message["from"]["id"]

                if user_id in user_states:
                    weather = await get_weather(text)
                    await send_message(session, chat_id, weather)

                    user_states.pop(user_id)

                if text == "/quote":
                    quote = await get_daily_quote_async()
                    await send_message(session, chat_id, quote)
                elif text == "/start":
                    await send_message(session, chat_id, "Леееее")
                elif text == "/headline":
                    await send_message(session, chat_id, await headline())
                elif text == "/weather":
                    await send_message(session, chat_id,
                                       "Пожалуйста, введите название города.")
                    user_states[user_id] = "waiting_for_city"

                offset = update_id + 1


if __name__ == "__main__":
    asyncio.run(main())
