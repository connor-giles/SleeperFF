import sqlite3
import numpy as np
from collections import defaultdict
import requests

# ======================================================================== #
#                                                                          #
#   This scripts calculates the win probabilities for the rest of the      #
#   season based on how the teams have done up to this point. It dis-      #
#   plays expected wins and proj. total wins for each user in the league   #
#                                                                          #
# ======================================================================== #


# Configuration
DB_FILE = "sleeper_league_25.db"
LEAGUE_ID = "1253516124402757633"
NUM_SIMULATIONS = 10000

def get_current_week():
    """Get current NFL week from Sleeper API"""
    nfl_state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
    return nfl_state['week']

def get_team_scores(db_file):
    """Get all historical scores for each team"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get scores grouped by team
    c.execute("""
        SELECT r.owner_id, u.display_name, m.points, m.week
        FROM matchups m
        JOIN rosters r ON m.roster_id = r.roster_id
        JOIN users u ON r.owner_id = u.user_id
        WHERE m.points > 0
        ORDER BY m.week
    """)
    
    team_scores = defaultdict(list)
    team_names = {}
    
    for owner_id, display_name, points, week in c.fetchall():
        team_scores[owner_id].append(points)
        team_names[owner_id] = display_name
    
    conn.close()
    return team_scores, team_names

def get_remaining_matchups(db_file, league_id, current_week, end_week=14):
    """Get remaining matchups for the regular season"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    remaining_matchups = []
    
    # Only fetch through end_week (default 14 for regular season)
    for week in range(current_week, end_week + 1):
        try:
            matchups = requests.get(
                f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
            ).json()
            
            if not matchups or matchups == []:
                break
            
            # Group by matchup_id to find opponents
            matchup_groups = defaultdict(list)
            for m in matchups:
                matchup_groups[m['matchup_id']].append(m['roster_id'])
            
            # Create pairs
            for matchup_id, roster_ids in matchup_groups.items():
                if len(roster_ids) == 2:
                    # Get owner_ids for these rosters
                    c.execute("""
                        SELECT roster_id, owner_id 
                        FROM rosters 
                        WHERE roster_id IN (?, ?)
                    """, tuple(roster_ids))
                    
                    roster_to_owner = {r[0]: r[1] for r in c.fetchall()}
                    
                    if len(roster_to_owner) == 2:
                        owner1 = roster_to_owner[roster_ids[0]]
                        owner2 = roster_to_owner[roster_ids[1]]
                        remaining_matchups.append({
                            'week': week,
                            'team1': owner1,
                            'team2': owner2
                        })
        except:
            break
    
    conn.close()
    return remaining_matchups

def simulate_matchup(team1_scores, team2_scores, n_sims=10000):
    """
    Simulate a matchup between two teams based on their historical scoring.
    Returns win probability for team1.
    """
    # Sample from historical scores with replacement
    team1_samples = np.random.choice(team1_scores, size=n_sims)
    team2_samples = np.random.choice(team2_scores, size=n_sims)
    
    # Calculate win probability
    team1_wins = np.sum(team1_samples > team2_samples)
    ties = np.sum(team1_samples == team2_samples)
    
    # Give half credit for ties
    win_prob = (team1_wins + 0.5 * ties) / n_sims
    
    return win_prob

def calculate_win_probabilities(team_scores, remaining_matchups, n_sims=10000):
    """Calculate win probabilities for all remaining matchups"""
    results = []
    
    for matchup in remaining_matchups:
        team1_id = matchup['team1']
        team2_id = matchup['team2']
        week = matchup['week']
        
        # Get historical scores
        team1_hist = team_scores[team1_id]
        team2_hist = team_scores[team2_id]
        
        # Simulate matchup
        win_prob = simulate_matchup(team1_hist, team2_hist, n_sims)
        
        results.append({
            'week': week,
            'team1': team1_id,
            'team2': team2_id,
            'team1_win_prob': win_prob,
            'team2_win_prob': 1 - win_prob,
            'team1_avg': np.mean(team1_hist),
            'team2_avg': np.mean(team2_hist)
        })
    
    return results

def simulate_season(team_scores, remaining_matchups, n_sims=10000):
    """
    Simulate the rest of the season to get expected wins for each team.
    Returns dictionary of {team_id: expected_additional_wins}
    """
    expected_wins = defaultdict(float)
    
    for matchup in remaining_matchups:
        team1_id = matchup['team1']
        team2_id = matchup['team2']
        
        # Get historical scores
        team1_hist = team_scores[team1_id]
        team2_hist = team_scores[team2_id]
        
        # Calculate win probability
        win_prob = simulate_matchup(team1_hist, team2_hist, n_sims)
        
        # Add expected wins
        expected_wins[team1_id] += win_prob
        expected_wins[team2_id] += (1 - win_prob)
    
    return expected_wins

