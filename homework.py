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
URL_PRAKTIKUM = 'https://praktikum.yandex.ru/api/user_api/{method}/'
CHECK_STR = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
HOMEWORK_STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'),
    'reviewing': 'Работа взята в проверку.',
    'unknown': ('У работы {homework_name} неизвестный '
                'статус: {status}')
}
REQUEST_EXEPTION = 'Проблемы с ответом от сервера. {ex}'
DATE_ERROR = 'Ошибка в указании даты'
JSON_ERROR = 'Проблемы с получением информации из json(). {er}'
ERROR_MESSAGE = 'Бот столкнулся с ошибкой: {e}'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name == None:
        message = JSON_ERROR.format(er=er)
        raise Exception(message)
    status = homework['status']
    if status == 'reviewing':
        return HOMEWORK_STATUSES['reviewing']
    verdict = None
    if status == 'rejected':
        verdict = HOMEWORK_STATUSES['rejected']
    elif status == 'approved':
        verdict = HOMEWORK_STATUSES['approved']
    else:
        logging.error('Ошибка в определении статуса работы')
        message = HOMEWORK_STATUSES['unknown'].format(
            homework_name=homework_name,
            status=status
        )
        raise Exception(message)
    return CHECK_STR.format(
        homework_name=homework_name, 
        verdict=verdict
    )


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        message = DATE_ERROR
        raise ValueError(message)
    headers = {
        'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN
    }
    params = {
        'from_date': current_timestamp
    }
    method = 'homework_statuses'
    try:
        homework_statuses = requests.get(
            URL_PRAKTIKUM.format(method=method),
            headers=headers,
            params=params
        )
    except requests.RequestException as ex:
        message = REQUEST_EXEPTION.format(ex=ex)
        raise ex(message)
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
    #current_timestamp = int(time.time())
    current_timestamp = 0

    while True:
        try:
            new_homework = get_homework_statuses(
                current_timestamp)
            get_new_homework = new_homework.get('homeworks')
            if get_new_homework:
                send_message(
                    parse_homework_status(get_new_homework[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)

        except Exception as e:
            message = ERROR_MESSAGE.format(e=e)
            logging.error(message, exc_info=True)
            bot_client.send_message(
                chat_id=CHAT_ID,
                text = message
            )
            time.sleep(5)


if __name__ == '__main__':
    main()
