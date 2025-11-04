import sqlite3
from collections import defaultdict
from rich.console import Console
from rich.table import Table

# Configuration
DB_FILE = "sleeper_league_25.db"

def get_all_weekly_scores(db_file):
    """Get all scores for all teams for each week"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute("""
        SELECT r.owner_id, u.display_name, m.week, m.points
        FROM matchups m
        JOIN rosters r ON m.roster_id = r.roster_id
        JOIN users u ON r.owner_id = u.user_id
        WHERE m.points > 0
        ORDER BY m.week, m.points DESC
    """)
    
    weekly_scores = defaultdict(list)  # {week: [(owner_id, name, points), ...]}
    team_names = {}
    
    for owner_id, name, week, points in c.fetchall():
        weekly_scores[week].append({
            'owner_id': owner_id,
            'name': name,
            'points': points
        })
        team_names[owner_id] = name
    
    conn.close()
    return weekly_scores, team_names

def get_actual_records(db_file):
    """Get actual head-to-head win-loss records"""
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

def calculate_all_play_records(weekly_scores):
    """Calculate what record would be if every team played every other team each week"""
    all_play_records = defaultdict(lambda: {
        'wins': 0, 
        'losses': 0, 
        'ties': 0,
        'weekly_ranks': [],
        'total_points': 0
    })
    
    # For each week, compare every team against every other team
    for week, scores in weekly_scores.items():
        # Sort by points for this week
        scores_sorted = sorted(scores, key=lambda x: x['points'], reverse=True)
        
        # Calculate rank for each team this week
        for rank, team in enumerate(scores_sorted, 1):
            all_play_records[team['owner_id']]['weekly_ranks'].append(rank)
            all_play_records[team['owner_id']]['total_points'] += team['points']
        
        # Compare each team against all others
        num_teams = len(scores)
        for i, team1 in enumerate(scores):
            wins_this_week = 0
            losses_this_week = 0
            ties_this_week = 0
            
            for j, team2 in enumerate(scores):
                if i == j:
                    continue  # Don't compare team to itself
                
                if team1['points'] > team2['points']:
                    wins_this_week += 1
                elif team1['points'] < team2['points']:
                    losses_this_week += 1
                else:
                    ties_this_week += 1
            
            all_play_records[team1['owner_id']]['wins'] += wins_this_week
            all_play_records[team1['owner_id']]['losses'] += losses_this_week
            all_play_records[team1['owner_id']]['ties'] += ties_this_week
    
    return all_play_records

def calculate_luck_index(actual_records, all_play_records, team_names):
    """Calculate how lucky/unlucky each team has been"""
    luck_data = []
    
    for owner_id in actual_records.keys():
        actual_wins = actual_records[owner_id]['wins']
        actual_losses = actual_records[owner_id]['losses']
        actual_pct = actual_wins / (actual_wins + actual_losses) if (actual_wins + actual_losses) > 0 else 0
        
        # All-play winning percentage
        all_play_wins = all_play_records[owner_id]['wins']
        all_play_losses = all_play_records[owner_id]['losses']
        all_play_pct = all_play_wins / (all_play_wins + all_play_losses) if (all_play_wins + all_play_losses) > 0 else 0
        
        # Luck index: positive = lucky (actual better than all-play), negative = unlucky
        luck_index = actual_pct - all_play_pct
        
        luck_data.append({
            'owner_id': owner_id,
            'name': team_names[owner_id],
            'actual_wins': actual_wins,
            'actual_losses': actual_losses,
            'actual_pct': actual_pct,
            'all_play_pct': all_play_pct,
            'luck_index': luck_index
        })
    
    return luck_data

def print_true_standings(all_play_records, team_names, actual_records):
    """Print all-play standings table"""
    console = Console()
    
    table = Table(
        title="True Standings (All-Play Record)", 
        show_header=True, 
        header_style="bold magenta"
    )
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Team", style="cyan", no_wrap=False)
    table.add_column("All-Play Record", justify="center")
    table.add_column("Win %", justify="center")
    table.add_column("Actual Record", justify="center", style="dim")
    table.add_column("Avg Rank", justify="center")
    table.add_column("Total PF", justify="center")
    
    # Prepare data and sort by all-play wins
    standings = []
    for owner_id, record in all_play_records.items():
        wins = record['wins']
        losses = record['losses']
        ties = record['ties']
        win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
        avg_rank = sum(record['weekly_ranks']) / len(record['weekly_ranks']) if record['weekly_ranks'] else 0
        
        actual = actual_records[owner_id]
        actual_record = f"{actual['wins']}-{actual['losses']}"
        
        standings.append({
            'owner_id': owner_id,
            'name': team_names[owner_id],
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'win_pct': win_pct,
            'avg_rank': avg_rank,
            'total_points': record['total_points'],
            'actual_record': actual_record
        })
    
    # Sort by win percentage, then by total points
    standings.sort(key=lambda x: (x['win_pct'], x['total_points']), reverse=True)
    
    # Add rows
    for rank, team in enumerate(standings, 1):
        all_play_record = f"{team['wins']}-{team['losses']}"
        if team['ties'] > 0:
            all_play_record += f"-{team['ties']}"
        
        table.add_row(
            str(rank),
            team['name'],
            all_play_record,
            f"{team['win_pct']:.3f}",
            team['actual_record'],
            f"{team['avg_rank']:.1f}",
            f"{team['total_points']:.1f}"
        )
    
    console.print(table)

def print_luck_rankings(luck_data):
    """Print luck index rankings"""
    console = Console()
    
    # Sort by luck index
    luck_data_sorted = sorted(luck_data, key=lambda x: x['luck_index'], reverse=True)
    
    table = Table(
        title="Luck Index (Actual vs All-Play Performance)", 
        show_header=True, 
        header_style="bold magenta"
    )
    table.add_column("Team", style="cyan", no_wrap=False)
    table.add_column("Actual Record", justify="center")
    table.add_column("Actual Win %", justify="center")
    table.add_column("All-Play Win %", justify="center")
    table.add_column("Luck Index", justify="center", style="bold")
    table.add_column("Assessment", justify="center")
    
    for team in luck_data_sorted:
        luck_index = team['luck_index']
        
        # Determine luck assessment
        if luck_index > 0.100:
            assessment = "🍀 Very Lucky"
            style = "bold green"
        elif luck_index > 0.050:
            assessment = "🙂 Lucky"
            style = "green"
        elif luck_index > -0.050:
            assessment = "😐 Neutral"
            style = "white"
        elif luck_index > -0.100:
            assessment = "😞 Unlucky"
            style = "yellow"
        else:
            assessment = "💀 Very Unlucky"
            style = "bold red"
        
        actual_record = f"{team['actual_wins']}-{team['actual_losses']}"
        
        table.add_row(
            team['name'],
            actual_record,
            f"{team['actual_pct']:.3f}",
            f"{team['all_play_pct']:.3f}",
            f"{luck_index:+.3f}",
            assessment,
            style=style
        )
    
    console.print(table)

def print_summary_stats(weekly_scores, all_play_records):
    """Print summary statistics"""
    console = Console()
    
    total_weeks = len(weekly_scores)
    total_teams = len(all_play_records)
    
    console.print("\n[bold cyan]Summary Statistics[/bold cyan]")
    console.print(f"Weeks Played: {total_weeks}")
    console.print(f"Teams: {total_teams}")
    console.print(f"Total Matchups Per Week (All-Play): {total_teams * (total_teams - 1)}")
    console.print(f"Total All-Play Games: {total_weeks * total_teams * (total_teams - 1)}")

def main():
    console = Console()
    
    console.print("[bold magenta]All-Play Record & True Standings Calculator")
    console.print("[bold magenta]═" * 30 + "\n")
    
    console.print("[yellow]Loading data...[/yellow]")
    
    # Get all weekly scores
    weekly_scores, team_names = get_all_weekly_scores(DB_FILE)
    
    # Get actual head-to-head records
    actual_records = get_actual_records(DB_FILE)
    
    # Calculate all-play records
    console.print("[yellow]Calculating all-play records...[/yellow]")
    all_play_records = calculate_all_play_records(weekly_scores)
    
    # Calculate luck index
    console.print("[yellow]Analyzing luck index...[/yellow]\n")
    luck_data = calculate_luck_index(actual_records, all_play_records, team_names)
    
    # Print results
    print_true_standings(all_play_records, team_names, actual_records)
    console.print()
    print_luck_rankings(luck_data)
    console.print()
    print_summary_stats(weekly_scores, all_play_records)
    
    console.print("\n[bold green]Analysis complete![/bold green]\n")

if __name__ == "__main__":
    main()