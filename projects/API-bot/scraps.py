import requests
from bs4 import BeautifulSoup, Tag


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWe"
    "bKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36"
}


def get_daily_news() -> str:
    url = "https://ria.ru"

    try:
        reply = requests.get(url)
        reply.raise_for_status()
    except requests.RequestException as error:
        print(error)
        return ""

    pars = BeautifulSoup(reply.text, "html.parser")
    if isinstance(pars, BeautifulSoup):
        quote = pars.find("div", class_="cell-list__item m-no-image")
        if isinstance(quote, Tag):
            text_module = quote.find("a", class_="cell-list__item-link")
            if isinstance(text_module, Tag):
                text = text_module.get_text(strip=True)

                return f"На повестке дня: {text[:-5]} - {text[-5:]}"
    return ""


def get_count_for_summer() -> str:
    url = "https://www.calc.ru/dney-do-leta.html?back=https:// \
    www.google.com/search?client=safari&as_qdr=all&as_occt=" \
    "any&safe=active&as_q=сколько+лет+дней+до+лета&channel\
    =aplab&source=a-app1&hl=ru&clckid=c78545d8"

    try:
        reply = requests.get(url)
        reply.raise_for_status()
    except requests.RequestException as error:
        print(error)
        return ""

    pars = BeautifulSoup(reply.text, "html.parser")

    if isinstance(pars, BeautifulSoup):
        quote = pars.find("div", class_="text")
        if isinstance(quote, Tag):
            text_div = quote.find("div", id="count")
            if isinstance(text_div, Tag):
                text = text_div.get_text(strip=True)

                return f"До лета осталось {text}"
    return ""


def get_radiotapok_concert_date() -> str:
    url = "https://radiotapok.ru/"

    try:
        reply = requests.get(url, headers=headers)
        reply.raise_for_status()
    except requests.RequestException as error:
        print(error)
        return ""

    pars = BeautifulSoup(reply.text, "html.parser")

    if isinstance(pars, BeautifulSoup):
        quote = pars.find("div", class_="col-md-12 ticket row")
        if isinstance(quote, Tag):
            date_div = quote.find("div",
                                  class_="col-md-3 col-xs-3 conc_date pad0")
            city_div = quote.find("div", class_="col-md-5 col-xs-5 pad0")
            if isinstance(date_div, Tag) and isinstance(city_div, Tag):
                city_div = city_div.find("div", class_="ticket_city")
                if city_div:
                    city = city_div.get_text(strip=True)
                date = date_div.get_text(strip=True)

                return f"Следующий концерт Радиотапка {date} в городе {city}"
    return ""
