from __future__ import unicode_literals
from django import forms
from eveonline.providers import eve_provider_factory, ObjectNotFound


class EveEntityForm(forms.ModelForm):
    """
    Provides a clean_id method to check supplied IDs against external API for validation
    """
    def __init__(self, provider=None, *args, **kwargs):
        super(EveEntityForm, self).__init__(*args, **kwargs)
        self.provider = provider or eve_provider_factory()

    def clean_id(self):
        try:
            assert getattr(self.provider, 'get_%s' % self.Meta.model.__class__.__name__.lower())(
                self.cleaned_data['id'])
            return self.cleaned_data['id']
        except (ObjectNotFound, AssertionError):
            raise forms.ValidationError('Invalid %s ID' % self.Meta.model.__class__.__name__.lower())


class ReadOnlyEveEntityForm(EveEntityForm):
    """
    Treats all fields as read-only if the model is already saved
    """
    def __init__(self, *args, **kwargs):
        super(ReadOnlyEveEntityForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True  # should match FK, M2M and CharField which use <select>
            if not getattr(self, 'instance', None):
                self.fields['id'].widget.attrs['readonly'] = False

    def __getattr__(self, name):
        # provide clean_fieldname methods to prevent changing readonly attributes
        if str.startswith(name, 'clean_') and name != 'clean_':
            attr_name = name[name.index('_')+1:]
            instance = getattr(self, 'instance', None)
            if instance:
                return getattr(instance, attr_name)
            else:
                return None
        else:
            return super(ReadOnlyEveEntityForm, self).__getattr__(name)
