from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core import validators
import evelink
from eveonline.managers import CharacterManager, CorporationManager, AllianceManager
from eveonline.providers import eve_provider_factory, ObjectNotFound, Character as ProviderCharacter, \
    Corporation as ProviderCorporation, Alliance as ProviderAlliance, ItemType as ProviderItemType


class EveEntityValidator(validators.BaseValidator):
    """
    Ensures provided ID is valid for expected EVE entity type
    """
    def compare(self, obj_id, expected_type):
        try:
            return bool(getattr(eve_provider_factory(), 'get_%s' % expected_type.__class__.__name__.lower())(obj_id))
        except ObjectNotFound:
            return False

    def clean(self, obj):
        return obj.id


class EveEntityField(models.BigIntegerField):
    """
    Abstract superclass for EVE Item storage
    Subclasses must override the object class
    """

    object_class = None

    @classmethod
    def _get_object(cls, object_id):
        return getattr(eve_provider_factory(), 'get_%s' % cls.object_class.__class__.__name__.lower())(object_id)

    @property
    def validators(self):
        return super(EveEntityField, self).validators.append(
            [validators.MinValueValidator(1), EveEntityValidator(self.object_class)])

    def from_db_value(self, value, *args):
        if value is None:
            return value
        return self._get_object(value)

    def to_python(self, value):
        if isinstance(value, self.object_class):
            return value
        elif value is None:
            return None
        else:
            return self._get_object(value)


class CharacterField(EveEntityField):
    object_class = ProviderCharacter


class CorporationField(EveEntityField):
    object_class = ProviderCorporation


class AllianceField(EveEntityField):
    object_class = ProviderAlliance


class ItemTypeField(EveEntityField):
    object_class = ProviderItemType


class CharacterSnapshotMixin:
    """
    Provides pseudo-FK behaviour to external API character data
    Snapshots character_id and provides a character property
    """
    _character_id = models.PositiveIntegerField()

    @property
    def character(self):
        try:
            return eve_provider_factory().get_character(self._character_id)
        except ObjectNotFound:
            return None

    @character.setter
    def character(self, obj):
        self._character_id = obj.id


class CorpSnapshotMixin:
    """
    Provides pseudo-FK behaviour to external API corp data
    Snapshots corp_id and provides a corp property
    """
    _corp_id = models.PositiveIntegerField()

    @property
    def corp(self):
        try:
            return eve_provider_factory().get_corp(self._corp_id)
        except ObjectNotFound:
            return None

    @corp.setter
    def corp(self, obj):
        self._corp_id = obj.id


class AllianceSnapshotMixin:
    """
    Provides pseudo-FK behaviour to external API alliance data
    Snapshots alliance_id and provides a alliance property
    """
    _alliance_id = models.PositiveIntegerField()

    @property
    def alliance(self):
        try:
            return eve_provider_factory().get_alliance(self._alliance_id)
        except ObjectNotFound:
            return None

    @alliance.setter
    def alliance(self, obj):
        self._alliance_id = obj.id


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

    @classmethod
    def from_provider_obj(cls, obj):
        """
        Pulls data from a provider object and maps it to model attributes
        :param obj: :class:`eveonline.providers.Entity` or subclass
        :return: :class:`eveonline.models.BaseEntity` or subclass
        """
        fields = [field.name for field in cls._meta.fields]
        values = {}
        for f in fields:
            # iterate over field names and get data from object
            chain = f.split('_')
            if len(chain) == 1:
                # this is likely id or name, don't need to follow properties
                values[f] = getattr(obj, chain[0])
            else:
                # this is likely a nested attribute, such as corp_name -> corp.name
                # get the corp/alliance property, then get the id/name property of it
                values[f] = getattr(getattr(obj, chain[0]), chain[1])
        return cls(**values)

    def update(self, provider=None):
        """
        Updates the corp/alliance info from external source
        :param provider: :class:`eveonline.providers.EveProvider`
        :return: :class:`eveonline.models.BaseEntity` or subclass
        """
        provider = provider or eve_provider_factory()
        self = self.from_provider_obj(provider.get_character(self.id))
        self.save()
        return self


@python_2_unicode_compatible
class Character(BaseEntity):
    """
    Model representing a character from EVE Online
    """
    corp_id = models.PositiveIntegerField()
    corp_name = models.CharField(max_length=30)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=30, null=True, blank=True)

    objects = CharacterManager()

    @classmethod
    def from_provider_obj(cls, char):
        """
        Converts a provider-returned object to a django model
        :param char: :class:`eveonline.providers.Character`
        :return: :class:`eveonline.models.Character`
        """
        return cls(
            id=char.id,
            name=char.name,
            corp_id=char.corp.id,
            corp_name=char.corp.name,
            alliance_id=char.alliance.id,
            alliance_name=char.alliance.name,
        )


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


@python_2_unicode_compatible
class Alliance(BaseEntity):
    """
    Model representing an alliance from EVE Online
    """
    ticker = models.CharField(unique=True, max_length=7)

    objects = AllianceManager()


@python_2_unicode_compatible
class ItemType(BaseEntity):
    """
    Model representing an item type from EVE Online
    """
    pass


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
            return bool(account.key_info())
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
                assert evelink.corp.Corp(api=api).corporation_sheet(corp_id=corp_id).result
                corp, c = Corporation.objects.get_or_create(id=corp_id)
                if self.corp != corp:
                    self.corp = corp
                    update_fields.append('corp')
            else:
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
            if not self.is_valid:
                self.is_valid = True
                update_fields.append('is_valid')
            if update_fields:
                self.save(update_fields=update_fields)
        except evelink.api.APIError as e:
            if int(e.code) in [500, 520, 221]:
                raise e
            else:
                update_fields = []
                if self.is_valid or self.is_valid is None:
                    self.is_valid = False
                    update_fields.append('is_valid')
                if self.characters.all().exists():
                    for char in self.characters.all():
                        self.characters.remove(char)
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
                if update_fields:
                    self.save(update_fields=update_fields)
