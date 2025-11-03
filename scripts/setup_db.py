import sqlite3
import requests
import json

# DBs by Year
DB_FILE_2526 = "sleeper_league_2526.db"
DB_FILE_2425 = "sleeper_league_2425.db"

# League ID's
LEAGUE_ID_2526 = "1253516124402757633" # Hangover Sundays 2025/2026
LEAGUE_ID_2425 = "1121122562257293312" # Hangover Sundays 2024/2025

# API URLs
SLEEPER_API_NFL_PLAYERS = "https://api.sleeper.app/v1/players/nfl"

# Connect to SQLite
db_connection = sqlite3.connect(DB_FILE_2526)

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

# Commit table creation
db_connection.commit()

# Fetch NFL player data and insert into the players table
print("Fetching player data...")
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
print(f"Inserted {len(players)} players.")

# Fetch league users and store in users table
print("Fetching league users...")
users = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID_2526}/users").json()
for user in users:
    c.execute("""
    INSERT OR REPLACE INTO users (user_id, display_name, data)
    VALUES (?, ?, ?)
    """, (user['user_id'], user['display_name'], json.dumps(user)))
db_connection.commit()
print(f"Inserted {len(users)} users.")

# Fetch league rosters and store in the rosters table
print("Fetching rosters...")
rosters = requests.get(f"https://api.sleeper.app/v1/league/{LEAGUE_ID_2526}/rosters").json()
for roster in rosters:
    c.execute("""
    INSERT OR REPLACE INTO rosters (roster_id, owner_id, league_id, players)
    VALUES (?, ?, ?, ?)
    """, (roster['roster_id'], roster['owner_id'], LEAGUE_ID_2526, json.dumps(roster['players'])))
db_connection.commit()
print(f"Inserted {len(rosters)} rosters.")

# Close connection
db_connection.close()
print("Database setup / update complete! Your SQLite DB is ready.")