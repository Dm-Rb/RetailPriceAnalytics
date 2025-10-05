from parsers.edostavka_by.controller import main as edostavka_by_run
from parsers.gippo_market_by.controller import main as gippo_market_by_run

import schedule
import time


def start_scrapping():
    try:
        edostavka_by_run()
    except Exception as ex:
        print(ex)
    #
    try:
        gippo_market_by_run()
    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    schedule.every().day.at("01:30").do(start_scrapping)
    while True:
        schedule.run_pending()
        time.sleep(60)

