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


class ReadOnlyEntityForm(EveEntityForm):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyEntityForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['readonly'] = True
            if not getattr(self, 'instance', None):
                self.fields['id'].widget.attrs['readonly'] = False

    def __getattr__(self, item):
        # implement all field cleaning methods in one go
        # subclasses can implement specific field cleaning which will not call this
        if str.startswith(item, 'clean_'):
            attr_name = item[item.index('_'):]
            instance = getattr(self, 'instance', None)
            if instance:
                return getattr(instance, attr_name)
            else:
                return None


class ReadOnlyCharacterForm(CharacterForm, ReadOnlyEntityForm):
    pass


class ReadOnlyCorporationForm(CorporationForm, ReadOnlyEntityForm):
    pass


class ReadOnlyAllianceForm(AllianceForm, ReadOnlyEntityForm):
    pass


class ReadOnlyItemTypeForm(ItemTypeForm, ReadOnlyEntityForm):
    pass


class ReadOnlyFactionForm(FactionForm, ReadOnlyEntityForm):
    pass
