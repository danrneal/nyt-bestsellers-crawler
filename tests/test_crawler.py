import datetime
import json
import unittest
from unittest.mock import mock_open, patch
import crawler


@patch('requests.get')
@patch('crawler.datetime')
@patch('builtins.print')
@patch('time.sleep')
class ApiCallTest(unittest.TestCase):

    def setUp(self):
        crawler.API_CALLS = []

    def test_requests_page(
        self, mock_sleep, mock_print, mock_datetime, mock_get
    ):
        mock_get.return_value.text = json.dumps({'key': 'value'})
        response = crawler.api_call('url')
        mock_sleep.assert_not_called()
        mock_print.assert_not_called()
        mock_datetime.datetime.now.assert_called_once()
        mock_get.assert_called_once_with('url')
        self.assertEqual(response, {'key': 'value'})

    def test_requests_page_when_no_need_to_rate_limit(
        self, mock_sleep, mock_print, mock_datetime, mock_get
    ):
        mock_get.return_value.text = json.dumps({'key': 'value'})
        mock_datetime.datetime.now.return_value = datetime.datetime.now()
        for call in range(crawler.MAX_CALLS):
            crawler.api_call('url')
        future = datetime.datetime.now() + crawler.RATE_LIMIT_PERIOD
        mock_datetime.datetime.now.return_value = future
        response = crawler.api_call('url')
        mock_sleep.assert_not_called()
        mock_print.assert_not_called()
        mock_datetime.datetime.now.assert_called()
        mock_get.assert_called_with('url')
        self.assertEqual(response, {'key': 'value'})

    def test_rate_limits_when_necessary(
        self, mock_sleep, mock_print, mock_datetime, mock_get
    ):
        mock_get.return_value.text = json.dumps({'key': 'value'})
        now = datetime.datetime.now()
        mock_datetime.datetime.now.return_value = now
        for call in range(crawler.MAX_CALLS):
            crawler.api_call('url')
        future = now + crawler.RATE_LIMIT_PERIOD
        mock_datetime.datetime.now.side_effect = [now, future, future]
        response = crawler.api_call('url')
        mock_sleep.assert_called_once_with(
            crawler.RATE_LIMIT_PERIOD.total_seconds()
        )
        mock_print.assert_called_once_with(
            f'Sleeping {crawler.RATE_LIMIT_PERIOD.total_seconds()} seconds to '
            f'avoid being rate-limited'
        )
        mock_datetime.datetime.now.assert_called()
        mock_get.assert_called_with('url')
        self.assertEqual(response, {'key': 'value'})


@patch('crawler.retrieve_number_ones')
@patch('os.path.isfile')
@patch(
    'builtins.open',
    new_callable=mock_open,
    read_data=json.dumps({'key': 'value'})
)
class LoadBestSellerFileTest(unittest.TestCase):

    def test_initialize_file_if_it_does_not_exits(
        self, mock_with_open, mock_isfile, mock_retrieve_number_ones
    ):
        mock_isfile.return_value = False
        crawler.load_best_seller_file()
        mock_with_open.assert_not_called()
        mock_retrieve_number_ones.assert_called_once_with({
            'number_ones': [],
            'audio_best_sellers': []
        })

    def test_loads_file_if_present(
        self, mock_with_open, mock_isfile, mock_retrieve_number_ones
    ):
        mock_isfile.return_value = True
        crawler.load_best_seller_file()
        mock_with_open.assert_called_with('best_sellers.json')
        mock_retrieve_number_ones.assert_called_once_with({'key': 'value'})


