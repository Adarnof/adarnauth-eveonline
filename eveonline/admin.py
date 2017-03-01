from __future__ import unicode_literals
from django.contrib import admin
from eveonline.models import Character, Corporation, Alliance
from eveonline.forms import ReadOnlyCharacterForm, ReadOnlyCorporationForm, ReadOnlyAllianceForm


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    form = ReadOnlyCharacterForm


@admin.register(Corporation)
class CorporationAdmin(admin.ModelAdmin):
    form = ReadOnlyCorporationForm


@admin.register(Alliance)
class AllianceAdmin(admin.ModelAdmin):
    form = ReadOnlyAllianceForm
