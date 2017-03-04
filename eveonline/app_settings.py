from __future__ import unicode_literals
from django.conf import settings

# set this to control how long API data is cached
OBJ_CACHE_DURATION = int(getattr(settings, 'EVEONLINE_OBJ_CACHE_DURATION', 600))

# set this to alter default data source API
DEFAULT_PROVIDER = getattr(settings, 'EVEONLINE_DEFAULT_PROVIDER', 'esi')
