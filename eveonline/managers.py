from __future__ import unicode_literals
from django.db import models
from eveonline.providers import eve_provider_factory, ObjectNotFound


class BaseManager(models.Manager):
    class Meta:
        abstract = True

    def check_id(self, object_id):
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
    def check_id(self, char_id):
        """
        Ensures the character ID is valid
        """
        try:
            return bool(eve_provider_factory().get_character(char_id))
        except ObjectNotFound:
            return False


class CorporationManager(BaseManager):
    def check_id(self, corp_id):
        """
        Ensures corporation ID is valid
        """
        try:
            return bool(eve_provider_factory().get_corp(corp_id))
        except ObjectNotFound:
            return False


class AllianceManager(BaseManager):
    def check_id(self, alliance_id):
        """
        Ensures alliance ID is valid
        """
        try:
            return bool(eve_provider_factory().get_alliance(alliance_id))
        except ObjectNotFound:
            return False
