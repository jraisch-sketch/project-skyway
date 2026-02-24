import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from typing import Dict, Optional

SCORECARD_API_URL = 'https://api.data.gov/ed/collegescorecard/v1/schools'
SCORECARD_DEFAULT_FIELDS = (
    'id,school.name,school.state,school.ownership,school.locale,school.degrees_awarded.predominant,'
    'latest.student.size,latest.admissions.admission_rate.overall,latest.completion.rate_4yr_150nt,'
    'latest.completion.rate_150nt_4yr,latest.completion.completion_rate_4yr_150nt'
)

_USER_AGENT = 'ProjectSkywayScorecardEnricher/1.0 (admin@projectskyway.org)'


def fetch_scorecard_school(
    unitid: str,
    api_key: str,
    base_url: str = SCORECARD_API_URL,
    fields: str = SCORECARD_DEFAULT_FIELDS,
    max_retries: int = 3,
    retry_sleep_seconds: float = 1.0,
) -> Optional[Dict]:
    params = {
        'api_key': api_key,
        'id': str(unitid).strip(),
        'fields': fields,
        'per_page': 1,
    }
    url = f'{base_url}?{urllib.parse.urlencode(params)}'

    payload = None
    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as response:
                payload = json.loads(response.read().decode('utf-8'))
            break
        except HTTPError as exc:
            last_error = exc
            if exc.code == 429 and attempt < max_retries - 1:
                # Respect rate limits with exponential backoff.
                time.sleep(retry_sleep_seconds * (2 ** attempt))
                continue
            time.sleep(retry_sleep_seconds)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(retry_sleep_seconds)

    if payload is None:
        raise RuntimeError(f'Failed to fetch College Scorecard record for UNITID={unitid}: {last_error}')

    results = payload.get('results', []) or []
    if not results:
        return None
    return results[0]
