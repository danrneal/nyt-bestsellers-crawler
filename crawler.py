import datetime
import json
import os
import requests
import time
from titlecase import titlecase

API_KEY = os.environ['NYT_API_KEY']
API_CALLS = []
MAX_CALLS = 10
RATE_LIMIT_PERIOD = datetime.timedelta(seconds=60)
FIRST_NYT_N1_DATE = "2008-06-07"
FIRST_NYT_ABS_DATE = "2018-03-11"


def api_call(call_url):
    while len(API_CALLS) >= MAX_CALLS:
        elapsed_time = datetime.datetime.now() - API_CALLS[0]
        if elapsed_time >= RATE_LIMIT_PERIOD:
            API_CALLS.pop(0)
        else:
            sleep_time = (RATE_LIMIT_PERIOD - elapsed_time).total_seconds()
            print(
                f'Sleeping {sleep_time} seconds to avoid being '
                f'rate-limited'
            )
            time.sleep(sleep_time)
    API_CALLS.append(datetime.datetime.now())
    return json.loads(requests.get(f"{call_url}).text)


def save_best_seller_file(best_sellers):
    with open('best_sellers.json', 'w') as outfile:
        outfile.write(json.dumps(best_sellers, sort_keys=True, indent=4))


def load_best_seller_file():
    if os.path.isfile('best_sellers.json'):
        with open('best_sellers.json') as infile:
            best_sellers = json.load(infile)
    else:
        best_sellers = {
            'number_ones': [],
            'audio_best_sellers': []
        }
    retrieve_number_ones(best_sellers)


def retrieve_number_ones(best_sellers):
    published_date = best_sellers.get(
        '_number_ones_last_updated', FIRST_NYT_N1_DATE
    )
    while published_date:
        print(f'Getting number ones from {published_date}')

        url = 'https://api.nytimes.com/svc/books/v3/lists/overview.json'
        url += f'?published_date={published_date}&api-key={API_KEY}'

        results = api_call(url)['results']

        for list_ in results['lists']:
            author = list_['books'][0]['author'].strip()
            title = titlecase(list_['books'][0]['title'].strip())

            if not any(
                number_one['author'] == author and number_one['title'] == title
                for number_one in best_sellers['number_ones']
            ):
                best_sellers['number_ones'].append({
                    'author': author,
                    'title': title,
                    'date': published_date
                })
        best_sellers['_number_ones_last_updated'] = published_date
        save_best_seller_file(best_sellers)
        published_date = results['next_published_date']
    retrieve_audio_best_sellers(best_sellers)


def retrieve_audio_best_sellers(best_sellers):
    published_date = best_sellers.get(
        '_audio_best_sellers_last_updated', FIRST_NYT_ABS_DATE
    )
    while published_date:
        print(f'Getting audio best sellers from {published_date}')
        for category in ['Fiction', 'Nonfiction']:

            url = f"https://api.nytimes.com/svc/books/v3/lists/"
            url += f"{published_date}/audio-{category}.json?api-key={API_KEY}"

            results = api_call(url)['results']

            for book in results['books']:
                author = book['author'].strip()
                title = titlecase(book['title'].strip())

                if not any(
                    audio_best_seller['author'] == author and
                    audio_best_seller['title'] == title
                    for audio_best_seller in best_sellers['audio_best_sellers']
                ):
                    best_sellers['audio_best_sellers'].append({
                        'author': author,
                        'title': title,
                        'date': published_date,
                        'category': category
                    })
        best_sellers['_audio_best_sellers_last_updated'] = published_date
        save_best_seller_file(best_sellers)
        published_date = results['next_published_date']
    create_reading_list(best_sellers)


def create_reading_list(best_sellers):
    reading_list = []
    for audio_best_seller in best_sellers['audio_best_sellers']:
        if any(
            number_one['author'] == audio_best_seller['author'] and
            number_one['title'] == audio_best_seller['title']
            for number_one in best_sellers['number_ones']
        ):
            number_one = next(
                number_one for number_one in best_sellers['number_ones']
                if number_one['author'] == audio_best_seller['author'] and
                number_one['title'] == audio_best_seller['title']
            )
            reading_list.append({
                'author': audio_best_seller['author'],
                'title': audio_best_seller['title'],
                'date': max(number_one['date'], audio_best_seller['date']),
                'category': audio_best_seller['category']
            })

    for book in reading_list:
        print(
            f"{book['author']}, {book['title']}, {book['date']}, "
            f"{book['category']}"
        )

    best_sellers['reading_list'] = reading_list
    save_best_seller_file(best_sellers)


if __name__ == '__main__':
    load_best_seller_file()
