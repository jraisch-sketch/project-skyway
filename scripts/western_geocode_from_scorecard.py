#!/usr/bin/env python3
import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'ProjectSkywayWesternGeocoder/1.0 (admin@projectskyway.org)'


def _safe(value: Optional[str]) -> str:
    return (value or '').strip()


def _state_matches(expected_state: str, result: Dict) -> bool:
    if not expected_state:
        return True
    expected = expected_state.strip().lower()
    address = result.get('address', {}) or {}
    iso = (address.get('ISO3166-2-lvl4') or '').lower()
    state_name = (address.get('state') or '').lower()
    if iso.endswith(f'-{expected}'):
        return True
    return expected in state_name


def _city_matches(expected_city: str, result: Dict) -> bool:
    if not expected_city:
        return True
    expected = expected_city.strip().lower()
    address = result.get('address', {}) or {}
    result_city = (
        address.get('city')
        or address.get('town')
        or address.get('village')
        or address.get('hamlet')
        or ''
    ).lower()
    return expected in result_city or result_city in expected


def _build_queries(row: Dict[str, str]) -> List[str]:
    school_name = _safe(row.get('school_name'))
    nces_name = _safe(row.get('nces_name'))
    city = _safe(row.get('city'))
    state = _safe(row.get('state'))
    zip_code = _safe(row.get('zip_code'))

    queries: List[str] = []
    if nces_name and city and state and zip_code:
        queries.append(f'{nces_name}, {city}, {state} {zip_code}, USA')
    if school_name and city and state:
        queries.append(f'{school_name}, {city}, {state}, USA')
    if nces_name and city and state:
        queries.append(f'{nces_name}, {city}, {state}, USA')
    if school_name and state:
        queries.append(f'{school_name}, {state}, USA')
    if nces_name and state:
        queries.append(f'{nces_name}, {state}, USA')

    return list(dict.fromkeys([q for q in queries if q]))


def _nominatim_search(query: str, limit: int, countrycodes: str) -> List[Dict]:
    params = {
        'q': query,
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': str(limit),
    }
    if countrycodes:
        params['countrycodes'] = countrycodes
    url = f"{NOMINATIM_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = response.read().decode('utf-8')
    data = json.loads(payload)
    return data if isinstance(data, list) else []


def _score_candidate(row: Dict[str, str], query: str, result: Dict) -> float:
    score = 0.35
    importance = float(result.get('importance', 0) or 0)
    score += min(max(importance, 0.0), 1.0) * 0.30

    school_name = _safe(row.get('school_name')).lower()
    nces_name = _safe(row.get('nces_name')).lower()
    display_name = _safe(result.get('display_name')).lower()

    if school_name and school_name in display_name:
        score += 0.2
    elif nces_name and nces_name in display_name:
        score += 0.2

    result_type = _safe(result.get('type')).lower()
    if result_type in {'college', 'university', 'school'}:
        score += 0.1

    if _state_matches(_safe(row.get('state')), result):
        score += 0.1
    else:
        score -= 0.2

    if _city_matches(_safe(row.get('city')), result):
        score += 0.05

    if query and query.lower() in display_name:
        score += 0.05

    return max(0.0, min(score, 0.99))


def _choose_best(row: Dict[str, str], query: str, results: List[Dict]) -> Tuple[Optional[Dict], float]:
    best = None
    best_score = 0.0
    for result in results:
        score = _score_candidate(row, query, result)
        if score > best_score:
            best = result
            best_score = score
    return best, best_score


def _source_url(result: Dict) -> str:
    osm_type = _safe(result.get('osm_type'))
    osm_id = _safe(str(result.get('osm_id', '') or ''))
    if not osm_type or not osm_id:
        return ''
    return f'https://www.openstreetmap.org/{osm_type[0].lower()}/{osm_id}'


def _city_state_zip(result: Dict) -> Tuple[str, str, str]:
    address = result.get('address', {}) or {}
    city = _safe(address.get('city') or address.get('town') or address.get('village') or address.get('hamlet'))
    state = _safe(address.get('state'))
    zip_code = _safe(address.get('postcode'))
    iso = _safe(address.get('ISO3166-2-lvl4'))
    if iso.startswith('US-') and len(iso) == 5:
        state = iso[-2:]
    return city, state, zip_code


