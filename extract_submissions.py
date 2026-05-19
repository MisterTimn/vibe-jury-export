#!/usr/bin/env python3
"""
Busker Street Submissions Extractor - VI.BE HAR to CSV

Usage:
    1. On VI.BE submissions page, open DevTools → Network tab
    2. Refresh the page to capture all API calls
    3. Right-click → Save all as HAR
    4. Run: python3 extract_submissions.py [har_file]
"""

import json
import csv
import os
import sys
import glob
from datetime import datetime

BROAD_GENRE_MAPPING = {
    'hip-hop': ['hiphop', 'hip-hop', 'alt. hiphop', 'trap', 'rap', 'boombap', 'boom bap'],
    'electronic': ['electronic', 'electro', 'synth', 'dance', 'edm', 'techno', 'house', 
                   'ambient', 'idm', 'drum and bass', 'dnb', 'dubstep', 'trance'],
    'metal': ['metal', 'post-metal', 'stoner', 'doom', 'death metal', 'black metal',
              'nu-metal', 'thrash', 'sludge', 'heavy'],
    'punk': ['punk', 'post-punk', 'hardcore', 'garage', 'oi', 'pop punk', 'skate punk',
             'street punk', 'anarcho'],
    'rock': ['rock', 'hardrock', 'hard rock', 'classic rock', 'progressive rock', 
             'rock & roll', 'rock and roll', 'poprock', 'post-rock', 'grunge', 
             'alternative', 'alt', 'indie rock', 'indierock', 'shoegaze', 'noise rock',
             'psychedelic', 'psych', 'new wave', '80s', '90s', 'britpop'],
    'pop': ['pop', 'indie pop', 'dreampop', 'dream pop', 'hyperpop', 'synth pop',
            'synthpop', 'electropop', 'art pop', 'chamber pop'],
    'singer-songwriter': ['singer-songwriter', 'folk', 'americana', 'country', 
                          'kleinkunst', 'acoustic', 'chanson', 'traditioneel',
                          'nederlandstalig', 'lo-fi', 'slowcore', 'soft'],
    'jazz/soul': ['jazz', 'neo-soul', 'soul', 'funk', 'r&b', 'blues', 'fusion',
                  'swing', 'bebop', 'smooth jazz', 'afrobeat', 'afro'],
    'world': ['reggae', 'ska', 'dub', 'latin', 'afro', 'world', 'celtic', 'balkan'],
    'experimental': ['experimental', 'avant', 'noise', 'drone', 'glitch', 'art'],
}

GENRE_PRIORITY = [
    'hip-hop', 'metal', 'punk', 'electronic', 'jazz/soul', 
    'world', 'singer-songwriter', 'pop', 'rock', 'experimental',
]


def classify_genre(genres_str: str, custom_genre: str) -> str:
    all_text = f"{genres_str} {custom_genre}".lower()
    for broad_genre in GENRE_PRIORITY:
        for keyword in BROAD_GENRE_MAPPING.get(broad_genre, []):
            if keyword in all_text:
                return broad_genre
    return 'other'


def find_har_file(directory: str) -> str:
    har_files = glob.glob(os.path.join(directory, '*.har'))
    if not har_files:
        raise FileNotFoundError(f"No HAR files found in {directory}")
    return max(har_files, key=os.path.getmtime)


def extract_submissions(har_path: str) -> list:
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    submissions = []
    for entry in har['log']['entries']:
        url = entry['request']['url']
        if 'callsubmissions' in url and 'limit=100' in url:
            content = entry['response']['content']
            if 'text' in content:
                try:
                    data = json.loads(content['text'])
                    if isinstance(data, dict) and 'items' in data:
                        submissions.extend(data['items'])
                except json.JSONDecodeError:
                    continue
    
    seen = set()
    unique = []
    for sub in submissions:
        uuid = sub.get('uuid')
        if uuid and uuid not in seen:
            seen.add(uuid)
            unique.append(sub)
    return unique


def get_juror_name(user: dict) -> str:
    given = user.get('givenName', '').strip()
    family = user.get('familyName', '').strip()
    return f"{given} {family}".strip() if family else given


