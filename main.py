import os
import asyncio
import aiosqlite
from dotenv import load_dotenv
from openai import AsyncOpenAI


def load_config():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY not found")
    base_url = os.getenv("BOTHUB_BASE_URL", "https://bothub.chat/api/v2/openai/v1")
    model = os.getenv("JOKE_MODEL", "gpt-3.5-turbo")
    return api_key, base_url, model


def create_client(api_key, base_url):
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def get_system_message():
    return {
        "role": "system",
        "content": "Ты бот, рассказывающий анекдоты. Отвечай кратко и с юмором. Избегай темы про политику и жестокость."
    }


async def init_db():
    async with aiosqlite.connect("chat.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        await db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (session_id) REFERENCES sessions (id))")
        await db.commit()


async def create_session():
    async with aiosqlite.connect("chat.db") as db:
        cursor = await db.execute("INSERT INTO sessions DEFAULT VALUES")
        await db.commit()
        return cursor.lastrowid


async def add_message(session_id, role, content):
    async with aiosqlite.connect("chat.db") as db:
        await db.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
        await db.commit()


async def get_context(session_id):
    async with aiosqlite.connect("chat.db") as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 10", (session_id,))
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


async def handle_command(cmd, session_id):
    if cmd == "/history":
        history = await get_context(session_id)
        for msg in history:
            print(f"{msg['role'].upper()}: {msg['content']}")
        return "handled"
    elif cmd == "/sessions":
        async with aiosqlite.connect("chat.db") as db:
            async with db.execute("SELECT id, created_at FROM sessions ORDER BY id DESC LIMIT 5") as cursor:
                async for row in cursor:
                    print(f"ID: {row[0]}, Created: {row[1]}")
        return "handled"
    return None


async def request_joke(client, model, system_message, context):
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[system_message] + context,
                temperature=0.8
            ),
            timeout=30
        )
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return None
    except asyncio.TimeoutError:
        print("\nTimeout.")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


async def main():
    try:
        api_key, base_url, model = load_config()
    except ValueError as e:
        print(f"Config error: {e}")
        return

    client = create_client(api_key, base_url)
    await init_db()
    session_id = await create_session()
    system_message = get_system_message()

    print(f"Session: {session_id}. Commands: /new, /history, /sessions, /exit")

    while True:
        try:
            user_text = await asyncio.to_thread(input, "\n> ")
        except (KeyboardInterrupt, EOFError):
            break

        cmd = user_text.strip().lower()

        if cmd == "/exit":
            break
        elif cmd == "/new":
            session_id = await create_session()
            print(f"Session: {session_id}")
            continue
        
        result = await handle_command(cmd, session_id)
        if result == "handled":
            continue

        if not user_text:
            continue

        await add_message(session_id, "user", user_text)
        context = await get_context(session_id)
        
        response = await request_joke(client, model, system_message, context)

        if response:
            print(f"Bot: {response}")
            await add_message(session_id, "assistant", response)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())