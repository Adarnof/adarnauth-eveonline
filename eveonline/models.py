from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import evelink
import requests
from eveonline.endpoints import ALLIANCES
from eveonline.managers import CharacterManager, CorporationManager, AllianceManager

@python_2_unicode_compatible
class BaseEntity(models.Model):
    """
    Abstract base class for EVE Online objects.
    """
    id = models.PositiveIntegerField(unique=True)
    name = models.CharField(unique=True, max_length=254)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Character(BaseEntity):
    """
    Model representing a character from EVE Online
    """
    corp_id = models.PositiveIntegerField(null=True)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    faction_id = models.PositiveIntegerField(null=True, blank=True)
    faction_name = models.CharField(max_length=254, null=True, blank=True)

    objects = CharacterManager()

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

@python_2_unicode_compatible
class Corporation(BaseEntity):
    """
    Model representing a corporation from EVE Online
    """
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    members = models.PositiveIntegerField(help_text="Number of member characters")
    ticker = models.CharField(unique=True, max_length=7)

    objects = CorporationManager()

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

@python_2_unicode_compatible
class Alliance(BaseEntity):
    """
    Model representing an alliance from EVE Online
    """
    ticker = models.CharField(unique=True, max_length=7)

    objects = AllianceManager()

    def update(self, alliance_info=None):
        """
        Update model information from CREST
        """
        if not alliance_info:
            r = requests.get(ALLIANCES % self.id)
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

@python_2_unicode_compatible
class ApiKey(models.Model):
    """
    Model representing an API Key from EVE Online
    """
    TYPE_CHOICES = (
        ('account', 'account'),
        ('character', 'character'),
        ('corp', 'corp'),
        )

    id = models.PositiveIntegerField(unique=True, help_text="API ID")
    vcode = models.CharField(max_length=254, help_text="API Verification Code")
    is_valid = models.NullBooleanField(blank=True)
    access_mask = models.IntegerField(default=0)
    type = models.CharField(max_length=11, choices=TYPE_CHOICES, blank=True)
    characters = models.ManyToManyField(Character, blank=True, related_name='apis')
    corp = models.ForeignKey(Corporation, null=True, blank=True, related_name='apis')

    def __str__(self):
        return 'API Key %s' % self.id

    def validate(self):
        """
        Method to check if API Key is still valid.
        """
        try:
            api = evelink.api.API(api_key=(self.id, self.vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            return True
        except evelink.api.APIError as e:
            if int(e.code) == 403:
                return False
            else:
                raise e

    def update(self):
        """
        Update information about this API key.
        """
        try:
            api = evelink.api.API(api_key=(self.id, self.vcode))
            account = evelink.account.Account(api=api)
            update_fields = []
            key_info = account.key_info().result
            if key_info['type'] != self.type:
                self.type = key_info['type']
                update_fields.append('type')
            if key_info['access_mask'] != self.access_mask:
                self.access_mask = key_info['access_mask']
                update_fields.append('access_mask')
            api_chars = account.characters().result
            for char in self.characters.all():
                if not char.id in api_chars:
                    self.characters.remove(char)
            for api_char_id in api_chars:
                char, c = Character.objects.get_or_create(id=api_char_id)
                if not char in self.characters.all():
                    self.characters.add(char)
            if self.type == 'corp':
                for id in key_info['characters']:
                    corp_id = key_info['characters'][id]['corp']['id']
                    break
                api_corp = evelink.corp.Corp(api=api).corporation_sheet(corp_id=corp_id).result
                corp, c = Corporation.objects.get_or_create(id=corp_id)
                if self.corp != corp:
                    self.corp = corp
                    update_fields.append('corp')
            else:
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
            if not self.is_valid:
                self.is_valid=True
                update_fields.append('is_valid')
            if update_fields:
                self.save(update_fields=update_fields)
        except evelink.api.APIError as e:
            if int(e.code) in [500, 520, 221]:
                raise e
            else:
                update_fields = []
                if self.is_valid or self.is_valid==None:
                    self.is_valid=False
                    update_fields.append('is_valid')
                if self.characters.all().exists():
                    for char in self.characters.all():
                        self.characters.remove(char)
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
                if update_fields:
                    self.save(update_fields=update_fields)