def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    return phone.replace(' ', '').replace('-', '').replace('.', '')


def process_submissions(submissions: list) -> tuple:
    juror_names = set()
    for sub in submissions:
        for resp in sub.get('responses', []):
            name = get_juror_name(resp.get('user', {}))
            if name:
                juror_names.add(name)
    jurors = sorted(list(juror_names))
    
    rows = []
    for sub in submissions:
        artist_info = sub.get('artistInfo', {})
        genres = ', '.join([g.get('name', '') for g in artist_info.get('genres', [])])
        custom_genre = artist_info.get('customGenre', '')
        
        juror_ratings = {j: '' for j in jurors}
        juror_notes = {j: '' for j in jurors}
        for resp in sub.get('responses', []):
            name = get_juror_name(resp.get('user', {}))
            if name in jurors:
                juror_ratings[name] = resp.get('rating', '')
                juror_notes[name] = resp.get('notes', '').replace('\n', ' ').strip()
        
        rated_count = sum(1 for j in jurors if juror_ratings[j] != '')
        avg_rating = sub.get('rating', 0)
        
        row = {
            'Artist': sub.get('artist', {}).get('name', 'Unknown'),
            'VI.BE Page': f"https://vi.be/platform/{artist_info.get('slug', '')}",
            'Avg Rating': avg_rating if avg_rating else '',
            'Rated By': f"{rated_count}/{len(jurors)}",
            'Broad Genre': classify_genre(genres, custom_genre),
            'Shortlisted': 'Yes' if sub.get('shortListed', False) else 'No',
            'Email': artist_info.get('email', ''),
            'Phone': normalize_phone(artist_info.get('phone', '')),
            'Location': artist_info.get('location', {}).get('label', ''),
            'Genres': genres,
            'Custom Genre': custom_genre,
        }
        for j in jurors:
            row[f'{j} (Rating)'] = juror_ratings[j]
        for j in jurors:
            row[f'{j} (Notes)'] = juror_notes[j]
        rows.append(row)
    
    rows.sort(key=lambda x: float(x['Avg Rating']) if x['Avg Rating'] else -1, reverse=True)
    return rows, jurors


def write_csv(rows: list, jurors: list, output_path: str):
    fieldnames = ['Artist', 'VI.BE Page', 'Avg Rating', 'Rated By']
    fieldnames += [f'{j} (Rating)' for j in jurors]
    fieldnames += ['Broad Genre', 'Shortlisted']
    fieldnames += [f'{j} (Notes)' for j in jurors]
    fieldnames += ['Email', 'Phone', 'Location', 'Genres', 'Custom Genre']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if len(sys.argv) > 1:
        har_path = sys.argv[1]
    else:
        try:
            har_path = find_har_file(script_dir)
            print(f"Using: {os.path.basename(har_path)}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Usage: python3 extract_submissions.py [har_file]")
            sys.exit(1)
    
    if not os.path.exists(har_path):
        print(f"Error: File not found: {har_path}")
        sys.exit(1)
    
    print("Extracting submissions...")
    submissions = extract_submissions(har_path)
    print(f"Found {len(submissions)} submissions")
    
    if not submissions:
        print("No submissions found in HAR file.")
        sys.exit(1)
    
    rows, jurors = process_submissions(submissions)
    print(f"Jurors: {', '.join(jurors)}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(script_dir, f"busker_submissions_{timestamp}.csv")
    csv_latest = os.path.join(script_dir, "busker_submissions_latest.csv")
    
    write_csv(rows, jurors, csv_path)
    write_csv(rows, jurors, csv_latest)
    
    print(f"\nCreated: {csv_path}")
    print(f"Created: {csv_latest}")
    
    from collections import Counter
    genre_counts = Counter(row['Broad Genre'] for row in rows)
    print("\nBroad Genre Distribution:")
    for genre, count in genre_counts.most_common():
        print(f"  {genre}: {count}")
    
    fully_rated = sum(1 for r in rows if r['Rated By'] == f"{len(jurors)}/{len(jurors)}")
    print(f"\nRating Progress: {fully_rated}/{len(rows)} fully rated")


if __name__ == '__main__':
    main()
