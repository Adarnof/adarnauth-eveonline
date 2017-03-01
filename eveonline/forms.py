from __future__ import unicode_literals
from django import forms
from eveonline.providers import eve_provider_factory, ObjectNotFound
from eveonline.models import Character, Corporation, Alliance, ItemType


class EveEntityForm(forms.ModelForm):
    def __init__(self, provider=None, *args, **kwargs):
        super(EveEntityForm, self).__init__(*args, **kwargs)
        self.provider = provider or eve_provider_factory()

    def clean_id(self):
        try:
            assert getattr(self.provider, 'get_%s' % self.Meta.model.__class__.__name__.lower())(
                self.cleaned_data['id'])
            return self.cleaned_data['id']
        except (ObjectNotFound, AssertionError):
            raise forms.ValidationError('Invalid %s ID' % self.Meta.model.__class__.__name__)


class CharacterForm(EveEntityForm):
    class Meta:
        model = Character


class CorporationForm(EveEntityForm):
    class Meta:
        model = Corporation


class AllianceForm(EveEntityForm):
    class Meta:
        model = Alliance


class ItemTypeForm(EveEntityForm):
    class Meta:
        model = ItemType
