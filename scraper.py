import requests, json, sys

class Scraper:

    API_BASE_URL = "https://components.ifsc-climbing.org/results-api.php?api="

    headers = {
    'authority': 'components.ifsc-climbing.org',
    'accept': '*/*',
    'accept-language': 'en,en-US;q=0.9,sv-SE;q=0.8,sv;q=0.7,fi;q=0.6,ru;q=0.5',
    'cookie': 'OptanonAlertBoxClosed=2022-06-11T12:13:56.319Z; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Jul+07+2022+04%3A24%3A43+GMT%2B0200+(Central+European+Summer+Time)&version=6.20.0&isIABGlobal=false&consentId=04f2b45f-8dc3-41e4-a7d0-5a7e16f98626&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A0%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0&hosts=H7%3A0%2CH1%3A0%2CH2%3A0%2CH13%3A0%2CH11%3A0%2CH14%3A0%2CH9%3A0%2CH3%3A0%2CH4%3A0%2CH10%3A0%2CH12%3A0%2CH5%3A0&genVendors=V5%3A0%2C&geolocation=US%3BVA&AwaitingReconsent=false',
    'dnt': '1',
    'referer': 'https://components.ifsc-climbing.org/results/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
    }

    def __init__(self):

        self.data = None

    def get_data(self, period='all') -> None:

        season_info_url = self.API_BASE_URL + 'index'
        seasons = requests.get(season_info_url, headers=self.headers).json()['seasons']
        seasons = {int(season['name']): season for season in seasons}
        
        if period == 'all':
            years = list(seasons.keys())
        elif isinstance(period, int):
            years = [period]
        elif len(period) == 2:
            years = reversed(range(min(period), max(period)+1))
        elif isinstance(period, list) or isinstance(period, tuple):
            years = period
        else:
            raise ValueError(f"Invalid parameter value {period}")
        
        print("Scraping data...\n")
        
        for year in years:
            
            print(f"{year}:")
            season = seasons[year]
            season_id = season['id']
            league_id = season['leagues'][0]['id'] # pick only World Cup and World Champ data
            season['leagues'] = 'World Cups and World Championships'
            season['events'] = self.get_season_data(league_id)
        
        self.data = seasons

    def get_season_data(self, league_id: int) -> dict:

        print(f"Scraping...")

        # request event data
        league_info_url = f"{self.API_BASE_URL}season_leagues_results&league={league_id}"
        events = requests.get(league_info_url).json()['events']
        
        # get data for each event in season
        event_list = []
        for event in events:

            event_id = event['url'].split('/')[-1]

            try:
                print(f" {event['event']}")
                event_data = self.get_event_data(event_id)
            except:
                print(f" Could not scrape {event['event']}")
                continue

            event_list.append(event_data)
        
        # append to the season as dict
        event_dict = {}
        locations = [self.get_location(event) for event in event_list]
        counts = dict.fromkeys(locations, 0)
        for event in event_list:

            location = self.get_location(event)

            # check for repeated events in the same location and number them
            if locations.count(location) > 1:
                counts[location] += 1
                location += ' ' + str(counts[location])

            event_dict[location] =  event
        
        return event_dict

    def get_event_data(self, event_id: int) -> dict:
        
        # request category data
        event_info_url = f"{self.API_BASE_URL}event_results&event_id={event_id}"
        event = requests.get(event_info_url, headers=self.headers).json()
        
        # scrape data for each category in event
        event['categories'] = []
        event['results'] = {}
        for category in event['d_cats']:

            category_name = category['dcat_name']
            event['categories'].append(category_name)
            print(f"  {category_name}")
            discipline_id = int(category['full_results_url'].split('/')[-1])
            category_results_url = f"{self.API_BASE_URL}event_full_results&result_url=/api/v1/events/{event_id}/result/{discipline_id}"
            category_results = requests.get(category_results_url, headers=self.headers).json()
            event['results'][category_name] = category_results['ranking']

        del event['d_cats']
        return event

    def get_location(self, event: dict) -> str:
        return ' '.join(event['name'].split('-')[-1].strip().split()[:-2])

    def to_json(self, filename: str='data.json') -> None:

        if not self.data:
            print("No data. Run the get_data(period) method to scrape data.")
            return 
        
        print(f"Saving data to {filename}...")
        with open(filename, 'w+') as f:
            json.dump(self.data, f, indent=4)
        print("Done!")

def usage() -> None:

    print("Usage: 'python scraper.py' to scrape all data.\n       'python scraper.py -p <year>' to scraper a single season.\n       'python scraper.py -p <start_year> <end_year>' to scrape a range of years.")

def main() -> None:

    argv = sys.argv[1:]
    period = 'all'

    if argv:

        if not argv[0][:2] == "-p":
            usage()
            return

        if len(argv) == 2:
            period = int(argv[1])
        elif len(argv) == 3:
            period = [int(year) for year in argv[1:]]
        else:
            usage()
            return

    scraper = Scraper()
    scraper.get_data(period)
    scraper.to_json()

if __name__ == '__main__':

    main()