#!/usr/bin/env python3
import requests
import sqlite3
import json

import utl
import setup_db
import win_probability
import all_play_standings
import team_consistency


def main() -> None:
    # Connect to the SQLite Datbase
    db_connection = sqlite3.connect(utl.DB_FILE_25)
    c = db_connection.cursor()

    setup_db.main()
    win_probability.main()
    all_play_standings.main()
    team_consistency.main()

if __name__ == "__main__":
    main()


