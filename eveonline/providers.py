from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from esi.clients import esi_client_factory
from django.conf import settings
from django.core.cache import cache
from bravado.exception import HTTPNotFound, HTTPUnprocessableEntity
import evelink
import logging

logger = logging.getLogger(__name__)

# optional setting to control cached object lifespan
OBJ_CACHE_DURATION = int(getattr(settings, 'EVEONLINE_OBJ_CACHE_DURATION', 600))


@python_2_unicode_compatible
class ObjectNotFound(Exception):
    def __init__(self, obj_id, type_name):
        self.id = obj_id
        self.type = type_name

    def __str__(self):
        return '%s with ID %s not found.' % (self.type, self.id)


@python_2_unicode_compatible
class Entity(object):
    def __init__(self, obj_id, name, provider=None):
        self.id = obj_id
        self.name = name
        self._provider = provider

    def __str__(self):
        return str(self.name)

    def __int__(self):
        return int(self.id)

    def __repr__(self):
        return "<{} ({}): {}>".format(self.__class__.__name__, self.obj_id, self.name)

    def __bool__(self):
        return bool(self.obj_id)

    def __eq__(self, other):
        return int(self) == int(other) and str(self) == str(other)

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._provider = None

    def __getstate__(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    @property
    def provider(self):
        self._provider = self._provider or eve_provider_factory()
        return self._provider


class Corporation(Entity):
    def __init__(self, obj_id, name, ticker, ceo_id, members, alliance_id, faction_id, provider=None):
        super(Corporation, self).__init__(obj_id, name, provider=provider)
        self.ticker = ticker
        self.ceo_id = ceo_id
        self.members = members
        self.alliance_id = alliance_id
        self.faction_id = faction_id
        self._alliance = None
        self._ceo = None
        self._faction = None

    @property
    def alliance(self):
        if self.alliance_id:
            if not self._alliance:
                self._alliance = self.provider.get_alliance(self.alliance_id)
            return self._alliance
        return Entity(None, None)

    @alliance.setter
    def alliance(self, obj):
        if obj:
            self.alliance_id = obj.id
            self._alliance = obj
        else:
            self.alliance_id = None
            self._alliance = None

    @property
    def ceo(self):
        if not self._ceo:
            self._ceo = self.provider.get_character(self.ceo_id)
        return self._ceo

    @property
    def faction(self):
        if self.faction_id:
            if not self._faction:
                self._faction = self.provider.get_faction(self.faction_id)
            return self._faction
        return Entity(None, None)

    @faction.setter
    def faction(self, obj):
        if obj:
            self.faction_id = obj.id
            self._faction = obj
        else:
            self.faction_id = None
            self._faction = None

    def __getstate__(self):
        return super(Corporation, self).__getstate__().update(
            {
                'ticker': self.ticker,
                'ceo_id': self.ceo_id,
                'members': self.members,
                'alliance_id': self.alliance_id,
                'faction_id': self.faction_id,
            }
        )

    def __setstate__(self, state):
        super(Corporation, self).__setstate__(state)
        self._alliance = None
        self._ceo = None
        self._faction = None


class Alliance(Entity):
    def __init__(self, obj_id, name, ticker, corp_ids, executor_corp_id, provider=None):
        super(Alliance, self).__init__(obj_id, name, provider=provider)
        self.ticker = ticker
        self.corporation_ids = corp_ids
        self.executor_corporation_id = executor_corp_id
        self._corps = {}

    def corporation(self, corp_id):
        assert corp_id in self.corporation_ids
        if corp_id not in self._corps:
            self._corps[corp_id] = self.provider.get_corporation(corp_id)
            self._corps[corp_id]._alliance = self
        return self._corps[corp_id]

    @property
    def corporations(self):
        return sorted([self.corporation(corp_id) for corp_id in self.corporation_ids], key=lambda x: x.name)

    @property
    def executor_corporation(self):
        return self.corporation(self.executor_corporation_id)

    def __getstate__(self):
        return super(Alliance, self).__getstate__().update(
            {
                'ticker': self.ticker,
                'corporation_ids': self.corporation_ids,
                'executor_corporation_id': self.executor_corporation_id,
            }
        )

    def __setstate__(self, state):
        super(Alliance, self).__setstate__(state)
        self._corps = {}


class Character(Entity):
    def __init__(self, obj_id, name, corp_id, provider=None):
        super(Character, self).__init__(obj_id, name, provider=provider)
        self.corporation_id = corp_id
        self._corporation = None

    @property
    def corporation(self):
        if not self._corporation:
            self._corporation = self.provider.get_corporation(self.corporation_id)
        return self._corporation

    @corporation.setter
    def corporation(self, obj):
        self.corporation_id = obj.id
        self._corporation = obj

    @property
    def alliance(self):
        return self.corporation.alliance

    @property
    def faction(self):
        return self.corporation.faction

    def __getstate__(self):
        return super(Character, self).__getstate__().update(
            {
                'corporation_id': self.corporation_id,
                'alliance_id': self.alliance_id,
            }
        )

    def __setstate__(self, state):
        super(Character, self).__setstate__(state)
        self._corporation = None


class ItemType(Entity):
    def __init__(self, type_id, name, provider=None):
        super(ItemType, self).__init__(type_id, name, provider=provider)


class Faction(Entity):
    def __init__(self, faction_id, name, description, provider=None):
        super(Faction, self).__init__(faction_id, name, provider=provider)
        self.description = description

    def __getstate__(self):
        return super(Faction, self).__getstate__().update({'description': self.description})


class EveProvider(object):
    def get_alliance(self, alliance_id):
        """
        :return: an Alliance object for the given ID
        """
        raise NotImplementedError()

    def get_corporation(self, corp_id):
        """
        :return: a Corporation object for the given ID
        """
        raise NotImplementedError()

    def get_character(self, character_id):
        """
        :return: a Character object for the given ID
        """
        raise NotImplementedError()

    def get_itemtype(self, type_id):
        """
        :return: an ItemType object for the given ID
        """
        raise NotImplementedError()

    def get_faction(self, faction_id):
        """
        :return: a Faction object for the given ID
        """
        raise NotImplementedError()


@python_2_unicode_compatible
class EveSwaggerProvider(EveProvider):
    def __init__(self, token=None, adapter=None):
        self.client = esi_client_factory(token=token, Alliance='v1', Character='v4', Corporation='v3', Universe='v2')
        self.adapter = adapter or self

    def __str__(self):
        return 'esi'

    def get_alliance(self, alliance_id):
        try:
            data = self.client.Alliance.get_alliances_alliance_id(alliance_id=alliance_id).result()
            corps = self.client.Alliance.get_alliances_alliance_id_corporations(alliance_id=alliance_id).result()
            model = Alliance(
                self.adapter,
                alliance_id,
                data['alliance_name'],
                data['ticker'],
                corps,
                data['executor_corporation_id'],
            )
            return model
        except HTTPNotFound:
            raise ObjectNotFound(alliance_id, 'alliance')

    @staticmethod
    def _faction_name_to_id(name):
        factions = esi_client_factory(Universe='v1').get_factions().result()
        try:
            return [f['faction_id'] for f in factions if f['name'].startswith(name)][0]
        except KeyError:
            return None

    def get_corporation(self, corp_id):
        try:
            data = self.client.Corporation.get_corporations_corporation_id(corporation_id=corp_id).result()
            if 'faction' in data:
                faction_id = self._faction_name_to_id(data['faction'])
            else:
                faction_id = None
            model = Corporation(
                self.adapter,
                corp_id,
                data['corporation_name'],
                data['ticker'],
                data['ceo_id'],
                data['member_count'],
                data['alliance_id'] if 'alliance_id' in data else None,
                faction_id
            )
            return model
        except HTTPNotFound:
            raise ObjectNotFound(corp_id, 'corporation')

    def get_character(self, character_id):
        try:
            data = self.client.Character.get_characters_character_id(character_id=character_id).result()
            model = Character(
                self.adapter,
                character_id,
                data['name'],
                data['corporation_id'],
            )
            return model
        except (HTTPNotFound, HTTPUnprocessableEntity):
            raise ObjectNotFound(character_id, 'character')

    def get_itemtype(self, type_id):
        try:
            data = self.client.Universe.get_universe_types_type_id(type_id=type_id).result()
            return ItemType(self.adapter, type_id, data['name'])
        except (HTTPNotFound, HTTPUnprocessableEntity):
            raise ObjectNotFound(type_id, 'type')

    def get_faction(self, faction_id):
        try:
            data = esi_client_factory(Universe='v1').Universe.get_factions().result()
            faction_data = [faction for faction in data if faction['faction_id'] == faction_id][0]
            return Faction(self, faction_data['faction_id'], faction_data['name'], faction_data['description'])
        except KeyError:
            raise ObjectNotFound(faction_id, 'faction')


@python_2_unicode_compatible
class EveXmlProvider(EveProvider):
    def __init__(self, api_key=None, adapter=None):
        """
        :param api_key: tuple of api_id, verification_code
        """
        self.api = evelink.api.API(api_key=api_key) if api_key else evelink.api.API()
        self.adapter = adapter or self

    def __str__(self):
        return 'xml'

    def get_alliance(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        alliances = api.alliances().result
        try:
            results = alliances[int(obj_id)]
            model = Alliance(
                self.adapter,
                obj_id,
                results['name'],
                results['ticker'],
                results['member_corps'],
                results['executor_id'],
            )
            return model
        except KeyError:
            raise ObjectNotFound(obj_id, 'alliance')

    def get_corporation(self, obj_id):
        api = evelink.corp.Corp(api=self.api)
        try:
            corpinfo = api.corporation_sheet(corp_id=int(obj_id)).result
            model = Corporation(
                self.adapter,
                obj_id,
                corpinfo['name'],
                corpinfo['ceo']['id'],
                corpinfo['members']['current'],
                corpinfo['ticker'],
                corpinfo['alliance']['id'] if corpinfo['alliance'] else None,
                corpinfo['faction']['id'] if corpinfo['faction'] else None,
            )
            return model
        except evelink.api.APIError as e:
            if int(e.code) == 523:
                raise ObjectNotFound(obj_id, 'corporation')
            raise e

    def _build_character(self, result):
        return Character(
            self.adapter,
            result['id'],
            result['name'],
            result['corp']['id'],
        )

    def get_character(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        try:
            charinfo = api.character_info_from_id(obj_id).result
            return self._build_character(charinfo)
        except evelink.api.APIError as e:
            if int(e.code) == 105:
                raise ObjectNotFound(obj_id, 'character')
            raise e

    def get_itemtype(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        try:
            type_name = api.type_name_from_id(obj_id).result
            assert type_name != 'Unknown Type'
            return ItemType(self.adapter, obj_id, type_name)
        except AssertionError:
            raise ObjectNotFound(obj_id, 'itemtype')

    def get_faction(self, faction_id):
        api = evelink.eve.EVE(api=self.api)
        try:
            result = api.character_info_from_id(faction_id).result
            return Faction(self, faction_id, result['name'], None)
        except evelink.api.APIError as e:
            if int(e.code) == 105:
                raise ObjectNotFound(faction_id, 'faction')
            raise e


class CachingProviderWrapper(EveProvider):
    """
    Caches data from wrapper provider
    """

    def __init__(self, provider):
        self.provider = provider
        self.provider.adapter = self

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self.provider))

    @staticmethod
    def format_cache_key_name(obj_class, obj_id):
        return '%s__%s' % (obj_class.__name__.lower(), obj_id)

    def __get_object(self, obj_class, obj_id, new=False):
        cache_key_name = self.format_cache_key_name(obj_class, obj_id)
        method = getattr(self.provider, 'get_%s' % obj_class.__name__.lower())
        if new:
            obj = method(obj_id)
            cache.set(cache_key_name, obj, OBJ_CACHE_DURATION)
        else:
            obj = cache.get_or_set(cache_key_name, method(obj_id), OBJ_CACHE_DURATION)
            obj.provider = self
        return obj

    def get_character(self, obj_id, new=False):
        return self.__get_object(Character, obj_id, new=new)

    def get_corporation(self, obj_id, new=False):
        return self.__get_object(Corporation, obj_id, new=new)

    def get_alliance(self, obj_id, new=False):
        return self.__get_object(Alliance, obj_id, new=new)

    def get_itemtype(self, obj_id, new=False):
        return self.__get_object(ItemType, obj_id, new=new)

    def get_faction(self, obj_id, new=False):
        return self.__get_object(Faction, obj_id, new=new)


def eve_provider_factory(api_key=None, token=None, default_provider=None):
    default_provider = default_provider or getattr(settings, 'EVEONLINE_DEFAULT_PROVIDER', 'esi')

    if default_provider.lower() == 'xml':
        provider = EveXmlProvider(api_key=api_key)
    elif default_provider.lower() == 'esi':
        provider = EveSwaggerProvider(token=token)
    else:
        raise ValueError('Unrecognized provider "%s"' % default_provider)
    return CachingProviderWrapper(provider)
