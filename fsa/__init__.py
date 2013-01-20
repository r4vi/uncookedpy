import requests
from difflib import SequenceMatcher
from operator import itemgetter

DEFAULT_PARAMS = {'page': 1,
                  'format':'json',
                  'lang': 'en-GB', # fuck welsh
                  'sort':'DISTANCE',
                  'businesstype': 0, # all
                  'name': '%5e'}
BASE_URL = "http://ratings.food.gov.uk/enhanced-search/en-GB/{name}/%5e/{sort}/{businesstype}/%5e/{lng}/{lat}/1/30/{format}"

def _simple_result(ecoll_item, name=None):
    ret = {
        'name': ecoll_item.get('BusinessName'),
        'rating': ecoll_item.get('RatingValue'),
        'date': ecoll_item.get('RatingDate'),
        }
    if name:
        ret['perc_match'] = SequenceMatcher(None, name.lower(), ret['name'].lower()).ratio()
    return ret

def get_match(lat, lng, name=None):
    query = DEFAULT_PARAMS.copy()
    query_params = {
            'lat':lat,
            'lng':lng
            }
    if name:
        partial_name = name.split()[0].lower()
        query_params['name'] = partial_name #speedup
    query.update(query_params)
    url = BASE_URL.format(**query)
    resp = requests.get(url)
    if resp.ok:
        results = resp.json()
        establishments = results.get('FHRSEstablishment')
        if establishments:
            hdr = establishments.get('Header')
            if hdr:
                count = hdr.get('ItemCount',0)
                count = int(count)
                if count:
                    # find best match
                    ecoll = establishments.get('EstablishmentCollection')
                    # fucking xml shit
                    ecoll = ecoll.get('EstablishmentDetail')
                    if not name:
                        return _simple_result(ecoll[0])
                    else:
                        ecoll = sorted([_simple_result(x, name) for x in ecoll], key=itemgetter('perc_match'), reverse=True)
                        ecoll = [x for x in ecoll if x['perc_match'] > 0.8]
                        if ecoll:
                            return ecoll[0]


