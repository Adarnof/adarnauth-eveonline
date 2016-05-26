from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import evelink
import requests

@python_2_unicode_compatible
class BaseEVEEntity(models.Model):
    id = models.PositiveIntegerField(unique=True)
    name = models.CharField(unique=True, max_length=254)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class EVECharacter(BaseEVEEntity):
    corp_id = models.PositiveIntegerField(null=True)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    faction_id = models.PositiveIntegerField(null=True, blank=True)
    faction_name = models.CharField(max_length=254, null=True, blank=True)

    def update(self, char_info=None):
        """
        Update model information from EVE API
        """
        if not char_info:
            api = evelink.eve.EVE()
            result = api.affiliations_for_characters(self.id).result
            if not self.id in result:
                raise ValueError("evelink result does not contain character information.")
            else:
                char_info = result[self.id]
        if (not 'name' in char_info) or (not 'id' in char_info) or (not 'corp' in char_info):
            raise ValueError("Passed char_info missing required fields for updating character.")
        if not char_info['name']:
            raise KeyError("Received empty response from evelink for character update.")
        if self.id != char_info['id']:
            raise ValueError("Received api result for different character id.")
        update_fields = []
        if self.name != char_info['name']:
            self.name = char_info['name']
            update_fields.append('name')
        if self.corp_id != char_info['corp']['id']:
            self.corp_id = char_info['corp']['id']
            update_fields.append('corp_id')
        if self.corp_name != char_info['corp']['name']:
            self.corp_name = char_info['corp']['name']
            update_fields.append('corp_name')
        if 'faction' in char_info:
            if self.faction_id != char_info['faction']['id']:
                self.faction_id = char_info['faction']['id']
                update_fields.append('faction_id')
            if self.faction_name != char_info['faction']['name']:
                self.faction_name = char_info['faction']['name']
                update_fields.append('faction_name')
        else:
            if self.faction_id:
                self.faction_id = None
                update_fields.append('faction_id')
            if self.faction_name:
                self.faction_name = None
                update_fields.append('faction_name')
        if 'alliance' in char_info:
            if self.alliance_id != char_info['alliance']['id']:
                self.alliance_id = char_info['alliance']['id']
                update_fields.append('alliance_id')
            if self.alliance_name != char_info['alliance']['name']:
                self.alliance_name = char_info['alliance']['name']
                update_fields.append('alliance_name')
        else:
            if self.alliance_id:
                self.alliance_id = None
                update_fields.append('alliance_id')
            if self.alliance_name:
                self.alliance_name = None
                update_fields.append('alliance_name')
        if update_fields:
            self.save(update_fields=update_fields)

class EVECorporation(BaseEVEEntity):
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    members = models.PositiveIntegerField()
    ticker = models.CharField(unique=True, max_length=7)

    def update(self, result=None):
        """
        Update model information from EVE API
        """
        if not result:
            a = evelink.api.API()
            api = evelink.corp.Corp(a)
            result = api.corporation_sheet(corp_id=self.id).result
        if (not 'name' in result) or (not 'alliance' in result) or (not 'members' in result) or (not 'ticker' in result):
            raise ValueError("Passed corp result missing required fields for corp update.")
        if self.id != result['id']:
            raise ValueError("Received api result for different corp id.")
        update_fields = []
        if self.name != result['name']:
            self.name = result['name']
            update_fields.append('name')
        if self.alliance_id != result['alliance']['id']:
            self.alliance_id = result['alliance']['id']
            update_fields.append('alliance_id')
        if self.alliance_name != result['alliance']['name']:
            self.alliance_name = result['alliance']['name']
            update_fields.append('alliance_name')
        if self.members != result['members']['current']:
            self.members = result['members']['current']
            update_fields.append('members')
        if self.ticker != result['ticker']:
            self.ticker = result['ticker']
            update_fields.append('ticker')
        if update_fields:
            self.save(update_fields=update_fields)

class EVEAlliance(BaseEVEEntity):
    ticker = models.CharField(unique=True, max_length=7)

    def update(self, alliance_info=None):
        """
        Update model information from EVE API
        """
        if not alliance_info:
            r = requests.get(self.CREST_ALLIANCE_ENDPOINT % self.id)
            r.raise_for_status()
            alliance_info = r.json()
        update_fields=[]
        if self.name != alliance_info['name']:
            self.name = alliance_info['name']
            update_fields.append('name')
        if self.ticker != alliance_info['shortName']:
            self.ticker = alliance_info['shortName']
            update_fields.append('ticker')
        if update_fields:
            self.save(update_fields=update_fields)
