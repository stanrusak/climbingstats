# climbingstats
Climbing competition statistics based on data scraped from the IFSC website. Data from the years 2008-2023 because IFSC started reporting results in terms of tops and zones (bonuses) in 2008. So far only stats bouldering world cups and champs are presented. Lead will be added eventually. You can see the rankings here:

https://stanrusak.github.io/climbingstats/

### Data

The data can be found in the `data` folder. `full_data.zip` contains the full data of IFSC World Cup/World Champs events, including boulder, lead, and speed (in JSON format).

`men_2008-2023.csv` and `women_2008-2023.csv` contain corresponding athlete data. `climbingstats.py` has some helpful data structures for events and athletes. See the [Jupyter notebook](https://github.com/stanrusak/climbingstats/blob/main/bouldering.ipynb) for usage. 
