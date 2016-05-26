from __future__ import unicode_literals
from django.db import models
import evelink
import requests
from eveonline.endpoints import ALLIANCES

DOOMHEIM_CORP_ID = 1000001

class BaseManager(models.Manager):
    class Meta:
        abstract = True

    def check_id(self, id):
        """
        Verifies supplied ID is valid.
        """
        return False

    def create(self, *args, **kwargs):
        """
        Ensures supplied ID is valid before creation.
        Overwrites supplied fields if differing from EVE Online
        """
        if not self.check_id(model.id):
            raise ValueError("Supplied ID is invalid")
        model = super(BaseManager, self).create(*args, **kwargs)
        model.update()
        return model

class CharacterManager(BaseManager):
    def check_id(self, id):
        """
        Ensures character is real and is still alive.
        """
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(id).result[id]
        if result['name']:
            if result['corp']['id'] == DOOMHEIM_CORP_ID:
                # character has been biomassed
                return False
            else:
                return True
        else:
            return False

class CorporationManager(BaseManager):
    def check_id(self, id):
         """
         Ensures corporation is real and has not closed.
         """
         try:
            a = evelink.api.API()
            api = evelink.corp.Corp(a)
            result = api.corporation_sheet(corp_id=id).result
            return True
        except evelink.api.APIError as e:
            if int(e.code) == 523:
                # corp has been closed
                return False
            else:
                raise e

class AllianceManager(BaseManager):
    def check_id(self, id):
        """
        Ensures alliance is real and has not closed.
        """
        r = requests.get(ALLIANCES % id)
        if r.status_code == 200:
            return True
        elif r.status_code == 403:
            return False
        else:
            e = evelink.api.APIError()
            e.code = r.status_code
            e.message = "Unexpected CREST error occured"
            e.expires = None
            e.timestamp = datetime.datetime.utcnow()
            raise e
