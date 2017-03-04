from __future__ import unicode_literals
from django.contrib import admin
from eveonline.models import Character, Corporation, Alliance, Faction, ItemType
from eveonline.forms import ReadOnlyEveEntityForm


@admin.register(Character, Corporation, Alliance, Faction, ItemType)
class EveEntityModelAdmin(admin.ModelAdmin):
    form = ReadOnlyEveEntityForm
