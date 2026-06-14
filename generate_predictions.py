import json
import os
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent
OPENFOOTBALL_ROOT = ROOT / 'repo-openfootball'

TEAM_NORMALIZATION = {
    'Korea Republic': 'South Korea',
    'Republic of Korea': 'South Korea',
    'South Korea': 'South Korea',
    'Czech Republic': 'Czech Republic',
    'Czechia': 'Czech Republic',
    'United States': 'USA',
    'USA': 'USA',
    'Korea DPR': 'North Korea',
}

SCHEDULE_API = 'https://worldcupjson.net/matches?year=2026'

ACTUAL_RESULTS = {
    ('Brazil', 'Morocco'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Germany', 'Curaçao'): {'home': 7, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('Netherlands', 'Japan'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Qatar', 'Switzerland'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('USA', 'Paraguay'): {'home': 4, 'away': 1, 'status': 'completed', 'source': 'official result'},
}

BOOKMAKER_API_KEY = os.environ.get('ODDS_API_KEY')
BOOKMAKER_API_URL = 'https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds'

BOOKMAKER_FALLBACK_ODDS = {
    ('Canada', 'Bosnia & Herzegovina'): [
        {'bookmaker': 'User Upload', 'home': 1.62, 'draw': 3.32, 'away': 4.75},
    ],
    ('Mexico', 'South Africa'): [
        {'bookmaker': 'Pinnacle', 'home': 1.55, 'draw': 3.95, 'away': 6.80},
        {'bookmaker': 'Bet365', 'home': 1.57, 'draw': 3.90, 'away': 6.50},
        {'bookmaker': 'William Hill', 'home': 1.60, 'draw': 3.80, 'away': 6.40},
    ],
    ('South Korea', 'Czech Republic'): [
        {'bookmaker': 'Pinnacle', 'home': 2.35, 'draw': 3.15, 'away': 2.90},
        {'bookmaker': 'Bet365', 'home': 2.40, 'draw': 3.10, 'away': 2.85},
        {'bookmaker': 'William Hill', 'home': 2.45, 'draw': 3.05, 'away': 2.80},
    ],
    ('Czech Republic', 'South Africa'): [
        {'bookmaker': 'Pinnacle', 'home': 1.92, 'draw': 3.40, 'away': 4.20},
        {'bookmaker': 'Bet365', 'home': 1.95, 'draw': 3.35, 'away': 4.00},
        {'bookmaker': 'William Hill', 'home': 1.90, 'draw': 3.50, 'away': 4.25},
    ],
    ('Mexico', 'South Korea'): [
        {'bookmaker': 'Pinnacle', 'home': 1.45, 'draw': 4.10, 'away': 7.20},
        {'bookmaker': 'Bet365', 'home': 1.47, 'draw': 4.00, 'away': 6.80},
        {'bookmaker': 'William Hill', 'home': 1.50, 'draw': 3.95, 'away': 6.75},
    ],
    ('Czech Republic', 'Mexico'): [
        {'bookmaker': 'Pinnacle', 'home': 5.80, 'draw': 4.40, 'away': 1.52},
        {'bookmaker': 'Bet365', 'home': 5.90, 'draw': 4.30, 'away': 1.53},
        {'bookmaker': 'William Hill', 'home': 5.75, 'draw': 4.25, 'away': 1.50},
    ],
    ('South Korea', 'South Africa'): [
        {'bookmaker': 'Pinnacle', 'home': 2.10, 'draw': 3.40, 'away': 3.50},
        {'bookmaker': 'Bet365', 'home': 2.15, 'draw': 3.35, 'away': 3.40},
        {'bookmaker': 'William Hill', 'home': 2.05, 'draw': 3.50, 'away': 3.45},
    ],
    ('Qatar', 'Switzerland'): [
        {'bookmaker': 'Pinnacle', 'home': 5.50, 'draw': 3.80, 'away': 1.65},
        {'bookmaker': 'Bet365', 'home': 5.75, 'draw': 3.70, 'away': 1.63},
    ],
    ('Brazil', 'Morocco'): [
        {'bookmaker': 'Pinnacle', 'home': 1.80, 'draw': 3.60, 'away': 4.00},
        {'bookmaker': 'Bet365', 'home': 1.85, 'draw': 3.50, 'away': 3.90},
    ],
    ('USA', 'Paraguay'): [
        {'bookmaker': 'Pinnacle', 'home': 1.95, 'draw': 3.40, 'away': 3.80},
        {'bookmaker': 'Bet365', 'home': 2.00, 'draw': 3.30, 'away': 3.75},
    ],
}


def normalize_team_name(name: str) -> str:
    name = name.strip()
    if name in TEAM_NORMALIZATION:
        return TEAM_NORMALIZATION[name]
    return name


def get_actual_result(home: str, away: str):
    return ACTUAL_RESULTS.get((home, away))


def odds_to_probabilities(odds):
    implied = {
        'home': 1.0 / odds['home'],
        'draw': 1.0 / odds['draw'],
        'away': 1.0 / odds['away'],
    }
    total = sum(implied.values())
    return {k: v / total for k, v in implied.items()}


def fetch_bookmaker_odds_from_api():
    if not BOOKMAKER_API_KEY:
        return None

    params = {
        'apiKey': BOOKMAKER_API_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso',
    }
    url = f"{BOOKMAKER_API_URL}?{urllib.parse.urlencode(params)}"
    print('Fetching bookmaker odds from API...')
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        print('Failed to fetch bookmaker odds from API:', exc)
        return None

    odds_by_match = {}
    for event in data:
        raw_teams = event.get('teams') or []
        teams = [normalize_team_name(t) for t in raw_teams if isinstance(t, str)]

        home_team = normalize_team_name(event.get('home_team') or (teams[0] if len(teams) >= 1 else None))
        away_team = normalize_team_name(event.get('away_team') or (teams[1] if len(teams) >= 2 else None))
        if not home_team or not away_team:
            continue

        entries = []
        for bookmaker in event.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') != 'h2h':
                    continue
                prices = {}
                for outcome in market.get('outcomes', []):
                    name = normalize_team_name(outcome.get('name', ''))
                    price = outcome.get('price')
                    if not name or price is None:
                        continue
                    if name.lower() in ('draw', 'the draw'):
                        prices['draw'] = price
                    else:
                        prices[name] = price

                if home_team in prices and away_team in prices and 'draw' in prices:
                    entries.append({
                        'bookmaker': bookmaker.get('title', 'unknown'),
                        'home': prices[home_team],
                        'draw': prices['draw'],
                        'away': prices[away_team],
                    })
                    break

        if entries:
            odds_by_match[(home_team, away_team)] = entries

    if odds_by_match:
        save_bookmaker_odds_snapshot(odds_by_match)
    return odds_by_match


def normalize_odds_key(key):
    if isinstance(key, tuple):
        return key
    if isinstance(key, list):
        return tuple(key)
    if isinstance(key, str):
        if '|' in key:
            parts = [p.strip() for p in key.split('|', 1)]
        elif ' v ' in key:
            parts = [p.strip() for p in key.split(' v ', 1)]
        else:
            parts = [p.strip() for p in key.split(',', 1)]
        if len(parts) == 2:
            return tuple(parts)
    raise ValueError(f'Unsupported bookmaker odds key format: {key}')


def save_bookmaker_odds_snapshot(odds_by_match):
    local_file = ROOT / 'bookmaker_odds.json'
    try:
        snapshot = {
            f"{home}|{away}": odds
            for (home, away), odds in odds_by_match.items()
        }
        local_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Saved bookmaker odds snapshot to bookmaker_odds.json')
    except Exception as exc:
        print('Failed to save bookmaker odds snapshot:', exc)


def load_local_bookmaker_odds():
    local_file = ROOT / 'bookmaker_odds.json'
    if not local_file.exists():
        return None

    try:
        raw = json.loads(local_file.read_text(encoding='utf-8'))
    except Exception as exc:
        print('Failed to load local bookmaker odds file:', exc)
        return None

    normalized = {}
    for key, values in raw.items():
        try:
            normalized[normalize_odds_key(key)] = values
        except ValueError:
            continue
    return normalized


def load_bookmaker_odds():
    api_data = fetch_bookmaker_odds_from_api()
    local_data = load_local_bookmaker_odds()
    if api_data is None and local_data is None:
        print('Using fallback hardcoded bookmaker odds.')
        return BOOKMAKER_FALLBACK_ODDS

    if api_data is not None:
        print('Loaded bookmaker odds from API for', len(api_data), 'matches.')
    if local_data is not None:
        print('Loaded bookmaker odds from local bookmaker_odds.json for', len(local_data), 'matches.')

    all_keys = set(BOOKMAKER_FALLBACK_ODDS.keys())
    if api_data is not None:
        all_keys |= set(api_data.keys())
    if local_data is not None:
        all_keys |= set(local_data.keys())

    combined = {}
    for key in all_keys:
        if api_data is not None and key in api_data:
            combined[key] = api_data[key]
        elif local_data is not None and key in local_data:
            combined[key] = local_data[key]
        else:
            combined[key] = BOOKMAKER_FALLBACK_ODDS.get(key, [])

    return combined


def average_bookmaker_odds(home: str, away: str, bookmaker_odds):
    key = (home, away)
    reversed_match = False
    if key not in bookmaker_odds:
        key = (away, home)
        if key not in bookmaker_odds:
            return None
        reversed_match = True

    raw_entries = bookmaker_odds[key]
    entries = []
    for odds in raw_entries:
        if odds['home'] <= 1 or odds['draw'] <= 1 or odds['away'] <= 1:
            continue
        if reversed_match:
            entries.append({'home': odds['away'], 'draw': odds['draw'], 'away': odds['home'], 'bookmaker': odds.get('bookmaker')})
        else:
            entries.append({'home': odds['home'], 'draw': odds['draw'], 'away': odds['away'], 'bookmaker': odds.get('bookmaker')})

    trimmed = [o for o in entries if o['home'] < 8 and o['draw'] < 9 and o['away'] < 8]
    if trimmed:
        entries = trimmed
    if not entries:
        return None

    average = {
        'home': float(np.median([o['home'] for o in entries])),
        'draw': float(np.median([o['draw'] for o in entries])),
        'away': float(np.median([o['away'] for o in entries])),
    }
    sources = [o['bookmaker'] for o in entries if 'bookmaker' in o]
    return {
        'bookmaker_odds': average,
        'implied_probabilities': odds_to_probabilities(average),
        'sources': sources,
    }


def parse_match_line(line: str):
    line = line.rstrip('\n')
    # drop leading spaces and simplify spacing for easier parsing
    if 'UTC' not in line or not re.search(r'\d+-\d+', line):
        return None

    score_match = re.search(r'(\d+)-(\d+)', line)
    if not score_match:
        return None

    left = line[: score_match.start()].strip()
    right = line[score_match.end() :].strip()
    left = re.sub(r'^\d{1,2}:\d{2}\s+UTC[+-]\d+\s+', '', left)
    right = re.sub(r'^\(.*?\)\s*', '', right)
    right = right.split('@')[0].strip()

    team1 = normalize_team_name(left)
    team2 = normalize_team_name(right)
    score1 = int(score_match.group(1))
    score2 = int(score_match.group(2))
    return team1, team2, score1, score2


def load_historical_matches():
    matches = []
    for folder in sorted(OPENFOOTBALL_ROOT.iterdir()):
        if not folder.is_dir() or not folder.name.endswith('--') and '--' not in folder.name:
            continue
        year = int(folder.name.split('--')[0])
        if year >= 2026:
            continue
        cup_file = folder / 'cup.txt'
        if not cup_file.exists():
            continue
        with cup_file.open('r', encoding='utf-8') as fh:
            for line in fh:
                parsed = parse_match_line(line)
                if parsed:
                    team1, team2, score1, score2 = parsed
                    matches.append({'year': year, 'team1': team1, 'team2': team2, 'score1': score1, 'score2': score2})
    return pd.DataFrame(matches)


def build_team_stats(matches: pd.DataFrame):
    stats = defaultdict(lambda: {'played': 0, 'goals_for': 0, 'goals_against': 0, 'wins': 0, 'draws': 0, 'losses': 0})
    for _, row in matches.iterrows():
        t1, t2, g1, g2 = row.team1, row.team2, row.score1, row.score2
        stats[t1]['played'] += 1
        stats[t1]['goals_for'] += g1
        stats[t1]['goals_against'] += g2
        stats[t2]['played'] += 1
        stats[t2]['goals_for'] += g2
        stats[t2]['goals_against'] += g1

        if g1 > g2:
            stats[t1]['wins'] += 1
            stats[t2]['losses'] += 1
        elif g1 < g2:
            stats[t2]['wins'] += 1
            stats[t1]['losses'] += 1
        else:
            stats[t1]['draws'] += 1
            stats[t2]['draws'] += 1

    team_df = []
    for team, data in stats.items():
        if data['played'] == 0:
            continue
        team_df.append({
            'team': team,
            'played': data['played'],
            'goals_for_avg': data['goals_for'] / data['played'],
            'goals_against_avg': data['goals_against'] / data['played'],
            'goal_diff_avg': (data['goals_for'] - data['goals_against']) / data['played'],
            'win_rate': data['wins'] / data['played'],
            'draw_rate': data['draws'] / data['played'],
            'loss_rate': data['losses'] / data['played'],
        })
    return pd.DataFrame(team_df).set_index('team')


def get_team_summary(team_stats, team):
    if team in team_stats.index:
        return team_stats.loc[team]
    avg = team_stats.mean()
    avg['goals_for_avg'] = float(avg.get('goals_for_avg', 1.2))
    avg['goals_against_avg'] = float(avg.get('goals_against_avg', 1.2))
    avg['goal_diff_avg'] = float(avg.get('goal_diff_avg', 0.0))
    avg['win_rate'] = float(avg.get('win_rate', 0.33))
    avg['draw_rate'] = float(avg.get('draw_rate', 0.25))
    avg['loss_rate'] = float(avg.get('loss_rate', 0.42))
    return avg


def make_feature_row(row, team_stats):
    t1 = row.team1
    t2 = row.team2
    t1_stats = get_team_summary(team_stats, t1)
    t2_stats = get_team_summary(team_stats, t2)
    return {
        'team1_goals_for_avg': t1_stats.goals_for_avg,
        'team1_goals_against_avg': t1_stats.goals_against_avg,
        'team1_goal_diff_avg': t1_stats.goal_diff_avg,
        'team1_win_rate': t1_stats.win_rate,
        'team1_draw_rate': t1_stats.draw_rate,
        'team2_goals_for_avg': t2_stats.goals_for_avg,
        'team2_goals_against_avg': t2_stats.goals_against_avg,
        'team2_goal_diff_avg': t2_stats.goal_diff_avg,
        'team2_win_rate': t2_stats.win_rate,
        'team2_draw_rate': t2_stats.draw_rate,
        'goal_diff_delta': t1_stats.goal_diff_avg - t2_stats.goal_diff_avg,
        'win_rate_delta': t1_stats.win_rate - t2_stats.win_rate,
    }


def train_model(matches, team_stats):
    rows = []
    labels = []
    for _, row in matches.iterrows():
        feature_row = make_feature_row(row, team_stats)
        if feature_row is None:
            continue
        rows.append(feature_row)
        if row.score1 > row.score2:
            labels.append(0)
        elif row.score1 == row.score2:
            labels.append(1)
        else:
            labels.append(2)

    X = pd.DataFrame(rows)
    y = np.array(labels)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.18, random_state=42, stratify=y)

    model = XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False,
        max_depth=4,
        learning_rate=0.15,
        n_estimators=120,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model, X_test, y_test


