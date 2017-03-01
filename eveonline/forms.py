from __future__ import unicode_literals
from django import forms
from eveonline.providers import eve_provider_factory, ObjectNotFound
from eveonline.models import Character, Corporation, Alliance, ItemType, Faction


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


class FactionForm(EveEntityForm):
    class Meta:
        model = Faction


class ReadOnlyCharacterForm(CharacterForm):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyCharacterForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['corp_id'].widget.attrs['readonly'] = True
        self.fields['corp_name'].widget.attrs['readonly'] = True
        self.fields['alliance_id'].widget.attrs['readonly'] = True
        self.fields['alliance_name'].widget.attrs['readonly'] = True
        self.fields['faction_id'].widget.attrs['readonly'] = True
        self.fields['faction_name'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None

    def clean_corp_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.corp_id
        else:
            return None

    def clean_corp_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.corp_name
        else:
            return None

    def clean_alliance_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_id
        else:
            return None

    def clean_alliance_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_name
        else:
            return None

    def clean_faction_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_name
        else:
            return None

    def clean_faction_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_id
        else:
            return None


class ReadOnlyCorporationForm(CorporationForm):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyCorporationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['alliance_id'].widget.attrs['readonly'] = True
        self.fields['alliance_name'].widget.attrs['readonly'] = True
        self.fields['faction_id'].widget.attrs['readonly'] = True
        self.fields['faction_name'].widget.attrs['readonly'] = True
        self.fields['members'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None

    def clean_alliance_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_id
        else:
            return None

    def clean_alliance_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_name
        else:
            return None

    def clean_faction_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_id
        else:
            return None

    def clean_faction_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_name
        else:
            return None

    def clean_members(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.members
        else:
            return 0

    def clean_ticker(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.ticker
        else:
            return None


class ReadOnlyAllianceForm(AllianceForm):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyAllianceForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None

    def clean_ticker(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.ticker
        else:
            return None
