#!/usr/bin/env python3
import requests
import sqlite3
import json

# Database information
DB_FILE = "sleeper_league.db"

# API URLs
SLEEPER_API_URL = "https://api.sleeper.app/v1/"
SLEEPER_API_LEAGUE = "https://api.sleeper.app/v1/league/"
SLEEPER_API_NFL_PLAYERS = "https://api.sleeper.app/v1/players/nfl"
LEAGUE_ID = "1253516124402757633" # Hangover Sundays

# Owner IDs for the League
DYLAN_OWNER_ID = "1121129137239953408" # StringerIHardlyKnowHer
LIAM_OWNER_ID = "1121129568196235264" # Ballesty
MILAN_OWNER_ID = "1012039696140042240" # milan00p
JEREMY_OWNER_ID = "1004192958289154048" # HoodieHarris
JACKSON_OWNER_ID = "734680732328407040" # jciordia
SEANIE_OWNER_ID = "847513622405038080" # sstelzer
GARRETT_OWNER_ID = "873713486264754176" # garretthobbs
NICKYJ_OWNER_ID = "1083904103815716864" # MrDoctorBartender
CONNOR_OWNER_ID = "1083906150413856768" # maytag34
BURKE_OWNER_ID = "1120530360045084672" # kjburke212
TAYLOR_OWNER_ID = "1121305037675941888" # twatkinz
MONTE_OWNER_ID = "1121881416008192000" # monte2424


def main() -> None:
    #league_info = requests.get(f"{SLEEPER_API_LEAGUE}{LEAGUE_ID}").json()
    #rosters = requests.get(f"{SLEEPER_API_LEAGUE}{LEAGUE_ID}/rosters").json()
    players = requests.get(f"{SLEEPER_API_NFL_PLAYERS}").json()

    print(players)

if __name__ == "__main__":
    main()


