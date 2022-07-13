import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

from IPython.display import display, HTML
from tqdm.notebook import tqdm

import json
import plotly.express as px

# colors
ifsc_pink = "#e6007e"
ifsc_pink_dark = "#d6006e"
ifsc_blue = "#10bbef"
ifsc_blue_dark = "#10aaef"

# layput tamplate
template = {'margin': dict(l=20, r=20, t=20, b=20)}

class Event:
    """ Object storing event data."""

    def boulder_results(self):
        
        result = {}
        for sex in ["Men", "Women"]:
            
            discipline = self.results["BOULDER " + sex]
            
            stages = {}
            for stage in ["Qualification", "Semi-final", "Final"]:
                if stage not in discipline:
                    continue
                boulders = discipline[stage].apply(lambda x: Athlete.parse_tops(x, none_to_zeros=False)).dropna().to_list()
                boulders = pd.DataFrame(boulders, columns=["tops","zones", "top_attempts","zone_attempts"], index=discipline.name[:len(boulders)])
                stages[stage] = boulders
            
            result[sex] = stages
        
        return result
    
    @staticmethod
    def from_dict(event_dict: dict):
        
        event = Event()
        for key in list(event_dict.keys())[:-1]:
            event.__dict__[key] = event_dict[key]
        
        event.results = {}
        for category in event.categories:
            
            if 'BOULDER' in category:
                event.results[category] = Event._parse_boulder_scores(event_dict['results'][category])
        
        return event
    
    @staticmethod
    def _count_flashes(ascents: dict) -> int:
        
        if ascents is np.nan:
            return 0
        
        ascents = pd.json_normalize(ascents)
        return sum((ascents.top == True) & (ascents.top_tries == 1))
    
    @staticmethod
    def _parse_rounds(rounds: dict, round_num=3) -> list:
        
        rounds  = pd.json_normalize(rounds)
        flashes = rounds.ascents.apply(Event._count_flashes)
        flashes = str(flashes.to_list())[1:-1].replace(',','')
        scores = rounds["score"].to_list()
        scores += [None] * (round_num - len(scores))
        starting_group = rounds.loc[0,"starting_group"][-1]  if "starting_group" in rounds.columns else ' '
        
        return scores + [flashes, starting_group]
    
    @staticmethod
    def _parse_boulder_scores(rankings: dict) -> pd.DataFrame:
        
        df = pd.json_normalize(rankings)
        df["name"] = (df["firstname"] + ' ' +  df["lastname"]).str.title()

        round_names = [entry["round_name"].capitalize() for entry in df.loc[0,"rounds"]]
        scores = pd.DataFrame(df.rounds.apply(lambda x: Event._parse_rounds(x, len(round_names))).to_list(), columns=round_names+["flashes", "starting_group"])
        return pd.concat([df[["rank","name","athlete_id", "country"]], scores], axis=1)
    
    @staticmethod
    def _get_ranking(results):
    
        results = results["rank"].dropna().astype(int)
        counts = results.value_counts().sort_index().to_dict()
        return results.apply(lambda place: Event._calculate_ranking(place, counts))
    
    @staticmethod
    def _calculate_ranking(place, counts):

        count = counts[place]
        return np.floor(100*sum(Athlete.RANKING[place:place+count])/count)/100
    