def run(input_csv: Path, output_csv: Path, review_csv: Path, threshold: float, sleep_s: float, countrycodes: str) -> None:
    with input_csv.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))

    output_rows: List[Dict[str, str]] = []
    review_rows: List[Dict[str, str]] = []

    processed = 0
    geocoded = 0
    failed = 0
    review_count = 0

    for row in rows:
        if _safe(row.get('match_status')) != 'matched':
            continue

        processed += 1
        queries = _build_queries(row)
        best = None
        best_score = 0.0
        best_query = ''

        for query in queries:
            results = _nominatim_search(query=query, limit=3, countrycodes=countrycodes)
            candidate, score = _choose_best(row, query, results)
            if candidate and score > best_score:
                best = candidate
                best_score = score
                best_query = query
            if best_score >= threshold:
                break
            if sleep_s > 0:
                time.sleep(sleep_s)

        if not best:
            failed += 1
            merged = dict(row)
            merged.update(
                {
                    'geocode_status': 'failed',
                    'geocode_confidence': '',
                    'geocode_needs_review': 'true',
                    'geocode_query': '',
                    'geocode_source': 'nominatim',
                    'geocode_source_url': '',
                    'latitude': '',
                    'longitude': '',
                    'geocode_raw': '',
                    'address_complete': '',
                    'geocode_notes': 'No geocode candidate found via Nominatim',
                }
            )
            output_rows.append(merged)
            review_rows.append(merged)
            continue

        city, state, zip_code = _city_state_zip(best)
        needs_review = best_score < threshold
        if needs_review:
            review_count += 1
        else:
            geocoded += 1

        merged = dict(row)
        merged.update(
            {
                'geocode_status': 'review' if needs_review else 'geocoded',
                'geocode_confidence': f'{best_score:.2f}',
                'geocode_needs_review': 'true' if needs_review else 'false',
                'geocode_query': best_query,
                'geocode_source': 'nominatim',
                'geocode_source_url': _source_url(best),
                'latitude': str(best.get('lat', '') or ''),
                'longitude': str(best.get('lon', '') or ''),
                'geocode_raw': f"{best.get('lat', '')}, {best.get('lon', '')}",
                'address_complete': _safe(best.get('display_name')),
                'city': city or _safe(row.get('city')),
                'state': state or _safe(row.get('state')),
                'zip_code': zip_code or _safe(row.get('zip_code')),
                'geocode_notes': 'Coordinates generated from Nominatim',
            }
        )
        output_rows.append(merged)
        if needs_review:
            review_rows.append(merged)

        if sleep_s > 0:
            time.sleep(sleep_s)

    fieldnames = [
        'school_name',
        'contact_email',
        'match_status',
        'match_score',
        'scorecard_id',
        'nces_name',
        'state',
        'city',
        'zip_code',
        'school_website',
        'institution_control',
        'institution_level',
        'locale',
        'enrollment',
        'acceptance_rate',
        'graduation_rate',
        'avg_cost',
        'source_url',
        'notes',
        'geocode_status',
        'geocode_confidence',
        'geocode_needs_review',
        'geocode_query',
        'geocode_source',
        'geocode_source_url',
        'latitude',
        'longitude',
        'geocode_raw',
        'address_complete',
        'geocode_notes',
    ]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    with review_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f'Wrote geocode results: {output_csv}')
    print(f'Wrote needs-review: {review_csv}')
    print(f'Processed matched rows: {processed}')
    print(f'Geocoded (above threshold): {geocoded}')
    print(f'Review: {review_count}')
    print(f'Failed: {failed}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Geocode western conference schools from Scorecard enrichment output.')
    parser.add_argument(
        '--input-csv',
        default='data/western_conference/western_scorecard_enrichment_latest.csv',
    )
    parser.add_argument('--output-csv', default='')
    parser.add_argument('--review-csv', default='')
    parser.add_argument('--threshold', type=float, default=0.75)
    parser.add_argument('--sleep', type=float, default=1.0)
    parser.add_argument('--countrycodes', default='us')
    args = parser.parse_args()

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_csv = args.output_csv or f'data/western_conference/western_geocode_results_{ts}.csv'
    review_csv = args.review_csv or f'data/western_conference/western_geocode_needs_review_{ts}.csv'

    run(
        input_csv=Path(args.input_csv),
        output_csv=Path(output_csv),
        review_csv=Path(review_csv),
        threshold=args.threshold,
        sleep_s=args.sleep,
        countrycodes=args.countrycodes,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
