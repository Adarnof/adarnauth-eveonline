from django.contrib import admin
from django import forms
from eveonline.models import Character, Corporation, Alliance


class CharacterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CharacterForm, self).__init__(*args, **kwargs)
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

    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if Character.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")

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


class CorporationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CorporationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['alliance_id'].widget.attrs['readonly'] = True
        self.fields['alliance_name'].widget.attrs['readonly'] = True
        self.fields['members'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if Corporation.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")

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


class AllianceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AllianceForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if Alliance.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")

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


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    form = CharacterForm


@admin.register(Corporation)
class CorporationAdmin(admin.ModelAdmin):
    form = CorporationForm


@admin.register(Alliance)
class AllianceAdmin(admin.ModelAdmin):
    form = AllianceForm

