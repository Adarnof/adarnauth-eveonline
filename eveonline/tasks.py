from celery.task import periodic_task
from celery import shared_task
from eveonline.models import Character, Corporation, Alliance
from eveonline.providers import eve_provider_factory
from datetime import timedelta


@shared_task
def update_character(obj_id, provider=None):
    """
    Updates a given character model asynchronously
    :param obj_id: Alliance ID to update
    :param provider: :class:`eveonline.provders.EveProvider`
    """
    char = Character.objects.get(id=obj_id)
    char.update(provider=provider)


@shared_task
def update_corporation(obj_id, provider=None):
    """
    Updates a given corporation model asynchronously
    :param obj_id: Alliance ID to update
    :param provider: :class:`eveonline.provders.EveProvider`
    """
    corp = Corporation.objects.get(id=obj_id)
    corp.update(provider=provider)


@shared_task
def update_alliance(obj_id, provider=None):
    """
    Updates a given alliance model asynchronously
    :param obj_id: Alliance ID to update
    :param provider: :class:`eveonline.provders.EveProvider`
    """
    alliance = Alliance.objects.get(id=obj_id)
    alliance.update(provider=provider)


@periodic_task(run_every=timedelta(hours=3))
def update_all_characters():
    """
    Triggers an update of all Character models
    """
    char_ids = [c.id for c in Character.objects.all()]
    provider = eve_provider_factory()
    for obj_id in char_ids:
        update_character.delay(obj_id, provider=provider)


@periodic_task(run_every=timedelta(hours=8))
def update_all_corps():
    """
    Triggers an update of all Corporation models
    """
    corp_ids = [c.id for c in Corporation.objects.all()]
    provider = eve_provider_factory()
    for obj_id in corp_ids:
        update_corporation.delay(obj_id, provider=provider)


@shared_task  # data only changes very rarely on CCP intervention, don't queue periodically
def update_all_alliances():
    """
    Triggers an update of all Alliance models
    """
    alliance_ids = [a.id for a in Alliance.objects.all()]
    provider = eve_provider_factory()
    for obj_id in alliance_ids:
        update_alliance.delay(obj_id, provider=provider)
