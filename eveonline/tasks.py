from celery.task import periodic_task
from celery.decorators import task
from eveonline.models import Character, Corporation, Alliance, ApiKey
from datetime import timedelta
import evelink

@task
def update_character(id, char_info):
    """
    Task to update a character with supplied data from
    evelink on a separate thread.
    """
    char = Character.objects.get(id=id)
    char.update(char_info=char_info)

@task
def update_corp(id):
    """
    Task to update a corp on a separate thred.
    """
    corp = Corporation.objects.get(id=id)
    corp.update()

@task
def update_alliance(id, alliance_info):
    """
    Task to update an alliance with supplied data from
    CREST on a separate thread.
    """
    alliance = Alliance.objects.get(id=id)
    alliance.update(alliance_info=alliance_info)

@task
def update_api_key(id):
    """
    Task to update an API key on a separate thread.
    """
    api = ApiKey.objects.get(id=id)
    api.update()

@periodic_task(run_every=timedelta(hours=3))
def update_all_characters():
    """
    Triggers an update of all Character models using
    one API call to get all information.
    """
    char_ids = [c.id for c in Character.objects.all()]
    api = evelink.eve.EVE()
    result = api.affiliations_for_characters(char_ids).result
    for id in result:
        update_character.delay(id, result[id])

@periodic_task(run_every=timedelta(hours=8))
def update_all_corps():
    """
    Triggers an update of all Corporation models.
    """
    corp_ids = [c.id for c in Corporation.objects.all()]
    for id in corp_ids:
        update_corp.delay(id)

@periodic_task(run_every=timedelta(hours=8))
def update_all_alliances():
    """
    Triggers an update of all Alliance models using
    one API call to get all information.
    """
    alliance_ids = [a.id for a in Alliance.objects.all()]
    api = evelink.eve.EVE()
    result = api.alliances().result
    for id in alliance_ids:
        if id in result:
            update_alliance.delay(id, result[id])

@periodic_task(run_every=timedelta(hours=6))
def update_all_api_keys():
    """
    Triggers an update of all Api Key models.
    """
    api_ids = [a.id for a in ApiKey.objects.exclude(is_valid=False)]
    for id in api_ids:
        update_api_key.delay(id)