@patch('crawler.retrieve_audio_best_sellers')
@patch('crawler.api_call')
@patch('crawler.save_best_seller_file')
@patch('builtins.print')
class RetrieveNumberOnesTest(unittest.TestCase):

    def test_passes_best_sellers_dict_on(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_retrieve_audio_best_sellers
    ):
        best_sellers = {'_number_ones_last_updated': ""}
        crawler.retrieve_number_ones(best_sellers)
        mock_print.assert_not_called()
        mock_save_best_seller_file.assert_not_called()
        mock_api_call.assert_not_called()
        mock_retrieve_audio_best_sellers.assert_called_once_with(best_sellers)

    def test_gets_number_ones_until_no_published_date(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_retrieve_audio_best_sellers
    ):
        mock_api_call.return_value = {
            'results': {
                'lists': [{
                    'books': [{
                        'contributor': 'author',
                        'title': 'title'
                    }]
                }],
                'next_published_date': ""
            }
        }
        crawler.retrieve_number_ones({'number_ones': []})
        mock_print.assert_called_once_with(
            f'Getting number ones from {crawler.FIRST_NYT_N1_DATE}'
        )
        best_sellers = {
            '_number_ones_last_updated': crawler.FIRST_NYT_N1_DATE,
            'number_ones': [{
                'author': 'author',
                'title': 'Title',
                'date': crawler.FIRST_NYT_N1_DATE
            }]
        }
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_once_with(
            f'https://api.nytimes.com/svc/books/v3/lists/overview.json'
            f'?published_date={crawler.FIRST_NYT_N1_DATE}'
            f'&api-key={crawler.API_KEY}'
        )
        mock_retrieve_audio_best_sellers.assert_called_once_with(best_sellers)

    def test_processes_author_name_correctly(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_retrieve_audio_best_sellers
    ):
        mock_api_call.return_value = {
            'results': {
                'lists': [{
                    'books': [{
                        'contributor': 'by author',
                        'title': 'title'
                    }]
                }],
                'next_published_date': ""
            }
        }
        crawler.retrieve_number_ones({'number_ones': []})
        mock_print.assert_called_once_with(
            f'Getting number ones from {crawler.FIRST_NYT_N1_DATE}'
        )
        best_sellers = {
            '_number_ones_last_updated': crawler.FIRST_NYT_N1_DATE,
            'number_ones': [{
                'author': 'author',
                'title': 'Title',
                'date': crawler.FIRST_NYT_N1_DATE
            }]
        }
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_once_with(
            f'https://api.nytimes.com/svc/books/v3/lists/overview.json'
            f'?published_date={crawler.FIRST_NYT_N1_DATE}'
            f'&api-key={crawler.API_KEY}'
        )
        mock_retrieve_audio_best_sellers.assert_called_once_with(best_sellers)

    def test_ignores_duplicates(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_retrieve_audio_best_sellers
    ):
        mock_api_call.return_value = {
            'results': {
                'lists': [{
                    'books': [{
                        'contributor': 'author',
                        'title': 'title'
                    }]
                }],
                'next_published_date': ""
            }
        }
        best_sellers = {
            '_number_ones_last_updated': crawler.FIRST_NYT_N1_DATE,
            'number_ones': [{
                'author': 'author',
                'title': 'Title',
                'date': crawler.FIRST_NYT_N1_DATE
            }]
        }
        crawler.retrieve_number_ones(best_sellers)
        mock_print.assert_called_once_with(
            f'Getting number ones from {crawler.FIRST_NYT_N1_DATE}'
        )
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_once_with(
            f'https://api.nytimes.com/svc/books/v3/lists/overview.json'
            f'?published_date={crawler.FIRST_NYT_N1_DATE}'
            f'&api-key={crawler.API_KEY}'
        )
        mock_retrieve_audio_best_sellers.assert_called_once_with(best_sellers)


