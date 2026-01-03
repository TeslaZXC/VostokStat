import time
from logic.download_mission import main

if __name__ == "__main__":
    print("=== Инициализация миссий ===")
    main(mode="init")

    while True:
        try:
            print("=== Поиск новых миссий (последние 2 дня) ===")
            main(mode="update")
        except Exception as e:
            print(f"Ошибка: {e}")
        print("Перезапуск через 10 секунд...")
        time.sleep(10)