def get_current_records(db_file):
    """Get current win-loss records"""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # Get all matchup results
    c.execute("""
        SELECT m1.roster_id, r1.owner_id, u1.display_name,
               m1.week, m1.points, m1.matchup_id_group,
               m2.points as opp_points
        FROM matchups m1
        JOIN matchups m2 ON m1.matchup_id_group = m2.matchup_id_group 
            AND m1.week = m2.week 
            AND m1.roster_id != m2.roster_id
        JOIN rosters r1 ON m1.roster_id = r1.roster_id
        JOIN users u1 ON r1.owner_id = u1.user_id
        WHERE m1.points > 0
        ORDER BY u1.display_name, m1.week
    """)
    
    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'name': ''})
    
    for roster_id, owner_id, name, week, points, matchup_id, opp_points in c.fetchall():
        records[owner_id]['name'] = name
        if points > opp_points:
            records[owner_id]['wins'] += 1
        else:
            records[owner_id]['losses'] += 1
    
    conn.close()
    return records

def print_projections(team_names, current_records, expected_wins):
    """Print projections using Rich table"""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    table = Table(title="Season Projections", show_header=True, header_style="bold magenta")
    table.add_column("Team", style="cyan", no_wrap=False)
    table.add_column("Current Record", justify="center")
    table.add_column("Expected Wins", justify="center")
    table.add_column("Projected Total", justify="center", style="bold green")
    
    # Prepare data
    proj_data = []
    for owner_id, exp_wins in expected_wins.items():
        name = team_names[owner_id]
        curr_wins = current_records[owner_id]['wins']
        curr_losses = current_records[owner_id]['losses']
        projected_total = curr_wins + exp_wins
        
        proj_data.append({
            'name': name,
            'current': f"{curr_wins}-{curr_losses}",
            'expected': exp_wins,
            'total': projected_total
        })
    
    # Sort by projected total
    proj_data.sort(key=lambda x: x['total'], reverse=True)
    
    # Add rows
    for proj in proj_data:
        table.add_row(
            proj['name'],
            proj['current'],
            f"{proj['expected']:.2f}",
            f"{proj['total']:.2f}"
        )
    
    console.print(table)

def main():
    print("=" * 60)
    print("Win Probability Calculator - Remaining Season")
    print("=" * 60)
    
    # Configuration
    REGULAR_SEASON_END_WEEK = 14  # Playoffs start week 15
    
    # Get current week
    current_week = get_current_week()
    print(f"\nCurrent NFL Week: {current_week}")
    print(f"Regular Season ends Week {REGULAR_SEASON_END_WEEK}")
    
    # Get historical scoring data
    print("\nLoading historical team scores...")
    team_scores, team_names = get_team_scores(DB_FILE)
    
    print(f"Found {len(team_scores)} teams with scoring history")
    
    # Get remaining matchups (only through week 14)
    print("\nFetching remaining regular season matchups...")
    remaining_matchups = get_remaining_matchups(DB_FILE, LEAGUE_ID, current_week, REGULAR_SEASON_END_WEEK)
    
    if not remaining_matchups:
        print("No remaining matchups found. Season may be complete or matchups not yet set.")
        return
    
    print(f"Found {len(remaining_matchups)} remaining matchups")
    
    # Calculate win probabilities
    print(f"\nSimulating matchups ({NUM_SIMULATIONS:,} simulations per matchup)...")
    matchup_probs = calculate_win_probabilities(team_scores, remaining_matchups, NUM_SIMULATIONS)
    
    # Get current records
    current_records = get_current_records(DB_FILE)
    
    # Simulate rest of season
    print("\nSimulating rest of season...")
    expected_wins = simulate_season(team_scores, remaining_matchups, NUM_SIMULATIONS)
    
    # Print results
    print("\n" + "=" * 60)
    print("REMAINING MATCHUP WIN PROBABILITIES")
    print("=" * 60)
    
    for result in matchup_probs:
        team1_name = team_names[result['team1']]
        team2_name = team_names[result['team2']]
        
        print(f"\nWeek {result['week']}:")
        print(f"  {team1_name:20} ({result['team1_avg']:.1f} avg) - {result['team1_win_prob']*100:.1f}% win probability")
        print(f"  {team2_name:20} ({result['team2_avg']:.1f} avg) - {result['team2_win_prob']*100:.1f}% win probability")
    
    # Print season projections with Rich table
    print("\n")
    print_projections(team_names, current_records, expected_wins)

if __name__ == "__main__":
    main()