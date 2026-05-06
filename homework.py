import logging
import os
import time

import requests
import telebot
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Базовое исключение для ошибок при работе с API Практикума."""


class APIRequestError(APIError):
    """Ошибка при выполнении HTTP-запроса к API."""


class APIStatusCodeError(APIError):
    """API вернул неуспешный HTTP-статус."""


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing = [name for name, value in tokens.items() if not value]
    if missing:
        logger.critical(
            f'Отсутствуют обязательные переменные окружения: '
            f'{", ".join(missing)}'
        )
        return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение отправлено: {message}')
    except telebot.apihelper.ApiException as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        raise APIRequestError(f'Ошибка при запросе к API: {error}')
    if response.status_code != 200:
        raise APIStatusCodeError(
            f'API вернул код {response.status_code}: {response.text}'
        )
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарём.')
    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ "homeworks".')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является списком.')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутствует ключ "homework_name".')
    homework_name = homework['homework_name']
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы: {status}')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_if_new(bot, message, last_message):
    """Отправляет сообщение, если оно отличается от предыдущего."""
    if message != last_message:
        send_message(bot, message)
        return message
    return last_message


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s [%(levelname)s] '
            '%(funcName)s:%(lineno)d - %(message)s'
        ),
    )

    if not check_tokens():
        raise SystemExit('Программа остановлена.')

    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                last_message = send_if_new(bot, message, last_message)
            else:
                logger.debug('Новых статусов нет.')
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            last_message = send_if_new(bot, message, last_message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