@patch('crawler.create_reading_list')
@patch('crawler.api_call')
@patch('crawler.save_best_seller_file')
@patch('builtins.print')
class RetrieveAudioBestSellers(unittest.TestCase):

    def test_passes_best_sellers_on(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_create_reading_list
    ):
        best_sellers = {'_audio_best_sellers_last_updated': ""}
        crawler.retrieve_audio_best_sellers(best_sellers)
        mock_print.assert_not_called()
        mock_save_best_seller_file.assert_not_called()
        mock_api_call.assert_not_called()
        mock_create_reading_list.assert_called_once_with(best_sellers)

    def test_gets_audio_best_sellers_until_no_published_date(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_create_reading_list
    ):
        mock_api_call.side_effect = [
            {
                'results': {
                    'books': [{
                        'contributor': 'author 1',
                        'title': 'title 1'
                    }],
                    'next_published_date': ""
                }
            },
            {
                'results': {
                    'books': [{
                        'contributor': 'author 2',
                        'title': 'title 2'
                    }],
                    'next_published_date': ""
                }
            }
        ]
        crawler.retrieve_audio_best_sellers({'audio_best_sellers': []})
        mock_print.assert_called_once_with(
            f'Getting audio best sellers from {crawler.FIRST_NYT_ABS_DATE}'
        )
        best_sellers = {
            '_audio_best_sellers_last_updated': crawler.FIRST_NYT_ABS_DATE,
            'audio_best_sellers': [
                {
                    'author': 'author 1',
                    'title': 'Title 1',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Fiction'
                },
                {
                    'author': 'author 2',
                    'title': 'Title 2',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Nonfiction'
                },
            ]
        }
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_with(
            f'https://api.nytimes.com/svc/books/v3/lists/'
            f'{crawler.FIRST_NYT_ABS_DATE}/audio-Nonfiction.json'
            f'?api-key={crawler.API_KEY}'
        )
        mock_create_reading_list.assert_called_once_with(best_sellers)

    def test_processes_author_name_correctly(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_create_reading_list
    ):
        mock_api_call.side_effect = [
            {
                'results': {
                    'books': [{
                        'contributor': 'by author 1',
                        'title': 'title 1'
                    }],
                    'next_published_date': ""
                }
            },
            {
                'results': {
                    'books': [{
                        'contributor': 'by author 2',
                        'title': 'title 2'
                    }],
                    'next_published_date': ""
                }
            }
        ]
        crawler.retrieve_audio_best_sellers({'audio_best_sellers': []})
        mock_print.assert_called_once_with(
            f'Getting audio best sellers from {crawler.FIRST_NYT_ABS_DATE}'
        )
        best_sellers = {
            '_audio_best_sellers_last_updated': crawler.FIRST_NYT_ABS_DATE,
            'audio_best_sellers': [
                {
                    'author': 'author 1',
                    'title': 'Title 1',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Fiction'
                },
                {
                    'author': 'author 2',
                    'title': 'Title 2',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Nonfiction'
                },
            ]
        }
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_with(
            f'https://api.nytimes.com/svc/books/v3/lists/'
            f'{crawler.FIRST_NYT_ABS_DATE}/audio-Nonfiction.json'
            f'?api-key={crawler.API_KEY}'
        )
        mock_create_reading_list.assert_called_once_with(best_sellers)

    def test_ignores_duplicates(
        self, mock_print, mock_save_best_seller_file, mock_api_call,
        mock_create_reading_list
    ):
        mock_api_call.side_effect = [
            {
                'results': {
                    'books': [{
                        'contributor': 'author 1',
                        'title': 'title 1'
                    }],
                    'next_published_date': ""
                }
            },
            {
                'results': {
                    'books': [{
                        'contributor': 'author 2',
                        'title': 'title 2'
                    }],
                    'next_published_date': ""
                }
            }
        ]
        best_sellers = {
            '_audio_best_sellers_last_updated': crawler.FIRST_NYT_ABS_DATE,
            'audio_best_sellers': [
                {
                    'author': 'author 1',
                    'title': 'Title 1',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Fiction'
                },
                {
                    'author': 'author 2',
                    'title': 'Title 2',
                    'date': crawler.FIRST_NYT_ABS_DATE,
                    'category': 'Nonfiction'
                },
            ]
        }
        crawler.retrieve_audio_best_sellers(best_sellers)
        mock_print.assert_called_once_with(
            f'Getting audio best sellers from {crawler.FIRST_NYT_ABS_DATE}'
        )
        mock_save_best_seller_file.assert_called_once_with(best_sellers)
        mock_api_call.assert_called_with(
            f'https://api.nytimes.com/svc/books/v3/lists/'
            f'{crawler.FIRST_NYT_ABS_DATE}/audio-Nonfiction.json'
            f'?api-key={crawler.API_KEY}'
        )
        mock_create_reading_list.assert_called_once_with(best_sellers)


@patch('crawler.save_best_seller_file')
@patch('builtins.print')
class CreateReadingListTest(unittest.TestCase):

    def test_reading_list_is_saved(
        self, mock_print, mock_save_best_seller_file
    ):
        best_sellers = {
            'audio_best_sellers': [{
                'author': 'author 1',
                'title': 'Title 1'
            }],
            'number_ones': [{
                'author': 'author 2',
                'title': 'Title 2'
            }]
        }
        crawler.create_reading_list(best_sellers)
        mock_print.assert_not_called()
        best_sellers['reading_list'] = []
        mock_save_best_seller_file.assert_called_once_with(best_sellers)

    def test_reading_list_is_created(
        self, mock_print, mock_save_best_seller_file
    ):
        best_sellers = {
            'audio_best_sellers': [{
                'author': 'author',
                'title': 'Title',
                'date': '2008-06-07',
                'category': 'Fiction'
            }],
            'number_ones': [{
                'author': 'author',
                'title': 'Title',
                'date': '2018-03-11'
            }]
        }
        crawler.create_reading_list(best_sellers)
        mock_print.assert_called_once_with('author, Title, 2018-03-11, Fiction')
        best_sellers['reading_list'] = [{
            'author': 'author',
            'title': 'Title',
            'date': '2018-03-11',
            'category': 'Fiction'

        }]
        mock_save_best_seller_file.assert_called_once_with(best_sellers)


if __name__ == '__main__':
    unittest.main()