def parse_2026_date(date_line: str, time_line: str):
    month = date_line.strip().split()[1]
    day = date_line.strip().split()[2]
    date_str = f"{month} {day} 2026"
    time_match = re.search(r"(\d{1,2}:\d{2})\s+UTC([+-]?\d+)", time_line)
    if not time_match:
        raise ValueError(f'Cannot parse time from line: {time_line}')
    time_str = time_match.group(1)
    offset_hours = int(time_match.group(2))
    dt = datetime.strptime(f"{date_str} {time_str}", '%B %d %Y %H:%M')
    return dt.replace(tzinfo=timezone(timedelta(hours=offset_hours))).isoformat()


def load_2026_group_matches(group_label=None):
    cup_file = OPENFOOTBALL_ROOT / '2026--usa' / 'cup.txt'
    if not cup_file.exists():
        raise FileNotFoundError('Cannot find 2026 cup.txt in openfootball dataset.')

    groups = defaultdict(list)
    current_group = None
    in_group = group_label is None
    current_date = None
    with cup_file.open('r', encoding='utf-8') as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith('▪ Group '):
                current_group = stripped[2:]
                in_group = group_label is None or current_group == group_label
                continue
            if stripped.startswith('▪ '):
                current_group = None
                in_group = False
                continue
            if not in_group:
                continue
            if not stripped:
                continue
            if re.match(r'^[A-Za-z]{3} ', stripped):
                current_date = stripped
                continue
            if ' v ' in line and '@' in line:
                time_team, venue = line.split('@', 1)
                venue = venue.strip()
                home_away = time_team.strip()
                home_away = re.sub(r'^\d{1,2}:\d{2}\s+UTC[+-]?\d+\s+', '', home_away)
                parts = home_away.split(' v ')
                if len(parts) != 2 or current_group is None:
                    continue
                home = normalize_team_name(parts[0].strip())
                away = normalize_team_name(parts[1].strip())
                match_datetime = parse_2026_date(current_date, line)
                groups[current_group].append({
                    'home_team': home,
                    'away_team': away,
                    'datetime': match_datetime,
                    'venue': venue,
                })
    if group_label:
        return groups.get(group_label, [])
    return dict(groups)


