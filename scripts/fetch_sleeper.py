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

def get_roster_for_team(owner_id, db_cursor):
    # Get roster info for this owner
    db_cursor.execute("SELECT roster_id, players FROM rosters WHERE owner_id = ?", (owner_id,))
    row = db_cursor.fetchone()
    if row is None:
        return None  # owner has no roster

    roster_id, players_json = row

    # Get owner name
    db_cursor.execute("SELECT display_name FROM users WHERE user_id = ?", (owner_id,))
    owner_row = db_cursor.fetchone()
    owner_name = owner_row[0] if owner_row else "Unknown"

    # Load player IDs from JSON
    player_ids = json.loads(players_json)

    # Get player info
    player_ids = json.loads(players_json)
    players_info = []

    for pid in player_ids:
        db_cursor.execute("SELECT full_name, position, team FROM players WHERE player_id = ?", (pid,))
        player_row = db_cursor.fetchone()

        if player_row:
            full_name, position, team = player_row

            # Handle defenses or missing names
            if position == "DEF" or not full_name:
                display_name = f"{team}"
            else:
                display_name = full_name

            players_info.append({
                'full_name': display_name,
                'position': position,
                'team': team
            })
        else:
            players_info.append({'full_name': 'Unknown', 'position': 'Unknown', 'team': 'Unknown'})

    return {
        'owner_name': owner_name,
        'players': players_info
    }

def main() -> None:
    # Connect to the SQLite Datbase
    db_connection = sqlite3.connect(DB_FILE)
    c = db_connection.cursor()
    
    burke_roster = get_roster_for_team(BURKE_OWNER_ID, c)
    if burke_roster:
        print(f"Owner: {burke_roster['owner_name']}")
        for p in burke_roster['players']:
            print(f"{p['full_name']} ({p['position']}) - {p['team']}")

if __name__ == "__main__":
    main()


