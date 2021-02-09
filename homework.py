import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_PRAKTIKUM = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    # Инициализирую бота внутри функции, т.к. pytest
    # не дает в функцию передать больше одного параметра.
    try:
        homework_name = homework.get('homework_name')
    except KeyError as er:
        message = f'Проблемы с получением информации из json(). {er}'
        logging.error(er, exc_info=True)
        bot_client.send_message(CHAT_ID, message)
    status = homework['status']
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:  # status == 'appruved':
        verdict = 'Ревьюеру всё понравилось, '\
                  'можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    # Инициализирую бота внутри функции, т.к. pytest
    # не дает в функцию передать больше одного параметра.
    if current_timestamp is None:
        raise ValueError('Ошибка в указании даты')
    headers = {
        'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN
    }
    params = {
        'from_date': current_timestamp
    }
    try:
        homework_statuses = requests.get(
            URL_PRAKTIKUM,
            headers=headers,
            params=params
        )
    except requests.RequestException as ex:
        message = f'Проблемы с ответом от сервера. {ex}'
        logging.error(message, exc_info=True)
        bot_client = bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        bot_client.send_message(CHAT_ID, message)
    logging.debug('Ответ от сервера Я.Практикум получен')
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Сообщение отправлено ботом в чат')
    return bot_client.send_message(
        chat_id=CHAT_ID,
        text=message
    )


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Бот активирован')
    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        try:
            new_homework = get_homework_statuses(
                current_timestamp, bot_client)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
