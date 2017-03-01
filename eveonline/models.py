from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core import validators
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

    def get_prep_value(self, value):
        if value is None:
            return value
        else:
            return super(EveEntityField, self).get_prep_value(value.id)


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


class CorporationSnapshotMixin:
    """
    Provides pseudo-FK behaviour to external API corporation data
    Snapshots corporation_id and provides a corporation property
    """
    _corporation_id = models.PositiveIntegerField()

    @property
    def corporation(self):
        try:
            return eve_provider_factory().get_corporation(self._corporation_id)
        except ObjectNotFound:
            return None

    @corporation.setter
    def corporation(self, obj):
        self._corporation_id = obj.id


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
        Pulls data from a provider object and maps it to model attributes.
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
                # this is likely a nested attribute, such as corporation_name -> corporation.name
                # get the corporation/alliance property, then get the id/name property of it
                values[f] = getattr(getattr(obj, chain[0]), chain[1])
        return cls(**values)

    def update(self, provider=None):
        """
        Updates the corporation/alliance info from external source
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
    corporation_id = models.PositiveIntegerField()
    corporation_name = models.CharField(max_length=30)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=30, null=True, blank=True)


@python_2_unicode_compatible
class Corporation(BaseEntity):
    """
    Model representing a corporation from EVE Online
    """
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    members = models.PositiveIntegerField(help_text="Number of member characters")
    ticker = models.CharField(unique=True, max_length=7)


@python_2_unicode_compatible
class Alliance(BaseEntity):
    """
    Model representing an alliance from EVE Online
    """
    ticker = models.CharField(unique=True, max_length=7)


@python_2_unicode_compatible
class ItemType(BaseEntity):
    """
    Model representing an item type from EVE Online
    """
    pass
