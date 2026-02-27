#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError

SCORECARD_API_URL = 'https://api.data.gov/ed/collegescorecard/v1/schools'
FIELDS = (
    'id,school.name,school.alias,school.city,school.state,school.zip,school.school_url,school.ownership,school.locale,'
    'school.degrees_awarded.predominant,latest.student.size,latest.admissions.admission_rate.overall,'
    'latest.completion.rate_4yr_150nt,latest.completion.rate_150nt_4yr,latest.completion.completion_rate_4yr_150nt,'
    'latest.cost.avg_net_price.overall'
)

LOCALE_CODE_MAP = {
    '11': 'City: Large',
    '12': 'City: Midsize',
    '13': 'City: Small',
    '21': 'Suburb: Large',
    '22': 'Suburb: Midsize',
    '23': 'Suburb: Small',
    '31': 'Town: Fringe',
    '32': 'Town: Distant',
    '33': 'Town: Remote',
    '41': 'Rural: Fringe',
    '42': 'Rural: Distant',
    '43': 'Rural: Remote',
}

STATE_HINTS = {
    'University of Nevada-Reno': 'NV',
}


def _normalize(text: str) -> str:
    raw = (text or '').lower()
    raw = raw.replace("'s", "s")
    return re.sub(r'[^a-z0-9]+', ' ', raw).strip()


def _tokens(text: str) -> List[str]:
    return [t for t in _normalize(text).split() if t]


def _map_institution_control(value) -> str:
    text = str(value or '').strip().lower()
    if not text:
        return 'unknown'
    if text in {'1', 'public'} or 'public' in text:
        return 'public'
    if text in {'2'} or 'nonprofit' in text or 'non-profit' in text:
        return 'private_nonprofit'
    if text in {'3'} or 'for-profit' in text or 'for profit' in text:
        return 'private_for_profit'
    return 'unknown'


def _map_institution_level(value) -> str:
    text = str(value or '').strip().lower()
    if not text:
        return 'unknown'
    if text in {'3', '4'}:
        return 'four_year'
    if text in {'2'}:
        return 'two_year'
    if text in {'1'}:
        return 'less_than_two_year'
    return 'unknown'


def _map_locale(value) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    return LOCALE_CODE_MAP.get(text, text)


def _format_integerish(value) -> str:
    if value is None or value == '':
        return ''
    try:
        parsed = float(value)
    except ValueError:
        return str(value)
    if parsed < 0:
        return ''
    return f'{int(round(parsed)):,}'


def _format_percent(value) -> str:
    if value is None or value == '':
        return ''
    try:
        parsed = float(value)
    except ValueError:
        return str(value)
    if parsed < 0:
        return ''
    if parsed <= 1:
        parsed *= 100
    return f'{parsed:.1f}%'


def _extract(record: Dict, dotted: str):
    if dotted in record and record[dotted] is not None:
        return record[dotted]
    current = record
    for segment in dotted.split('.'):
        if not isinstance(current, dict):
            return None
        if segment not in current:
            return None
        current = current[segment]
    return current


def _fetch_candidates(school_name: str, api_key: str, per_page: int, retries: int, sleep_s: float) -> List[Dict]:
    params = {
        'api_key': api_key,
        'fields': FIELDS,
        'school.name': school_name,
        'per_page': str(per_page),
    }
    url = f"{SCORECARD_API_URL}?{urllib.parse.urlencode(params)}"

    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ProjectSkywayWesternEnricher/1.0'})
            with urllib.request.urlopen(req, timeout=45) as response:
                payload = json.loads(response.read().decode('utf-8'))
                return payload.get('results', []) or []
        except HTTPError as exc:
            last_error = exc
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(sleep_s * (2 ** attempt))
                continue
            time.sleep(sleep_s)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(sleep_s)
    raise RuntimeError(f'Failed to query Scorecard for "{school_name}": {last_error}')


