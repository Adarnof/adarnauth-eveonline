from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core import validators
from eveonline.providers import eve_provider_factory, ObjectNotFound, Character as ProviderCharacter, \
    Corporation as ProviderCorporation, Alliance as ProviderAlliance, ItemType as ProviderItemType, \
    Faction as ProviderFaction


class EveEntityValidator(validators.BaseValidator):
    """
    Ensures provided ID is valid for expected EVE entity type
    """

    @staticmethod
    def compare(obj_id, expected_type):
        try:
            return bool(getattr(eve_provider_factory(), 'get_%s' % expected_type.__class__.__name__.lower())(obj_id))
        except ObjectNotFound:
            return False

    @staticmethod
    def clean(obj):
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


class FactionField(EveEntityField):
    object_class = ProviderFaction


class AllianceSnapshotMixin(object):
    """
    Provides pseudo-FK behaviour to external API alliance data
    Snapshots alliance_id and provides a alliance property
    """
    alliance_id = models.PositiveIntegerField()
    alliance_name = models.CharField(max_length=30)

    @property
    def alliance(self):
        try:
            return eve_provider_factory().get_alliance(self.alliance_id)
        except ObjectNotFound:
            return None

    @alliance.setter
    def alliance(self, obj):
        self.alliance_id = obj.id
        self.alliance_name = obj.name


class NullAllianceSnapshotMixin(AllianceSnapshotMixin):
    """
    Provides pseudo-FK behaviour to external API alliance data
    Snapshots alliance_id and provides a alliance property
    Allows null values
    """
    alliance_id = models.PositiveIntegerField(blank=True, null=True)
    alliance_name = models.CharField(max_length=30, blank=True, null=True)

    @property
    def alliance(self):
        if self.alliance_id and self.alliance_name:
            return super(NullAllianceSnapshotMixin, self).alliance
        return None

    @alliance.setter
    def alliance(self, obj):
        if obj:
            super(NullAllianceSnapshotMixin, self).alliance = obj
        else:
            self.alliance_id = None
            self.alliance_name = None


class FactionSnapshotMixin(object):
    """
    Provides pseudo-FK behaviour to external API faction data
    Snapshots faction_id and provides a faction property
    """
    faction_id = models.PositiveIntegerField()
    faction_name = models.CharField(max_length=30)

    @property
    def faction(self):
        try:
            return eve_provider_factory().get_faction(self.faction_id)
        except ObjectNotFound:
            return None

    @faction.setter
    def faction(self, obj):
        self.faction_id = obj.id
        self.faction_name = obj.name


class NullFactionSnapshotMixin(FactionSnapshotMixin):
    """
    Provides pseudo-FK behaviour to external API faction data
    Snapshots faction_id and provides a faction property
    """
    faction_id = models.PositiveIntegerField(blank=True, null=True)
    faction_name = models.CharField(max_length=30, blank=True, null=True)

    @property
    def faction(self):
        if self.faction_id and self.faction_name:
            return super(NullFactionSnapshotMixin, self).faction
        else:
            return None

    @faction.setter
    def faction(self, obj):
        if obj:
            super(NullFactionSnapshotMixin, self).faction = obj
        else:
            self.faction_id = None
            self.faction_name = None


class CorporationSnapshotMixin(NullAllianceSnapshotMixin, NullFactionSnapshotMixin):
    """
    Provides pseudo-FK behaviour to external API corporation data
    Snapshots corporation_id and provides a corporation property
    """
    corporation_id = models.PositiveIntegerField()
    corporation_name = models.CharField(max_length=30)

    @property
    def corporation(self):
        try:
            corp = eve_provider_factory().get_corporation(self.corporation_id)
            corp.alliance = self.alliance
            corp.faction = self.faction
        except ObjectNotFound:
            return None

    @corporation.setter
    def corporation(self, obj):
        self.corporation_id = obj.id
        self.corporation_name = obj.name
        self.alliance = obj.alliance


class CharacterSnapshotMixin(CorporationSnapshotMixin):
    """
    Provides pseudo-FK behaviour to external API character data
    Snapshots character_id and provides a character property
    """
    character_id = models.PositiveIntegerField()
    character_name = models.CharField(max_length=37)

    @property
    def character(self):
        try:
            char = eve_provider_factory().get_character(self.character_id)
            char.corporation = self.corporation
        except ObjectNotFound:
            return None

    @character.setter
    def character(self, obj):
        self.character_id = obj.id
        self.character_name = obj.name
        self.corporation = obj.corporation


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
    def map_obj_attributes(cls, obj):
        """
        Updates model attribute values from provider object
        :param obj: :class:`eveonline.providers.EveEntity`
        :return: Dictionary of attribute_name:value
        """
        fields = [field.name for field in cls._meta.fields]
        values = {}
        for f in fields:
            try:
                # iterate over field names and get data from object
                chain = f.split('_')
                attribute = None
                index = 0
                while index < len(chain):
                    item = chain[index]
                    try:
                        # if we're lucky this is a direct mapping, like 'id' or 'name'
                        attribute = getattr(obj, item)
                    except AttributeError:
                        # attributes with underscores in their name such as executor_corporation will not map directly
                        # test-join neighbouring attributes to see if we can find what we're looking for
                        right_item = '_'.join([chain[index], chain[index + 1]])
                        attribute = getattr(obj, right_item)
                        index += 1  # skip getting the next item because we had to join it to the current
                    index += 1
                values[f] = attribute
            except AttributeError:
                # obj does not have this attribute, so let the calling function decide how to handle missing data
                pass
        return values

    @classmethod
    def from_provider_obj(cls, obj):
        """
        Pulls data from a provider object and maps it to model attributes.
        :param obj: :class:`eveonline.providers.Entity` or subclass
        :return: :class:`eveonline.models.BaseEntity` or subclass
        """
        attr_dict = cls.map_obj_attributes(obj)
        return cls(**attr_dict)

    def update(self, provider=None, commit=True):
        """
        Updates the corporation/alliance info from external source
        :param provider: :class:`eveonline.providers.EveProvider`
        :param commit: True to save the model upon updating
        :return: :class:`eveonline.models.BaseEntity` or subclass
        """
        provider = provider or eve_provider_factory()
        obj = (provider.get_character(self.id))
        attr_dict = self.map_obj_attributes(obj)
        for attr, value in attr_dict.items():
            setattr(self, attr, value)
        if commit:
            self.save()
        return self


class Character(CorporationSnapshotMixin, BaseEntity):
    """
    Model representing a character from EVE Online
    """
    pass


class Corporation(NullAllianceSnapshotMixin, NullFactionSnapshotMixin, BaseEntity):
    """
    Model representing a corporation from EVE Online
    """
    members = models.PositiveIntegerField(help_text="Number of member characters")
    ticker = models.CharField(unique=True, max_length=7)


class Alliance(BaseEntity):
    """
    Model representing an alliance from EVE Online
    """
    ticker = models.CharField(unique=True, max_length=7)


class ItemType(BaseEntity):
    """
    Model representing an item type from EVE Online
    """
    pass


class Faction(BaseEntity):
    """
    Model representing a faction from EVE Online
    """
    description = models.CharField()
