from parsers.edostavka_by.controller import main as edostavka_by_run
from parsers.gippo_market_by.controller import main as gippo_market_by_run
from parsers.green_dostavka_by.controller import main as green_dostavka_by_run
import schedule
import time


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        total_seconds = end_time - start_time
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)

        print(f"Время выполнения {func.__name__}: {minutes:02d}:{seconds:02d}")
        return result

    return wrapper


def start_scrapping():
    try:
        timer_decorator(edostavka_by_run())
        print('edostavka_by done...')
    except Exception as ex:
        print(ex)
    #
    try:
        timer_decorator(gippo_market_by_run())
        print('gippo_market_by done...')

    except Exception as ex:
        print(ex)
    #
    try:
        timer_decorator(green_dostavka_by_run())
        print('green_dostavka_by done...')

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    start_scrapping()
    schedule.every().day.at("01:30").do(start_scrapping)
    while True:
        schedule.run_pending()
        time.sleep(60)