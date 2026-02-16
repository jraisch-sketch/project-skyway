import json
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

from .models import School

NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'ProjectSkywayGeocoder/1.0 (admin@projectskyway.org)'


def _safe_text(value: Optional[str]) -> str:
    return (value or '').strip()


def build_enrichment_queries(school: School) -> List[str]:
    name = _safe_text(school.name)
    city = _safe_text(school.city)
    state = _safe_text(school.state)
    address = _safe_text(school.address_complete)

    queries: List[str] = []
    if address:
        queries.append(address)
    if name and city and state:
        queries.append(f'{name}, {city}, {state}, USA')
    if name and state:
        queries.append(f'{name}, {state}, USA')
    if name:
        queries.append(f'{name}, college or university, USA')

    # Preserve order but remove duplicates.
    return list(dict.fromkeys(queries))


def nominatim_search(query: str, limit: int = 3, countrycodes: str = 'us') -> List[Dict]:
    params = {
        'q': query,
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': str(limit),
    }
    if countrycodes:
        params['countrycodes'] = countrycodes

    url = f"{NOMINATIM_BASE}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read().decode('utf-8')
    parsed = json.loads(data)
    return parsed if isinstance(parsed, list) else []


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


def score_candidate(school: School, query: str, result: Dict) -> float:
    score = 0.35
    importance = float(result.get('importance', 0) or 0)
    score += min(max(importance, 0.0), 1.0) * 0.30

    name = _safe_text(school.name).lower()
    display_name = _safe_text(result.get('display_name', '')).lower()
    if name and name in display_name:
        score += 0.2

    result_type = _safe_text(result.get('type', '')).lower()
    if result_type in {'college', 'university', 'school'}:
        score += 0.1

    if _state_matches(school.state, result):
        score += 0.1
    else:
        score -= 0.2

    if _city_matches(school.city, result):
        score += 0.05

    if query and query.lower() in display_name:
        score += 0.05

    return max(0.0, min(score, 0.99))


def choose_best_candidate(school: School, query: str, results: List[Dict]) -> Tuple[Optional[Dict], float]:
    if not results:
        return None, 0.0

    best: Optional[Dict] = None
    best_score = 0.0
    for result in results:
        score = score_candidate(school, query, result)
        if score > best_score:
            best = result
            best_score = score

    return best, best_score


def osm_source_url(result: Dict) -> str:
    osm_type = _safe_text(result.get('osm_type'))
    osm_id = _safe_text(str(result.get('osm_id', '') or ''))
    if not osm_type or not osm_id:
        return ''
    first = osm_type[0].lower()
    return f'https://www.openstreetmap.org/{first}/{osm_id}'


def result_city_state_zip(result: Dict) -> Tuple[str, str, str]:
    address = result.get('address', {}) or {}
    city = _safe_text(
        address.get('city')
        or address.get('town')
        or address.get('village')
        or address.get('hamlet')
    )
    state = _safe_text(address.get('state'))
    postcode = _safe_text(address.get('postcode'))

    # If ISO code exists, prefer 2-letter state abbreviation.
    iso = _safe_text(address.get('ISO3166-2-lvl4'))
    if iso.startswith('US-') and len(iso) == 5:
        state = iso[-2:]

    return city, state, postcode


def throttle(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
