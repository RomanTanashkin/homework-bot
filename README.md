# Homework status bot

Telegram bot that polls an external REST API every 10 minutes and reports status changes of submitted homework to a chat. Written as an exercise in working with a third-party API, error handling and logging.

Built during the *Python Developer* course at Yandex Practicum (2025–2026). Every project was reviewed and accepted by a course mentor.

## What it does

1. Validates that all required tokens are present at start-up
2. Requests `homework_statuses` from the API with an OAuth header and a `from_date` timestamp
3. Validates the response structure and maps the status to a human-readable verdict
4. Sends a message only when the verdict changed, logs everything else
5. Any API, network or Telegram error is logged and reported to the chat once, without crashing the loop

## Tech stack

Python 3 · pyTelegramBotAPI · requests · logging · pytest

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```text
PRACTICUM_TOKEN=...
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

```bash
python homework.py
```

`Procfile` allows deployment to a PaaS that runs a worker process.

## Tests

```bash
pytest          # 25 tests
```

## Author

Roman Tanashkin — [github.com/RomanTanashkin](https://github.com/RomanTanashkin)