def _match_score(input_name: str, result: Dict, expected_state: str) -> float:
    target = _normalize(input_name)
    candidate_name = str(_extract(result, 'school.name') or '')
    candidate_alias = str(_extract(result, 'school.alias') or '')

    candidate_norm = _normalize(candidate_name)
    alias_norm = _normalize(candidate_alias)

    if candidate_norm == target or alias_norm == target:
        base = 1.0
    else:
        input_tokens = set(_tokens(input_name))
        best_tokens = set(_tokens(candidate_name))
        if alias_norm:
            alias_tokens = set(_tokens(candidate_alias))
            if len(alias_tokens & input_tokens) > len(best_tokens & input_tokens):
                best_tokens = alias_tokens
        if not input_tokens:
            base = 0.0
        else:
            overlap = input_tokens & best_tokens
            union = input_tokens | best_tokens
            containment = len(overlap) / len(input_tokens)
            jaccard = (len(overlap) / len(union)) if union else 0.0
            base = (containment * 0.7) + (jaccard * 0.3)

    state = str(_extract(result, 'school.state') or '').strip().upper()
    if expected_state and state == expected_state:
        base += 0.1

    return min(base, 1.0)


def _expected_state(school_name: str) -> str:
    if school_name in STATE_HINTS:
        return STATE_HINTS[school_name]
    return 'CA'


def _rank_tuple(input_name: str, result: Dict, expected_state: str):
    target = _normalize(input_name)
    candidate_name = str(_extract(result, 'school.name') or '')
    candidate_alias = str(_extract(result, 'school.alias') or '')
    candidate_norm = _normalize(candidate_name)
    alias_norm = _normalize(candidate_alias)
    exact = 1 if (candidate_norm == target or alias_norm == target) else 0
    state = str(_extract(result, 'school.state') or '').strip().upper()
    state_match = 1 if expected_state and state == expected_state else 0
    score = _match_score(input_name, result, expected_state)
    length_delta = abs(len(_tokens(candidate_name)) - len(_tokens(input_name)))
    return (exact, state_match, score, -length_delta)