class Athlete:
    """ Object storing athlete data."""
    
    RANKING = [None, 1000, 805, 690, 610, 545, 495, 455, 415, 380, 350, 325, 300, 280, 260, 240, 220, 205, 185, 170, 155, 145, 130, 120, 105, 95, 84, 73, 63, 56, 48, 42, 37, 33, 30, 27, 24, 21, 19, 17, 15, 14, 13, 12, 11, 11, 10, 9, 9, 8, 8, 7, 7, 7, 6, 6, 6, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
    
    def __init__(self, name, sex, country, ifsc_id):
        
        self.name = name
        self.sex = sex[0].capitalize()
        self.country = country
        self.id = ifsc_id
        self.height = np.nan
        
        self.events = {"BOULDER": 0, "LEAD": 0}
        self._ranking_points = {"BOULDER": 0, "LEAD": 0}
        
        self._gold = {"BOULDER": 0, "LEAD": 0}
        self._silver = {"BOULDER": 0, "LEAD": 0}
        self._bronze = {"BOULDER": 0, "LEAD": 0}
        
        self._semis_B = 0
        self._finals_B = 0

        self._top_array = np.zeros(4, dtype=np.int64)
        self._rounds_B = 0
        self._boulders_attempted = 0
        
        self._maxtops = 0
        self._maxzones = 0
        
    def __repr__(self):
        
        printout = self.name + '\n' + str(self._ranking_points)
        printout += f'  Boulder: {self._gold["BOULDER"]} gold, {self._silver["BOULDER"]} silver, {self._bronze["BOULDER"]} bronze'
        
        return printout
    
    @property
    def url(self):
        return f"https://www.ifsc-climbing.org/index.php?option=com_ifsc&task=athlete.display&id={self.id}"

    def _update_boulder(self, entry):
        
        self.events["BOULDER"] += 1
        
        if entry["rank"] == 1:
            self._gold["BOULDER"] += 1
        elif entry["rank"] == 2:
            self._silver["BOULDER"] += 1
        elif entry["rank"] == 3:
            self._bronze["BOULDER"] += 1
        
        self._ranking_points["BOULDER"] += entry['points']
        
        score = np.zeros(4, dtype=np.int32)
        i = entry.index.get_loc("country") + 1
        for stage in entry.index[i:-3]:
            
            if entry[stage]:
                
                self._rounds_B += 1
                if stage == "Semi-final":
                    self._semis_B += 1
                elif stage == "Final" :
                    self._finals_B += 1
                self._boulders_attempted += 5 if stage == "Qualification" else 4

            score += Athlete.parse_tops(entry[stage])
            
        self._top_array += score
    
    def datarow(self):

        return pd.DataFrame({
            "name": [self.name],
            "country": [self.country],
            "id": [self.id],
            "height": [self.height],
            "ranking_B": [self._ranking_points["BOULDER"]],
            "events_B": [self.events["BOULDER"]],
            "rounds_B": [self._rounds_B],
            "semis_B": [self._semis_B],
            "finals_B": [self._finals_B],
            "gold_B":[self._gold["BOULDER"]],
            "silver_B": [self._silver["BOULDER"]],
            "bronze_B": [self._bronze["BOULDER"]],
            "tops": [self._top_array[0]],
            "zones": [self._top_array[1]],
            "top_attempts": [self._top_array[2]],
            "zone_attempts": [self._top_array[3]],
            "boulders_attempted": [self._boulders_attempted],
        })
    
    @property
    def data(self):
        return self.datarow()

    @staticmethod
    def parse_tops(item, none_to_zeros=True):
        
        if item is np.nan or item is None or item == "DNS":
            return np.zeros(4,dtype=np.int32) if none_to_zeros else None
        
        score = item.split()
        
        if len(score) == 3:
            
            tops = int(score[0][0])
            zones = int(score[0][2])
            top_attempts = int(score[1])
            zone_attempts = int(score[2])
            
        elif len(score) == 2:
            tops, zones = score
            tops, top_attempts = tops.split('t')
            zones, zone_attempts = zones.split('b')
            tops, zones = int(tops), int(zones)
            top_attempts = int(top_attempts) if top_attempts else 0
            zone_attempts = int(zone_attempts) if zone_attempts else 0
        else:
            raise ValueError(f"Unrecognizable score {item}")
        
        return np.array([tops, zones, top_attempts, zone_attempts])
  
class EventDict(dict):
    """ Dictionary storing event objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_athlete_data(self, years='all', heights=True):
        
        if years == 'all':
            years = self.keys()
        elif isinstance(years, int):
            years = [years]
        athletes = AthleteDict()
        
        for year in years:
            
            events = self[year]
            for event in events:

                categories = event.results.keys()
                for category in categories:
                    
                    discipline, sex = category.split()
                    if isinstance(event.results[category], str):
                        continue
                        
                    results = event.results[category]
                    results["points"] = Event._get_ranking(results)
                    for athlete in results.iloc:
                        
                        name = athlete["name"]
                        if name not in athletes:
                            athletes[name] = Athlete(name, sex, athlete["country"], athlete["athlete_id"])
                        
                        if discipline == "BOULDER":
                            athletes[name]._update_boulder(athlete)
        
        if heights:
            athletes.get_heights()
        
        return athletes
        
    @staticmethod
    def read_json(filename, period='all', printout=False, progress=True):

        result = EventDict()
        
        if printout:
            print("Importing data...")
        
        with open(filename, 'r') as f:
            data = json.load(f)
            EventDict.normalize_data(data)
        
        if printout:
            print("Processing...")
        
        if period == 'all':
            years = [int(year) for year in data.keys()]
        elif isinstance(period, int):
            progress = False
            years = [period]
        elif len(period) == 2:
            years = reversed(range(min(period), max(period)+1))
        else:
            raise ValueError(f"Unsupported value {period} for period.")
        
        if progress:
            years = list(years)
            pbar = tqdm(range(len(years)))
        for year in years:
            
            if printout:
                print(f"  {year}")
            
            result[year] = []
            for event in data[str(year)]['events'].values():
                
                if printout:
                    print(f"    {event['name']}")
                result[year].append(Event.from_dict(event))
        
            if progress:
                pbar.update(1)

        return result

    @staticmethod
    def normalize_data(data):
        """ 
        API returns different structure of data for different years. This function standardizes some of the inconsistencies.
             - Prior to 2020 boulder results had 'speed_elimination_stages' dict inside which boulder ascent data was. From 2020 there is just an 'ascents' dict,
        """
    
        for year, season_data in data.items():
            for event, event_data in season_data['events'].items():    
                for category, rankings in event_data['results'].items():
                    if 'BOULDER' in category:

                        for athlete_data in rankings:
                            for round_data in athlete_data['rounds']:

                                if 'speed_elimination_stages' in round_data:

                                    try:
                                        if round_data['speed_elimination_stages'] != []:
                                            round_data['ascents'] = round_data['speed_elimination_stages']['ascents']
                                        del round_data['speed_elimination_stages']
                                    except Exception as e:
                                        print(year, event, category)
                                        print(round_data)
                                        raise Exception(e)


class AthleteDict(dict):
    """ Dictionary storing athlete objects."""

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @staticmethod
    def from_list(athlete_list):
        
        if not isinstance(athlete_list[0], Athlete):
            raise Exception("Input must be a list of Athlete objects")
        
        result = AthleteDict()
        for athlete in athlete_list:
            
            result[athlete.name] = athlete
        
        return result
        
    def get_sex(self, sex='All'):
        """ Separate by sex """
        
        men = []
        women = []
        
        for athlete in self.values():
            if athlete.sex == 'M':
                men.append(athlete)
            elif athlete.sex == "W":
                women.append(athlete)
            else:
                raise Exception(f"Unrecognized sex {athlete.sex}")
        
        men = AthleteDict.from_list(men)
        women = AthleteDict.from_list(women)
        
        result = {"Men": men, "Women": women}
        
        s = sex.capitalize()
        if s == "All":
            return result
        elif s == "M" or s == "Men":
            return result["Men"]
        elif s == "W" or s == "Women":
            return result["Women"]
        else:
            raise Exception(f"Unknown sex {sex}")
    
    def get_stats(self, sex):
    
        athletes = self.get_sex()[sex]
        
        df = pd.DataFrame()
        for athlete in athletes.values():
            df = pd.concat([df,athlete.datarow()], ignore_index=True)
        
        df["top_percentage"] = df["tops"]/df["boulders_attempted"]
        df["ranking_per_event_B"] = df["ranking_B"]/df["events_B"]
        
        if all(df["height"].isna()):
            df.drop(columns="height", inplace=True)
        
        return df.sort_values("ranking_B", ascending=False).reset_index(drop=True)
    
    def get_heights(self, filename='data/heights.json'):

        heights = pd.read_json(filename, orient='split')

        for name, athlete in self.items():

            if any(heights["name"].str.contains(name, regex=False)):
                row = heights[heights.name.str.contains(name)].iloc[0]
                athlete.age = row.age
                athlete.height = row.height
            else:
                athlete.height = np.nan

def get_event_data(filename='/data/full_data.json', period=(2008,2022)):

    return EventDict.read_json('normalized.json', period=(2008,2022))


def get_yearly_data(events, period, elite_cutoff=10):
    
    start, end = period
    years = [year for year in range(start,end+1)]
    top_data = pd.DataFrame({"year": years})
    avg_top_perc, elite_top_perc = {"men": [], "women": []}, {"men": [], "women": []}
    
    for year in years:
        
        athletes = events.get_athlete_data(year)
        
        for sex in ["Men", "Women"]:
            
            stats = athletes.get_stats(sex)
            avg_top_perc[sex.lower()].append(stats["top_percentage"].mean())
            elite_top_perc[sex.lower()].append(stats["top_percentage"].sort_values(ascending=False).head(elite_cutoff).mean())
    
    
    for sex in ["men", "women"]:

        top_data[sex+"_avg_top_percentage"] = avg_top_perc[sex]
        top_data[sex+"_elite_top_percentage"] = elite_top_perc[sex]

    return top_data

