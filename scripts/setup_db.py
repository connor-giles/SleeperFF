import sqlite3
import requests
import json

# DBs by Year
DB_FILE_25 = "sleeper_league_25.db"
DB_FILE_24 = "sleeper_league_24.db"

# League ID's
LEAGUE_ID_25 = "1253516124402757633" # Hangover Sundays 2025/2026
LEAGUE_ID_24 = "1121122562257293312" # Hangover Sundays 2024/2025

# API URLs
SLEEPER_API_NFL_PLAYERS = "https://api.sleeper.app/v1/players/nfl"

def main():
    # Connect to SQLite
    db_connection = sqlite3.connect(DB_FILE_25)

    # Allows interaction with the db
    c = db_connection.cursor()

    # Create NFL players table
    c.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        full_name TEXT,
        team TEXT,
        position TEXT,
        data JSON
    )
    """)

    # Create league users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        data JSON
    )
    """)

    # Create league rosters table
    c.execute("""
    CREATE TABLE IF NOT EXISTS rosters (
        roster_id INTEGER PRIMARY KEY,
        owner_id TEXT,
        league_id TEXT,
        players JSON,
        FOREIGN KEY(owner_id) REFERENCES users(user_id)
    )
    """)

    # Creates / updates the matchups table
    c.execute("""
    CREATE TABLE IF NOT EXISTS matchups (
        matchup_id TEXT PRIMARY KEY,
        week INTEGER,
        roster_id INTEGER,
        points REAL,
        starters JSON,
        players_points JSON,
        matchup_id_group INTEGER,
        FOREIGN KEY(roster_id) REFERENCES rosters(roster_id)
    )
    """)

    # Commit table creation
    db_connection.commit()

    # Fetch NFL player data and insert into the players table
    print("Fetching NFL player data...")
    players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    for pid, pdata in players.items():
        full_name = pdata.get('full_name', 'Unknown')
        team = pdata.get('team', '')
        position = pdata.get('position', '')
        c.execute("""
        INSERT OR REPLACE INTO players (player_id, full_name, team, position, data)
        VALUES (?, ?, ?, ?, ?)
        """, (pid, full_name, team, position, json.dumps(pdata)))
    db_connection.commit()
    print(f"Inserted {len(players)} NFL players.\n")

    # Fetch league users and store in users table
    print("Fetching Sleeper users...")
    users = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID_25}/users").json()
    for user in users:
        c.execute("""
        INSERT OR REPLACE INTO users (user_id, display_name, data)
        VALUES (?, ?, ?)
        """, (user['user_id'], user['display_name'], json.dumps(user)))
    db_connection.commit()
    print(f"Inserted {len(users)} users for Hangover Sundays.\n")

    # Fetch league rosters and store in the rosters table
    print("Fetching league rosters...")
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID_25}/rosters").json()
    for roster in rosters:
        c.execute("""
        INSERT OR REPLACE INTO rosters (roster_id, owner_id, league_id, players)
        VALUES (?, ?, ?, ?)
        """, (roster['roster_id'], roster['owner_id'], LEAGUE_ID_25, json.dumps(roster['players'])))
    db_connection.commit()
    print(f"Inserted {len(rosters)} rosters.\n")

    # Fetch matchups for each week of the year
    print("Fetching league matchups by week...")
    for week in range(1, 18):  # Regular season weeks
        matchups = requests.get(
            f"https://api.sleeper.app/v1/league/{LEAGUE_ID_25}/matchups/{week}"
        ).json()
        
        if matchups:
            for matchup in matchups:
                matchup_id = f"{LEAGUE_ID_25}_{week}_{matchup['roster_id']}"
                c.execute("""
                INSERT OR REPLACE INTO matchups 
                (matchup_id, week, roster_id, points, starters, players_points, matchup_id_group)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    matchup_id,
                    week,
                    matchup['roster_id'],
                    matchup.get('points', 0),
                    json.dumps(matchup.get('starters', [])),
                    json.dumps(matchup.get('players_points', {})),
                    matchup.get('matchup_id')
                ))
            db_connection.commit()
            print(f"Inserted week {week} matchups.")

    # Close connection
    db_connection.close()
    print("Database setup / update complete! Your SQLite DB is ready.")