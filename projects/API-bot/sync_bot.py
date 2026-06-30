import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup, Tag
from typing import Any, Union


load_dotenv()
TOKEN = os.getenv("TOKEN")


def check_token() -> None:
    """
        Проверка подлинности токена
    """

    if TOKEN:
        url: str = "https://api.telegram.org/bot" + TOKEN + "/getMe"
    else:
        return

    try:
        reply = requests.get(url)
        reply.raise_for_status()
        data = reply.json()

        if data.get("ok"):
            print(data["result"].get("first_name", "-"))
            print(data["result"].get("username", "-"))
            print(data["result"].get("id", "-"))
        else:
            print("Unknown token")
    except requests.exceptions.RequestException as error:
        print(error)


def send_message(chat_id: int, text: str) -> None:
    """
    Отправка сообщения пользователю
    """
    if TOKEN:
        url: str = "https://api.telegram.org/bot" + TOKEN + "/sendMessage"
    else:
        return

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        reply = requests.post(url, json=payload)
        reply.raise_for_status()

        if not reply.json().get("ok"):
            print(reply.json().get("description"))

    except requests.exceptions.RequestException as error:
        print(error)


def get_updates(offset: Union[Any, None] = None,
                timeout: int = 30) -> list[dict[str, Any]]:
    """
    Получение обновлений
    """
    if TOKEN:
        url: str = "https://api.telegram.org/bot" + TOKEN + "/getUpdates"
    else:
        return []

    paramets = {"timeout": timeout}
    if offset:
        paramets["offset"] = offset

    try:
        reply = requests.get(url, params=paramets)
        reply.raise_for_status()

        if reply.json().get("ok"):
            answer = reply.json().get("result", [])
            if not isinstance(answer, list):
                return []

            return answer
        else:
            print(reply.json().get("description"))
            return []

    except requests.exceptions.RequestException as error:
        print(error)
        return []


def echo_bot() -> None:
    """
    Основной цикл работы синхронного бота
    """
    offset = None

    while True:
        updates = get_updates(offset)

        for update in updates:
            update_id = update.get("update_id")
            if not isinstance(update_id, int):
                continue

            message = update.get("message")

            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message["text"]

            if text == "/quote":
                send_message(chat_id, get_daily_quote())
            if text == "/start":
                send_message(chat_id, "Леееее")
            offset = update_id + 1


def get_daily_quote() -> str:
    """
    Функция-скрапер
    """
    url = "https://profkom.gaz.ru/projects/quote-of-the-day/"

    try:
        reply = requests.get(url)
        reply.raise_for_status()
    except requests.RequestException as error:
        print(error)
        return ""

    pars: BeautifulSoup = BeautifulSoup(reply.text, "html.parser")

    if pars and isinstance(pars, BeautifulSoup):
        quote = pars.find("div", class_="quote-of-the-day__item")
        if quote and isinstance(quote, Tag):
            text_div = quote.find("div", class_="item__quote")
            auth_div = quote.find("div", class_="item__quote-author")

            if isinstance(text_div, Tag) and isinstance(auth_div, Tag):
                text = text_div.get_text(strip=True)
                auth = auth_div.get_text(strip=True)
                return f"{text} - {auth}"

    return ""


"""import sys
if __name__ == "__main__":
    if len(sys.argv) == 1:
        check_token(sys.argv[1])
    elif len(sys.argv) == 3:
        send_message(int(sys.argv[1]), sys.argv[2])
    else:
        echo_bot()"""