def run(input_csv: Path, output_csv: Path, api_key: str, min_score: float, per_page: int, sleep_s: float) -> None:
    rows: List[Dict[str, str]] = []
    with input_csv.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    output_rows = []
    matched = 0
    unmatched = 0
    failed = 0

    for row in rows:
        school_name = (row.get('school_name') or '').strip()
        contact_email = (row.get('contact_email') or '').strip().lower()
        expected_state = _expected_state(school_name)

        try:
            candidates = _fetch_candidates(
                school_name=school_name,
                api_key=api_key,
                per_page=per_page,
                retries=4,
                sleep_s=sleep_s,
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            output_rows.append(
                {
                    'school_name': school_name,
                    'contact_email': contact_email,
                    'match_status': 'error',
                    'match_score': '',
                    'scorecard_id': '',
                    'nces_name': '',
                    'state': '',
                    'city': '',
                    'zip_code': '',
                    'school_website': '',
                    'institution_control': '',
                    'institution_level': '',
                    'locale': '',
                    'enrollment': '',
                    'acceptance_rate': '',
                    'graduation_rate': '',
                    'avg_cost': '',
                    'source_url': '',
                    'notes': str(exc),
                }
            )
            continue

        if not candidates:
            unmatched += 1
            output_rows.append(
                {
                    'school_name': school_name,
                    'contact_email': contact_email,
                    'match_status': 'unmatched',
                    'match_score': '',
                    'scorecard_id': '',
                    'nces_name': '',
                    'state': '',
                    'city': '',
                    'zip_code': '',
                    'school_website': '',
                    'institution_control': '',
                    'institution_level': '',
                    'locale': '',
                    'enrollment': '',
                    'acceptance_rate': '',
                    'graduation_rate': '',
                    'avg_cost': '',
                    'source_url': '',
                    'notes': 'No Scorecard candidates returned',
                }
            )
            continue

        ranked = sorted(
            candidates,
            key=lambda c: _rank_tuple(school_name, c, expected_state),
            reverse=True,
        )
        best = ranked[0]
        score = _match_score(school_name, best, expected_state)

        if score < min_score:
            unmatched += 1
            output_rows.append(
                {
                    'school_name': school_name,
                    'contact_email': contact_email,
                    'match_status': 'needs_review',
                    'match_score': f'{score:.2f}',
                    'scorecard_id': str(_extract(best, 'id') or ''),
                    'nces_name': str(_extract(best, 'school.name') or ''),
                    'state': str(_extract(best, 'school.state') or ''),
                    'city': str(_extract(best, 'school.city') or ''),
                    'zip_code': str(_extract(best, 'school.zip') or ''),
                    'school_website': str(_extract(best, 'school.school_url') or ''),
                    'institution_control': _map_institution_control(_extract(best, 'school.ownership')),
                    'institution_level': _map_institution_level(_extract(best, 'school.degrees_awarded.predominant')),
                    'locale': _map_locale(_extract(best, 'school.locale')),
                    'enrollment': _format_integerish(_extract(best, 'latest.student.size')),
                    'acceptance_rate': _format_percent(_extract(best, 'latest.admissions.admission_rate.overall')),
                    'graduation_rate': _format_percent(
                        _extract(best, 'latest.completion.rate_4yr_150nt')
                        or _extract(best, 'latest.completion.rate_150nt_4yr')
                        or _extract(best, 'latest.completion.completion_rate_4yr_150nt')
                    ),
                    'avg_cost': _format_integerish(_extract(best, 'latest.cost.avg_net_price.overall')),
                    'source_url': f'https://api.data.gov/ed/collegescorecard/v1/schools?id={_extract(best, "id")}',
                    'notes': 'Best candidate below threshold',
                }
            )
            continue

        matched += 1
        output_rows.append(
            {
                'school_name': school_name,
                'contact_email': contact_email,
                'match_status': 'matched',
                'match_score': f'{score:.2f}',
                'scorecard_id': str(_extract(best, 'id') or ''),
                'nces_name': str(_extract(best, 'school.name') or ''),
                'state': str(_extract(best, 'school.state') or ''),
                'city': str(_extract(best, 'school.city') or ''),
                'zip_code': str(_extract(best, 'school.zip') or ''),
                'school_website': str(_extract(best, 'school.school_url') or ''),
                'institution_control': _map_institution_control(_extract(best, 'school.ownership')),
                'institution_level': _map_institution_level(_extract(best, 'school.degrees_awarded.predominant')),
                'locale': _map_locale(_extract(best, 'school.locale')),
                'enrollment': _format_integerish(_extract(best, 'latest.student.size')),
                'acceptance_rate': _format_percent(_extract(best, 'latest.admissions.admission_rate.overall')),
                'graduation_rate': _format_percent(
                    _extract(best, 'latest.completion.rate_4yr_150nt')
                    or _extract(best, 'latest.completion.rate_150nt_4yr')
                    or _extract(best, 'latest.completion.completion_rate_4yr_150nt')
                ),
                'avg_cost': _format_integerish(_extract(best, 'latest.cost.avg_net_price.overall')),
                'source_url': f'https://api.data.gov/ed/collegescorecard/v1/schools?id={_extract(best, "id")}',
                'notes': '',
            }
        )

        if sleep_s > 0:
            time.sleep(sleep_s)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as fh:
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
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f'Wrote: {output_csv}')
    print(f'Matched: {matched}')
    print(f'Unmatched/Needs review: {unmatched}')
    print(f'Errors: {failed}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Enrich western conference seed schools with Scorecard non-cycling fields.')
    parser.add_argument(
        '--input-csv',
        default='data/western_conference/western_conference_contacts.csv',
        help='Input CSV with school_name/contact_email columns.',
    )
    parser.add_argument(
        '--output-csv',
        default='',
        help='Output CSV path. Defaults to data/western_conference/western_scorecard_enrichment_<timestamp>.csv',
    )
    parser.add_argument('--api-key', default=os.getenv('COLLEGE_SCORECARD_API_KEY', 'DEMO_KEY'))
    parser.add_argument('--min-score', type=float, default=0.65)
    parser.add_argument('--per-page', type=int, default=20)
    parser.add_argument('--sleep', type=float, default=0.15)
    args = parser.parse_args()

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_csv = args.output_csv or f'data/western_conference/western_scorecard_enrichment_{ts}.csv'

    run(
        input_csv=Path(args.input_csv),
        output_csv=Path(output_csv),
        api_key=args.api_key,
        min_score=args.min_score,
        per_page=args.per_page,
        sleep_s=args.sleep,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
