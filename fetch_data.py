import enum
import logging
import re
import random
import time
import requests
from datetime import date, datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)

class Station(enum.Enum):
    LONDON = 7015400
    PARIS = 8727100
    BRUXELLES = 8814001
    AMSTERDAM = 8400058


def find_api_key(eurostar_html_page: str) -> str:
    m = re.search(r'\\u0022apikey\\u0022:\\u0022(.*?)\\u0022', eurostar_html_page)
    return m.group(1)


def initialise():
    """ Initialise the session and retrieve the apikey """
    now_date = datetime.now().date().isoformat()
    base_url = 'https://booking.eurostar.com/uk-en/train-search?origin=7015400&destination=8727100&adult=1'
    init_url = base_url + f'&outbound-date={now_date}&inbound-date={now_date}'
    session = requests.Session()
    logging.info(f'Initiating Session - Get {init_url}')
    init_html = session.get(init_url).text
    apikey = find_api_key(eurostar_html_page=init_html)
    logging.info(f'API key extracted - x-apikey: {apikey}')
    return (session, apikey)


def fetch_prices(session: requests.Session, apikey: str, 
                 orig: Station, dest: Station, 
                 out_date: date, in_date: date = None) -> requests.Response:
    """ Return the response from the Eurostar price API for a given trip """
    # Build API query
    api_base = 'https://api.prod.eurostar.com/bpa/koa/train-search/uk-en'
    api = f'{api_base}/{orig.value}/{dest.value}'
    api += f'?outbound-date={out_date.isoformat()}'
    if in_date:
        api += f'&inbound-date={in_date.isoformat()}'
    api += f'&adult=1&booking-type=standard'

    logging.info(f'Query - Get {api}')
    result = session.get(api, headers={'x-apikey': apikey})
    return result


def build_dataset(data_dir: Path, origin: Station, destination:Station, days_ahead: int):
    # Initialise
    session, apikey = initialise()
    today = datetime.now().date()
    orig = origin
    dest = destination

    # Loop through dates
    for i in range(days_ahead):
        date_trip = today + timedelta(days=i)
        ## Same but single tickets
        # Fetch Data
        results = fetch_prices(
            session=session, apikey=apikey, 
            orig=orig, dest=dest, 
            out_date=date_trip
            )

        # Output Data
        filename = f'{today.strftime("%y%m%d")}_{orig.name}_{dest.name}'
        filename += f'_{date_trip.strftime("%y%m%d")}.json'
        output_file = data_dir / filename
        logging.info(f'Writing results to {output_file}')
        with open(output_file, 'w') as file_out:
            file_out.write(results.text)
        
        # Wait between 1 and 3 seconds (to avoid sending too many requests to the API)
        time.sleep(random.randint(1, 3))


if __name__ == "__main__":
    build_dataset(Path('data/data_raw/'), origin=Station.LONDON, destination=Station.PARIS, days_ahead=2)
    build_dataset(Path('data/data_raw/'), origin=Station.PARIS, destination=Station.LONDON, days_ahead=2)