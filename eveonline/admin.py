from __future__ import unicode_literals
from django.contrib import admin
from eveonline.models import Character, Corporation, Alliance, Faction, ItemType
from eveonline.forms import ReadOnlyEveEntityForm


@admin.register(Character, Corporation, Alliance, Faction, ItemType)
class EveEntityModelAdmin(admin.ModelAdmin):
    form = ReadOnlyEveEntityForm

    def get_fields(self, request, obj=None):
        if obj:
            return super(EveEntityModelAdmin, self).get_fields(request, obj=obj)
        else:
            # this is a new model addition, so only display the ID field and let the form populate the rest of the data
            return ['id']
