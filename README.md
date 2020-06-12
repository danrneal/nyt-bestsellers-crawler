# NYT Bestsellers Crawler

A script that uses the New York Times API to get all number one bestsellers (on any of their lists) that are also on their audiobook bestsellers lists.

## Set-up

Set-up a virtual environment and activate it:

```bash
python3 -m venv env
source env/bin/activate
```

You should see (env) before your command prompt now. (You can type `deactivate` to exit the virtual environment any time.)

Install the requirements:

```bash
pip install -U pip
pip install -r requirements.txt
```

Obtain a NYT API key [here](https://developer.nytimes.com/get-started).

Set up your environment variables:

```bash
touch .env
echo NYT_API_KEY="XXX" >> .env
```

## Usage

Make sure you are in the virtual environment (you should see (env) before your command prompt). If not `source /env/bin/activate` to enter it.

Make sure .env variables are set:

```bash
set -a; source .env; set +a
```

Then run the script:

```bash
Usage: crawler.py
```

## Testing Suite

This repository contains a test suite consisting of unit tests.

### Unit Tests

These test the program from the inside, from developer's point of view. You can run them with the following command:

```bash
python3 -m unittest discover tests
```

### A comment on TDD

This project was done following Test-Driven Development principles where the starting point is a failing test. My process was to write a unit test to define how I wanted to the code to behave. That is the point where I wrote the "actual" code to get the unit tests to pass.

While this may seem unnecessary for a program of such a small size and may seem like overdoing, TDD principles help to create quality, maintainable code and as such I believe are good habits to foster even on a small project such as this.

## License

NYT Bestsellers Crawler is licensed under the [MIT license](https://github.com/danrneal/nyt-bestsellers-crawler/blob/master/LICENSE).