def team_strength(team_stats, team_name):
    if team_name not in team_stats.index:
        return 0.5
    s = team_stats.loc[team_name]
    return 0.5 + 0.25 * s.win_rate + 0.15 * np.tanh(s.goal_diff_avg / 2)


def context_probabilities(match, team_stats, start_date):
    home = match['home_team'] if isinstance(match['home_team'], str) else match['home_team']['name']
    away = match['away_team'] if isinstance(match['away_team'], str) else match['away_team']['name']
    home_strength = team_strength(team_stats, home)
    away_strength = team_strength(team_stats, away)
    ratio = home_strength / max(home_strength + away_strength, 0.0001)

    kickoff = datetime.fromisoformat(match['datetime'].replace('Z', '+00:00'))
    day_offset = (kickoff - start_date).days
    rest_effect = min(max(day_offset * 0.02, -0.08), 0.08)

    home_prob = np.clip(ratio + 0.03 + rest_effect, 0.08, 0.88)
    away_prob = np.clip(1 - ratio - 0.02 - rest_effect, 0.08, 0.88)
    draw_prob = np.clip(1 - home_prob - away_prob, 0.08, 0.40)
    total = home_prob + away_prob + draw_prob
    return home_prob / total, draw_prob / total, away_prob / total


def predict_scores(probs, home, away, team_stats):
    home_strength = team_strength(team_stats, home)
    away_strength = team_strength(team_stats, away)
    home_summary = get_team_summary(team_stats, home)
    away_summary = get_team_summary(team_stats, away)

    home_base = 1.05 + (home_strength - away_strength) * 0.35
    away_base = 1.05 + (away_strength - home_strength) * 0.35

    home_lambda = max(0.45, home_base * (0.8 * home_summary.goals_for_avg + 0.2 * away_summary.goals_against_avg))
    away_lambda = max(0.45, away_base * (0.8 * away_summary.goals_for_avg + 0.2 * home_summary.goals_against_avg))

    home_goals = int(round((probs[0] + probs[1] * 0.35) * home_lambda * 1.9))
    away_goals = int(round((probs[2] + probs[1] * 0.35) * away_lambda * 1.9))

    if probs[1] >= probs[0] and probs[1] >= probs[2]:
        target = max((home_goals + away_goals) // 2, 1)
        home_goals = target
        away_goals = target
    elif probs[0] > probs[2] and home_goals <= away_goals:
        home_goals = away_goals + 1
    elif probs[2] > probs[0] and away_goals <= home_goals:
        away_goals = home_goals + 1

    return max(0, home_goals), max(0, away_goals)


def build_group_table(predictions):
    team_rows = defaultdict(lambda: {'played': 0, 'win': 0, 'draw': 0, 'loss': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0})
    for m in predictions:
        home = m['home_team']
        away = m['away_team']
        gh = m['predicted_score']['home']
        ga = m['predicted_score']['away']
        team_rows[home]['played'] += 1
        team_rows[away]['played'] += 1
        team_rows[home]['goals_for'] += gh
        team_rows[home]['goals_against'] += ga
        team_rows[away]['goals_for'] += ga
        team_rows[away]['goals_against'] += gh
        if gh > ga:
            team_rows[home]['win'] += 1
            team_rows[away]['loss'] += 1
            team_rows[home]['points'] += 3
        elif gh < ga:
            team_rows[away]['win'] += 1
            team_rows[home]['loss'] += 1
            team_rows[away]['points'] += 3
        else:
            team_rows[home]['draw'] += 1
            team_rows[away]['draw'] += 1
            team_rows[home]['points'] += 1
            team_rows[away]['points'] += 1

    table = []
    for team, values in team_rows.items():
        values['team'] = team
        values['goal_diff'] = values['goals_for'] - values['goals_against']
        table.append(values)
    table.sort(key=lambda x: (x['points'], x['goal_diff'], x['goals_for']), reverse=True)
    return table


def main():
    print('Loading historical matches...')
    historical_matches = load_historical_matches()
    print('Historical match count:', len(historical_matches))
    team_stats = build_team_stats(historical_matches)
    model, X_test, y_test = train_model(historical_matches, team_stats)
    if len(X_test) > 0:
        test_probs = model.predict_proba(X_test)
        print('Sample model output (first row):', test_probs[0])

    print('Loading 2026 group schedules...')
    groups_matches = load_2026_group_matches()
    if not groups_matches:
        raise RuntimeError('2026 group matches not found in local 2026 schedule.')

    bookmaker_odds = load_bookmaker_odds()
    all_matches = [m for group in groups_matches.values() for m in group]
    start_date = min(datetime.fromisoformat(m['datetime']) for m in all_matches)
    predictions_by_group = []
    for group_label, group_matches in groups_matches.items():
        if not group_matches:
            continue

        group_predictions = []
        for match in sorted(group_matches, key=lambda m: m['datetime']):
            home = match['home_team']
            away = match['away_team']
            row = pd.Series({
                'team1': home,
                'team2': away,
                'score1': 0,
                'score2': 0,
            })
            features = make_feature_row(row, team_stats)
            if features is None:
                print('Skipping match because team stats are missing for', home, away)
                continue
            xgb_probs = model.predict_proba(pd.DataFrame([features]))[0]
            context_probs = context_probabilities(match, team_stats, start_date)
            odds_data = average_bookmaker_odds(home, away, bookmaker_odds)
            if odds_data is not None:
                odds_probs = odds_data['implied_probabilities']
                match_bookmaker_odds = odds_data['bookmaker_odds']
            else:
                odds_probs = {'home': 0.0, 'draw': 0.0, 'away': 0.0}
                match_bookmaker_odds = None

            # 动态权重融合 - 基于6场实际比赛数据优化
            # 数据驱动权重: Odds(83.3%) > Context(50%) > XGBoost(16.7%)
            weights = {
                'xgb': 0.15,      # ↓ 从20%→15% (XGBoost仅16.7%准确度，表现很差)
                'context': 0.30,  # ↓ 从35%→30% (Context 50%准确度，表现中等)
                'odds': 0.55,     # ↑ 从45%→55% (Odds 83.3%准确度，表现最优)
            }
            if odds_data is None:
                weights = {
                    'xgb': 0.30,   # ↓ 降低XGBoost权重
                    'context': 0.70,  # ↑ Context主导
                    'odds': 0.0,
                }

            # 贝叶斯赔率修正 - 防止极端低估平局
            fused = np.array([
                xgb_probs[0] * weights['xgb'] + context_probs[0] * weights['context'] + odds_probs['home'] * weights['odds'],
                xgb_probs[1] * weights['xgb'] + context_probs[1] * weights['context'] + odds_probs['draw'] * weights['odds'],
                xgb_probs[2] * weights['xgb'] + context_probs[2] * weights['context'] + odds_probs['away'] * weights['odds'],
            ])
            fused = fused / fused.sum()

            # 增强的贝叶斯平率修正 - 6场数据优化
            # 关键发现：平局预测失败 (0/3)，需要大幅提升平率预测
            if odds_data is not None:
                odds_vec = np.array([odds_probs['home'], odds_probs['draw'], odds_probs['away']])

                # 特别关注平率的极端低估（模型历史上严重低估平）
                draw_divergence = abs(fused[1] - odds_vec[1])

                # 改进条件1: 降低触发阈值从8%→5%，提升敏感度
                # 改进条件2: 增强修正强度，信赖赔率而不是模型
                if draw_divergence > 0.05 or fused[1] < 0.15:  # 更激进的触发条件
                    # 当模型平率极低(<15%)时，无条件应用强修正
                    if fused[1] < 0.15:
                        # 极度低估：强烈信赖赔率
                        corrected_draw_prob = 0.1 * fused[1] + 0.9 * odds_vec[1]
                    elif fused[1] < 0.25 and odds_vec[1] > 0.20:
                        # 低估情况：主要信赖赔率
                        corrected_draw_prob = 0.2 * fused[1] + 0.8 * odds_vec[1]
                    else:
                        # 中等情况：标准修正
                        corrected_draw_prob = 0.35 * fused[1] + 0.65 * odds_vec[1]

                    # 重新归一化
                    remaining_prob = 1.0 - corrected_draw_prob
                    home_away_ratio = fused[0] / (fused[0] + fused[2]) if (fused[0] + fused[2]) > 0 else 0.5
                    fused[0] = remaining_prob * home_away_ratio
                    fused[1] = corrected_draw_prob
                    fused[2] = remaining_prob * (1 - home_away_ratio)

                # 保留原有的大差异检测（用于主客队胜负）
                overall_divergence = np.linalg.norm(fused - odds_vec, ord=1)
                if overall_divergence > 0.60:
                    fused = fused * 0.60 + odds_vec * 0.40  # 提升Odds权重
                    fused = fused / fused.sum()
            score_home, score_away = predict_scores(fused, home, away, team_stats)
            best_outcome = ['Home Win', 'Draw', 'Away Win'][int(np.argmax(fused))]
            actual = get_actual_result(home, away)
            group_predictions.append({
                'home_team': home,
                'away_team': away,
                'datetime': match['datetime'],
                'venue': match['venue'],
                'group': group_label,
                'probabilities': {
                    'home': float(fused[0]),
                    'draw': float(fused[1]),
                    'away': float(fused[2]),
                },
                'predicted_score': {'home': int(score_home), 'away': int(score_away)},
                'best_outcome': best_outcome,
                'bookmaker_odds': match_bookmaker_odds,
                'actual_score': actual and {'home': actual['home'], 'away': actual['away']} or None,
                'result_status': actual['status'] if actual else 'predicted',
                'result_source': actual['source'] if actual else None,
                'xgb_probabilities': {
                    'home': float(xgb_probs[0]),
                    'draw': float(xgb_probs[1]),
                    'away': float(xgb_probs[2]),
                },
                'context_probabilities': {
                    'home': float(context_probs[0]),
                    'draw': float(context_probs[1]),
                    'away': float(context_probs[2]),
                },
            })

        standings = build_group_table(group_predictions)
        predictions_by_group.append({
            'group': group_label,
            'predictions': group_predictions,
            'standings': standings,
        })

    output = {'groups': predictions_by_group}
    with open(ROOT / 'predictions.json', 'w', encoding='utf-8') as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    print('Generated predictions.json for', len(predictions_by_group), 'groups.')


if __name__ == '__main__':
    main()
