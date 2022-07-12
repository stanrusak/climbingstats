# climbingstats
Climbing competition statistics based on data scraped from the IFSC website. Data from the years 2008-2022 because IFSC started reporting results in terms of tops and zones (bonuses) in 2008. So far only stats bouldering world cups are presented. Lead will be added eventually. You can see the rankings here:

https://stanrusak.github.io/climbingstats/


### Data

The data can be found in the `data` folder. `event_data.json` contains the full data of IFSC World Cup events, including boulder, lead, and speed.

```python
import pandas as pd
import json

with open('event_data.json', 'r') as f:
    events = json.load(f)   

# results for men's boulder for the first event of 2022
df = pd.read_json(events['2022'][0]["categories"]["BOULDER Men"], orient='split')
```


`men.json` and `women.json` contains corresponding overall athlete data (only boulder so far).

```python
# women's overall results for boulder 
women = pd.read_json('women.json', orient='split')
```
