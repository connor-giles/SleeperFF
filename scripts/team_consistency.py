#!/usr/bin/env python3
import sqlite3
from collections import defaultdict
import statistics
from rich.console import Console
from rich.table import Table
import utl

DB_FILE = utl.DB_FILE_25

def get_weekly_scores(db_file):
    """Get weekly points for each team"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute("""
        SELECT r.owner_id, u.display_name, m.week, m.points
        FROM matchups m
        JOIN rosters r ON m.roster_id = r.roster_id
        JOIN users u ON r.owner_id = u.user_id
        WHERE m.points > 0
        ORDER BY m.week
    """)

    weekly_scores = defaultdict(list)  # {owner_id: [points,...]}
    team_names = {}

    for owner_id, name, week, points in c.fetchall():
        weekly_scores[owner_id].append(points)
        team_names[owner_id] = name

    conn.close()
    return weekly_scores, team_names

def get_actual_records(db_file):
    """Get actual win-loss records"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute("""
        SELECT m1.week, 
               r1.owner_id, m1.points,
               r2.owner_id, m2.points
        FROM matchups m1
        JOIN matchups m2 ON m1.matchup_id_group = m2.matchup_id_group 
            AND m1.week = m2.week 
            AND m1.roster_id < m2.roster_id
        JOIN rosters r1 ON m1.roster_id = r1.roster_id
        JOIN rosters r2 ON m2.roster_id = r2.roster_id
        WHERE m1.points > 0
    """)

    actual_records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0})

    for week, owner1, points1, owner2, points2 in c.fetchall():
        if points1 > points2:
            actual_records[owner1]['wins'] += 1
            actual_records[owner2]['losses'] += 1
        elif points2 > points1:
            actual_records[owner2]['wins'] += 1
            actual_records[owner1]['losses'] += 1
        else:
            actual_records[owner1]['ties'] += 1
            actual_records[owner2]['ties'] += 1

    conn.close()
    return actual_records

def calculate_consistency(weekly_scores):
    """Calculate team consistency (stddev / mean points)"""
    consistency_data = []

    for owner_id, points in weekly_scores.items():
        if len(points) > 1:
            mean_points = statistics.mean(points)
            stdev_points = statistics.stdev(points)
            consistency = stdev_points / mean_points
        else:
            consistency = 0  # Only one week
        consistency_data.append({
            'owner_id': owner_id,
            'consistency': consistency
        })

    # Sort from most consistent (lowest) to least consistent (highest)
    consistency_data.sort(key=lambda x: x['consistency'])
    return consistency_data

def print_consistency_table(weekly_scores, actual_records, team_names):
    """Print a Rich table showing team consistency"""
    console = Console()
    consistency_data = calculate_consistency(weekly_scores)

    table = Table(title="Team Consistency Rankings", show_header=True, header_style="bold magenta")
    table.add_column("Rank", justify="center")
    table.add_column("Team", style="cyan")
    table.add_column("Actual Record", justify="center")
    table.add_column("Consistency", justify="center")

    for rank, team in enumerate(consistency_data, 1):
        owner_id = team['owner_id']
        consistency = team['consistency']

        # Color-code: low consistency = green, high = red
        if consistency < 0.05:
            style = "bold green"
        elif consistency < 0.1:
            style = "green"
        elif consistency < 0.2:
            style = "yellow"
        else:
            style = "bold red"

        actual = actual_records[owner_id]
        actual_record = f"{actual['wins']}-{actual['losses']}"

        table.add_row(
            str(rank),
            team_names[owner_id],
            actual_record,
            f"{consistency:.2f}",
            style=style
        )

    console.print(table)

def main():
    print("[bold magenta]Team Consistency Analysis[/bold magenta]\n")

    weekly_scores, team_names = get_weekly_scores(DB_FILE)
    actual_records = get_actual_records(DB_FILE)
    print_consistency_table(weekly_scores, actual_records, team_names)

if __name__ == "__main__":
    main()