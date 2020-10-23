import json
import logging
import os

from cirruslib import Catalog, Catalogs
from cirruslib.utils import dict_merge

# configure logger - CRITICAL, ERROR, WARNING, INFO, DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('CIRRUS_LOG_LEVEL', 'INFO'))

# Default PROCESSES
with open(os.path.join(os.path.dirname(__file__), 'processes.json')) as f:
    PROCESSES = json.loads(f.read())


def lambda_handler(payload, context):    
    # Read SQS payload
    if 'Records' not in payload:
        raise ValueError("Input not from SQS")
    
    catalogs = []
    for cat in [json.loads(r['body']) for r in payload['Records']]:
        # expand catids to full catalogs
        if 'catids' in cat:
            _cats = Catalogs.from_catids(cat['catids'])
            if 'process_update' in cat:
                logger.debug(f"Process update: {json.dumps(cat['process_update'])}")
                for c in _cats:
                    c['process'] = dict_merge(c['process'], cat['process_update'])
            catalogs += _cats

        # If Item, create Catalog and use default process for that collection
        if cat.get('type', '') == 'Feature':
            if cat['collection'] not in PROCESSES.keys():
                raise ValueError(f"Default process not provided for collection {cat['collection']}")
            cat_json = {
                'type': 'FeatureCollection',
                'features': [cat],
                'process': PROCESSES[cat['collection']]
            }
            catalogs.append(Catalog(cat_json, update=True))
    
    if len(catalogs) > 0:
        catalogs.process()

    return len(catalogs)
