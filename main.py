import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI


MAX_HISTORY_MESSAGES = 10


def load_config():
    load_dotenv()

    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("В .env не найден API_KEY")

    base_url = os.getenv("BOTHUB_BASE_URL", "https://bothub.chat/api/v2/openai/v1")
    model = os.getenv("JOKE_MODEL", "gpt-3.5-turbo")

    return api_key, base_url, model


def create_client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


def get_system_message():
    return {
        "role": "system",
        "content": (
            "Ты бот, который рассказывает анекдоты, шутки и короткие смешные истории. "
            "Если пользователь задает тему — шути по теме. "
            "Если тема не указана — расскажи любой хороший анекдот. "
            "Шутки должны быть добрыми, без грубости, оскорблений и политики."
        ),
    }


def trim_history(history: list[dict]) -> None:
    if len(history) > MAX_HISTORY_MESSAGES:
        del history[:-MAX_HISTORY_MESSAGES]


def print_help():
    print("\nКоманды:")
    print("  анекдот / расскажи анекдот")
    print("  анекдот про ...")
    print("  история")
    print("  очистить")
    print("  статистика")
    print("  помощь")
    print("  выход")


def show_history(history: list[dict]):
    if not history:
        print("История пуста.")
        return

    print("\nПоследние сообщения:")
    for i, msg in enumerate(history, start=1):
        role = "Вы" if msg["role"] == "user" else "Бот"
        text = msg["content"].strip().replace("\n", " ")
        if len(text) > 120:
            text = text[:120] + "..."
        print(f"{i}. {role}: {text}")


def show_stats(request_count: int, history: list[dict], model: str, base_url: str):
    print("\nСтатистика:")
    print(f"  Анекдотов получено: {request_count}")
    print(f"  Сообщений в истории: {len(history)}")
    print(f"  Модель: {model}")
    print(f"  API endpoint: {base_url}")
    print(f"  Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def handle_command(text: str, history: list[dict], request_count: int, model: str, base_url: str):
    cmd = text.strip().lower()

    if cmd in {"выход", "exit", "quit", "q"}:
        print(f"Пока. За эту сессию получено анекдотов: {request_count}")
        return "exit"

    if cmd in {"помощь", "help", "?"}:
        print_help()
        return "handled"

    if cmd in {"история", "history", "h"}:
        show_history(history)
        return "handled"

    if cmd in {"очистить", "clear", "c"}:
        history.clear()
        print("История очищена.")
        return "handled"

    if cmd in {"статистика", "stats", "s"}:
        show_stats(request_count, history, model, base_url)
        return "handled"

    return None


def request_joke(
    client: OpenAI,
    model: str,
    system_message: dict,
    history: list[dict],
    user_text: str,
) -> str | None:
    messages = [system_message] + history + [{"role": "user", "content": user_text}]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=300,
            frequency_penalty=0.5,
            presence_penalty=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка API: {e}")
        print("Проверь API_KEY, баланс, base_url и интернет-соединение.")
        return None


def main():
    try:
        api_key, base_url, model = load_config()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        print("Создай файл .env и добавь строку:")
        print("API_KEY=твой_ключ")
        sys.exit(1)

    try:
        client = create_client(api_key, base_url)
    except Exception as e:
        print(f"Не удалось создать клиента: {e}")
        sys.exit(1)

    system_message = get_system_message()
    history: list[dict] = []
    request_count = 0

    print("Анекдот-бот запущен.")
    print(f"Модель: {model}")
    print(f"Храню до {MAX_HISTORY_MESSAGES} последних сообщений.")
    print("Напиши 'помощь', чтобы увидеть команды.")

    while True:
        try:
            user_text = input("\nВы: ").strip()
        except KeyboardInterrupt:
            print("\nВыход.")
            break
        except EOFError:
            print("\nВыход.")
            break

        if not user_text:
            continue

        command_result = handle_command(user_text, history, request_count, model, base_url)
        if command_result == "exit":
            break
        if command_result == "handled":
            continue

        joke = request_joke(client, model, system_message, history, user_text)
        if joke is None:
            continue

        print(f"Бот: {joke}")

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": joke})
        trim_history(history)

        request_count += 1


if __name__ == "__main__":
    main()
