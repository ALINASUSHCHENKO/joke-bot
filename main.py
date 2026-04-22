import os
import sys
from datetime import datetime
from collections import deque
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class JokeBot:   
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError(
                "API-ключ не найден в .env\n"
            )
        
        self.base_url = os.getenv(
            "BOTHUB_BASE_URL", 
            "https://bothub.chat/api/v2/openai/v1"
        )
        self.model = os.getenv("JOKE_MODEL", "gpt-3.5-turbo")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.max_history = 10
        self.history: List[Dict[str, str]] = []
        
        self.system_prompt = {
            "role": "system",
            "content": (
                "Ты рассказчик анекдотов и шуток. "
                "Твои задачи:\n"
                "1. Рассказывать смешные и добрые анекдоты\n"
                "2. Если пользователь просит анекдот на тему - расскажи на эту тему\n"
                "3. Если тема не указана - расскажи любой хороший анекдот\n"
                "4. Отвечай только анекдотами, шутками и короткими историями\n"
                "5. Будь веселым\n"
                "6. Избегай грубых, оскорбительных или политических шуток"
            )
        }
        self.request_count = 0
        
    def add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def clear_history(self):
        self.history.clear()
        print("История диалога очищена.")
    
    def show_history(self):
        if not self.history:
            print("История пуста. Попросите меня рассказать анекдот!")
            return
        
        print("\n" + "=" * 60)
        print("История последних диалогов:")
        print("=" * 60)
        
        for i, msg in enumerate(self.history, 1):
            role_icon = "Вы" if msg["role"] == "user" else "Бот"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{i:2}. {role_icon}: {content}")
        
        print("=" * 60)
    
    def get_joke(self, user_input: str) -> Optional[str]:
        try:
            messages = [self.system_prompt] + self.history + [
                {"role": "user", "content": user_input}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=300,
                top_p=1.0,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            
            joke = response.choices[0].message.content
            self.request_count += 1
            
            return joke
            
        except Exception as e:
            print(f"\n Ошибка при обращении к API: {e}")
            print(" Возможные причины:")
            print(" Неверный API-ключ в файле .env")
            print(" Закончились средства на балансе Bothub")
            print(" Проблемы с интернет-соединением")
            return None
    
    def process_command(self, command: str) -> bool:
        cmd = command.lower().strip()
        
        if cmd in ['выход', 'exit', 'quit', 'q']:
            print(f"\n До скорого! За время сессии я рассказал {self.request_count} анекдотов!")
            return False
            
        elif cmd in ['история', 'history', 'h']:
            self.show_history()
            return True
            
        elif cmd in ['очистить', 'clear', 'c']:
            self.clear_history()
            return True
            
        elif cmd in ['помощь', 'help', '?']:
            self.show_help()
            return True
            
        elif cmd in ['статистика', 'stats', 's']:
            self.show_stats()
            return True
            
        return None
    
    def show_help(self):
        print("\n" + "=" * 60)
        print(" ДОСТУПНЫЕ КОМАНДЫ: ")
        print("=" * 60)
        print("  'анекдот' или 'расскажи анекдот' - получить случайный анекдот")
        print("  'анекдот про ...' - получить анекдот на указанную (...) тему")
        print("  'история' или 'history' - показать последние 5 диалогов")
        print("  'очистить' или 'clear' - очистить историю диалога")
        print("  'статистика' или 'stats' - показать статистику сессии")
        print("  'помощь' или 'help' - показать эту справку")
        print("  'выход' или 'exit' - завершить работу")
        print("=" * 60)
        
        print("\n ПРИМЕРЫ ЗАПРОСОВ:")
        print(" Расскажи анекдот")
        print(" Анекдот про Штирлица")
        print(" Пошути про таксистов")
        print(" Расскажи короткую смешную историю")
        print(" Анекдот про пельмени")
    
    def show_stats(self):
        print("\n" + "=" * 60)
        print(" СТАТИСТИКА СЕССИИ")
        print("=" * 60)
        print(f" Всего анекдотов рассказано: {self.request_count}")
        print(f" Сохранено сообщений в истории: {len(self.history)}")
        print(f" Используемая модель: {self.model}")
        print(f" API endpoint: {self.base_url}")
        print(f" Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def run(self):
        self.print_welcome()
        
        while True:
            try:
                user_input = input("\n Вы: ").strip()
                
                if not user_input:
                    continue

                cmd_result = self.process_command(user_input)
                if cmd_result is False:
                    break
                if cmd_result is True:
                    continue
                
                self.add_to_history("user", user_input)
                
                print("Бот: ...", end="", flush=True)
                
                joke = self.get_joke(user_input)
                
                if joke:
                    print(joke)
                    self.add_to_history("assistant", joke)
                else:
                    print("Извините, не удалось получить анекдот. Попробуйте еще раз!")
                    
            except KeyboardInterrupt:
                print("\n\n Прервано пользователем.")
                break
            except Exception as e:
                print(f"\n Неожиданная ошибка: {e}")
                print("Попробуйте перезапустить бота")
    
    def print_welcome(self):
        print("\n" + "=" * 60)
        print(" Добро пожаловать в анекдот-бота!")
        print("=" * 60)
        print(f"Модель: {self.model}")
        print(f"Храню последние {self.max_history // 2} диалогов")
        print("=" * 60)
        self.show_help()


def main():
    try:
        bot = JokeBot()
        bot.run()
    except ValueError as e:
        print(f"\n Ошибка инициализации: {e}")
        print("\n Решение:")
        print("1. Создайте файл .env в той же папке")
        print("2. Добавьте в него строку: API_KEY=...")
        print("3. Получите ключ на https://bothub.chat")
        sys.exit(1)
    except Exception as e:
        print(f"\n Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()