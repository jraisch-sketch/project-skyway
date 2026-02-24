import json
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Dict, Iterator, List, Tuple

NCES_LAYER_URL = (
    'https://nces.ed.gov/opengis/rest/services/'
    'Postsecondary_School_Locations/EDGE_GEOCODE_POSTSECONDARYSCH_2223/MapServer/0'
)

_USER_AGENT = 'ProjectSkywayNCESImporter/1.0 (admin@projectskyway.org)'
NCES_DEFAULT_OUT_FIELDS = 'UNITID,NAME,STREET,CITY,STATE,ZIP,LAT,LON,SCHOOLYEAR'

_STOPWORDS = {
    'the',
    'of',
    'at',
    'for',
    'and',
    'university',
    'college',
    'school',
    'campus',
    'state',
    'community',
    'institute',
}


def normalize_name(value: str) -> str:
    value = (value or '').lower()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    tokens = [t for t in value.split() if t and t not in _STOPWORDS]
    return ' '.join(tokens)


def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def _query_url(base_url: str, params: Dict[str, str]) -> str:
    return f"{base_url}/query?{urllib.parse.urlencode(params)}"


def fetch_nces_records(
    base_url: str = NCES_LAYER_URL,
    page_size: int = 1000,
    sleep_seconds: float = 0.2,
    max_retries: int = 3,
    out_fields: str = NCES_DEFAULT_OUT_FIELDS,
) -> Iterator[Dict]:
    offset = 0

    while True:
        params = {
            'where': '1=1',
            'outFields': out_fields,
            'returnGeometry': 'false',
            'f': 'json',
            'resultOffset': str(offset),
            'resultRecordCount': str(page_size),
            'orderByFields': 'OBJECTID',
        }
        url = _query_url(base_url, params)

        payload = None
        last_error = None
        for _ in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
                with urllib.request.urlopen(req, timeout=45) as response:
                    payload = json.loads(response.read().decode('utf-8'))
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.0)

        if payload is None:
            raise RuntimeError(f'Failed to fetch NCES page at offset={offset}: {last_error}')

        features = payload.get('features', []) or []
        if not features:
            break

        for feature in features:
            attrs = feature.get('attributes', {}) or {}
            yield attrs

        offset += len(features)
        if len(features) < page_size:
            break
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)


def fetch_nces_layer_fields(
    base_url: str = NCES_LAYER_URL,
    max_retries: int = 3,
) -> List[Dict]:
    params = {'f': 'json'}
    url = f'{base_url}?{urllib.parse.urlencode(params)}'

    payload = None
    last_error = None
    for _ in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as response:
                payload = json.loads(response.read().decode('utf-8'))
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1.0)

    if payload is None:
        raise RuntimeError(f'Failed to fetch NCES layer metadata: {last_error}')

    fields = payload.get('fields', []) or []
    return fields


def clean_state(value: str) -> str:
    return (value or '').strip().upper()


def clean_zip(value: str) -> str:
    value = (value or '').strip()
    if not value:
        return ''
    return value[:5]


def full_address(street: str, city: str, state: str, zip_code: str) -> str:
    parts: List[str] = []
    street = (street or '').strip()
    city = (city or '').strip()
    state = clean_state(state)
    zip_code = clean_zip(zip_code)

    if street:
        parts.append(street)

    locality = ', '.join([p for p in [city, state] if p])
    if locality:
        parts.append(locality)
    if zip_code:
        parts.append(zip_code)

    if parts:
        parts.append('USA')
    return ', '.join(parts)


def choose_school_match(
    nces_record: Dict,
    schools_by_unitid: Dict[str, object],
    schools_by_state_norm: Dict[Tuple[str, str], List[object]],
    schools_by_norm: Dict[str, List[object]],
    schools_by_state: Dict[str, List[object]],
    schools_all: List[object],
) -> Tuple[object, float, str]:
    unitid = str(nces_record.get('UNITID') or '').strip()
    name = str(nces_record.get('NAME') or '').strip()
    state = clean_state(str(nces_record.get('STATE') or ''))
    norm = normalize_name(name)

    if unitid and unitid in schools_by_unitid:
        return schools_by_unitid[unitid], 1.0, 'unitid'

    direct_candidates = schools_by_state_norm.get((state, norm), [])
    if len(direct_candidates) == 1:
        return direct_candidates[0], 0.99, 'exact_state_name'

    fallback_candidates = schools_by_norm.get(norm, [])
    if len(fallback_candidates) == 1:
        candidate = fallback_candidates[0]
        score = 0.9
        if clean_state(getattr(candidate, 'state', '')) == state:
            score += 0.05
        return candidate, min(score, 0.99), 'exact_name'

    candidates = direct_candidates or fallback_candidates
    if not candidates and state:
        candidates = schools_by_state.get(state, [])
    if not candidates:
        # Last resort for unknown state entries.
        candidates = schools_all
    if not candidates:
        return None, 0.0, 'none'

    scored = []
    for candidate in candidates:
        base = name_similarity(name, getattr(candidate, 'name', ''))
        if state and clean_state(getattr(candidate, 'state', '')) == state:
            base += 0.08
        scored.append((candidate, min(base, 0.99)))

    scored.sort(key=lambda item: item[1], reverse=True)
    best, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    if best_score - second_score < 0.03:
        return None, best_score, 'ambiguous'

    return best, best_score, 'fuzzy'
