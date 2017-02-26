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
OBJ_CACHE_DURATION = int(getattr(settings, 'EVEONLINE_OBJ_CACHE_DURATION', 300))


@python_2_unicode_compatible
class ObjectNotFound(Exception):
    def __init__(self, obj_id, type_name):
        self.id = obj_id
        self.type = type_name

    def __str__(self):
        return '%s with ID %s not found.' % (self.type, self.id)


@python_2_unicode_compatible
class Entity(object):
    def __init__(self, obj_id, name):
        self.id = obj_id
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{} ({}): {}>".format(self.__class__.__name__, self.obj_id, self.name)

    def __bool__(self):
        return bool(self.obj_id)

    def __eq__(self, other):
        return self.obj_id == other.obj_id

    def serialize(self):
        return {
            'id': self.obj_id,
            'name': self.name,
        }

    @classmethod
    def from_dict(cls, data_dict):
        return cls(data_dict['id'], data_dict['name'])


class Corporation(Entity):
    def __init__(self, provider, obj_id, name, ticker, ceo_id, members, alliance_id):
        super(Corporation, self).__init__(obj_id, name)
        self.provider = provider
        self.ticker = ticker
        self.ceo_id = ceo_id
        self.members = members
        self.alliance_id = alliance_id
        self._alliance = None
        self._ceo = None

    @property
    def alliance(self):
        if self.alliance_id:
            if not self._alliance:
                self._alliance = self.provider.get_alliance(self.alliance_id)
            return self._alliance
        return Entity(None, None)

    @property
    def ceo(self):
        if not self._ceo:
            self._ceo = self.provider.get_character(self.ceo_id)
        return self._ceo

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'ticker': self.ticker,
            'ceo_id': self.ceo_id,
            'members': self.members,
            'alliance_id': self.alliance_id
        }

    @classmethod
    def from_dict(cls, obj_dict):
        return cls(
            None,
            obj_dict['id'],
            obj_dict['name'],
            obj_dict['ticker'],
            obj_dict['ceo_id'],
            obj_dict['members'],
            obj_dict['alliance_id'],
        )


class Alliance(Entity):
    def __init__(self, provider, obj_id, name, ticker, corp_ids, executor_corp_id):
        super(Alliance, self).__init__(obj_id, name)
        self.provider = provider
        self.ticker = ticker
        self.corp_ids = corp_ids
        self.executor_corp_id = executor_corp_id
        self._corps = {}

    def corp(self, corp_id):
        assert corp_id in self.corp_ids
        if corp_id not in self._corps:
            self._corps[corp_id] = self.provider.get_corp(corp_id)
            self._corps[corp_id]._alliance = self
        return self._corps[corp_id]

    @property
    def corps(self):
        return sorted([self.corp(corp_id) for corp_id in self.corp_ids], key=lambda x: x.name)

    @property
    def executor_corp(self):
        return self.corp(self.executor_corp_id)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'ticker': self.ticker,
            'corp_ids': self.corp_ids,
            'executor_corp_id': self.executor_corp_id,
        }

    @classmethod
    def from_dict(cls, obj_dict):
        return cls(
            None,
            obj_dict['id'],
            obj_dict['name'],
            obj_dict['ticker'],
            obj_dict['corp_ids'],
            obj_dict['executor_corp_id'],
        )


class Character(Entity):
    def __init__(self, provider, obj_id, name, corp_id, alliance_id):
        super(Character, self).__init__(obj_id, name)
        self.provider = provider
        self.corp_id = corp_id
        self.alliance_id = alliance_id
        self._corp = None
        self._alliance = None

    @property
    def corp(self):
        if not self._corp:
            self._corp = self.provider.get_corp(self.corp_id)
        return self._corp

    @property
    def alliance(self):
        if self.alliance_id:
            return self.corp.alliance
        return Entity(None, None)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'corp_id': self.corp_id,
            'alliance_id': self.alliance_id,
        }

    @classmethod
    def from_dict(cls, obj_dict):
        return cls(
            None,
            obj_dict['id'],
            obj_dict['name'],
            obj_dict['corp_id'],
            obj_dict['alliance_id'],
        )


class ItemType(Entity):
    def __init__(self, provider, type_id, name):
        super(ItemType, self).__init__(type_id, name)
        self.provider = provider

    @classmethod
    def from_dict(cls, data_dict):
        return cls(
            None,
            data_dict['id'],
            data_dict['name'],
        )


class EveProvider(object):
    def get_alliance(self, alliance_id):
        """
        :return: an Alliance object for the given ID
        """
        raise NotImplementedError()

    def get_corp(self, corp_id):
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
        raise NotImplemented()


@python_2_unicode_compatible
class EveSwaggerProvider(EveProvider):
    def __init__(self, token=None, adapter=None):
        self.client = esi_client_factory(token=token, Alliance='v1', Character='v4', Corporation='v2', Universe='v2')
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

    def get_corp(self, corp_id):
        try:
            data = self.client.Corporation.get_corporations_corporation_id(corporation_id=corp_id).result()
            model = Corporation(
                self.adapter,
                corp_id,
                data['corporation_name'],
                data['ticker'],
                data['ceo_id'],
                data['member_count'],
                data['alliance_id'] if 'alliance_id' in data else None,
            )
            return model
        except HTTPNotFound:
            raise ObjectNotFound(corp_id, 'corporation')

    def get_character(self, character_id):
        try:
            data = self.client.Character.get_characters_character_id(character_id=character_id).result()
            alliance_id = self.adapter.get_corp(data['corporation_id']).alliance_id
            model = Character(
                self.adapter,
                character_id,
                data['name'],
                data['corporation_id'],
                alliance_id,
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


@python_2_unicode_compatible
class EveXmlProvider(EveProvider):
    def __init__(self, api_key=None, adapter=None):
        """
        :param api_key: eveonline.EveApiKeyPair
        """
        self.api = evelink.api.API(api_key=(api_key.api_id, api_key.api_key)) if api_key else evelink.api.API()
        self.adapter = adapter or self

    def __str__(self):
        return 'xml'

    def get_alliance(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        alliances = api.alliances().result
        try:
            results = alliances[int(obj_id)]
        except KeyError:
            raise ObjectNotFound(obj_id, 'alliance')
        model = Alliance(
            self.adapter,
            obj_id,
            results['name'],
            results['ticker'],
            results['member_corps'],
            results['executor_id'],
        )
        return model

    def get_corp(self, obj_id):
        api = evelink.corp.Corp(api=self.api)
        try:
            corpinfo = api.corporation_sheet(corp_id=int(obj_id)).result
        except evelink.api.APIError as e:
            if int(e.code) == 523:
                raise ObjectNotFound(obj_id, 'corporation')
            raise e
        model = Corporation(
            self.adapter,
            obj_id,
            corpinfo['name'],
            corpinfo['ceo']['id'],
            corpinfo['members']['current'],
            corpinfo['ticker'],
            corpinfo['alliance']['id'] if corpinfo['alliance'] else None,
        )
        return model

    def _build_character(self, result):
        return Character(
            self.adapter,
            result['id'],
            result['name'],
            result['corp']['id'],
            result['alliance']['id'],
        )

    def get_character(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        try:
            charinfo = api.character_info_from_id(obj_id).result
        except evelink.api.APIError as e:
            if int(e.code) == 105:
                raise ObjectNotFound(obj_id, 'character')
            raise e
        return self._build_character(charinfo)

    def get_itemtype(self, obj_id):
        api = evelink.eve.EVE(api=self.api)
        try:
            type_name = api.type_name_from_id(obj_id).result
            assert type_name != 'Unknown Type'
            return ItemType(self.adapter, obj_id, type_name)
        except AssertionError:
            raise ObjectNotFound(obj_id, 'itemtype')


class EveAdapter(EveProvider):
    """
    Redirects queries to appropriate data source.
    """

    def __init__(self, char_provider, corp_provider, alliance_provider, itemtype_provider):
        self.char_provider = char_provider
        self.corp_provider = corp_provider
        self.alliance_provider = alliance_provider
        self.itemtype_provider = itemtype_provider
        self.char_provider.adapter = self
        self.corp_provider.adapter = self
        self.alliance_provider.adapter = self
        self.itemtype_provider.adapter = self

    def __repr__(self):
        skeleton = "<{} (character:{} corp:{} alliance:{} itemtype:{})>"
        return skeleton.format(self.__class__.__name__,
                               str(self.char_provider),
                               str(self.corp_provider),
                               str(self.alliance_provider),
                               str(self.itemtype_provider))

    @staticmethod
    def _get_from_cache(obj_class, obj_id):
        data = cache.get('%s__%s' % (obj_class.__name__.lower(), obj_id))
        if data:
            obj = obj_class.from_dict(data)
            logger.debug('Got from cache: %s' % obj.__repr__())
            return obj
        else:
            return None

    @staticmethod
    def _cache(obj):
        logger.debug('Caching: %s ' % obj.__repr__())
        cache.set('%s__%s' % (obj.__class__.__name__.lower(), obj.id), obj.serialize(),
                  int(OBJ_CACHE_DURATION))

    def get_character(self, obj_id, new=False):
        if new:
            obj = None
        else:
            obj = self._get_from_cache(Character, obj_id)
        if obj:
            obj.provider = self
        else:
            obj = self._get_character(obj_id)
            self._cache(obj)
        return obj

    def get_corp(self, obj_id, new=False):
        if new:
            obj = None
        else:
            obj = self._get_from_cache(Corporation, obj_id)
        if obj:
            obj.provider = self
        else:
            obj = self._get_corp(obj_id)
            self._cache(obj)
        return obj

    def get_alliance(self, obj_id, new=False):
        if new:
            obj = None
        else:
            obj = self._get_from_cache(Alliance, obj_id)
        if obj:
            obj.provider = self
        else:
            obj = self._get_alliance(obj_id)
            self._cache(obj)
        return obj

    def get_itemtype(self, obj_id, new=False):
        if new:
            obj = None
        else:
            obj = self._get_from_cache(ItemType, obj_id)
        if obj:
            obj.provider = self
        else:
            obj = self._get_itemtype(obj_id)
            self._cache(obj)
        return obj

    def _get_character(self, obj_id):
        return self.char_provider.get_character(obj_id)

    def _get_corp(self, obj_id):
        return self.corp_provider.get_corp(obj_id)

    def _get_alliance(self, obj_id):
        return self.alliance_provider.get_alliance(obj_id)

    def _get_itemtype(self, obj_id):
        return self.itemtype_provider.get_itemtype(obj_id)


def eve_adapter_factory(api_key=None, token=None, **kwargs):
    character_source = kwargs.get('character_source',
                                  getattr(settings, 'EVEONLINE_CHARACTER_PROVIDER', '') or 'esi').lower()
    corp_source = kwargs.get('corp_source', getattr(settings, 'EVEONLINE_CORP_PROVIDER', '') or 'esi').lower()
    alliance_source = kwargs.get('alliance_source',
                                 getattr(settings, 'EVEONLINE_ALLIANCE_PROVIDER', '') or 'esi').lower()
    itemtype_source = kwargs.get('itemtype_source',
                                 getattr(settings, 'EVEONLINE_ITEMTYPE_PROVIDER', '') or 'esi').lower()

    sources = [character_source, corp_source, alliance_source, itemtype_source]
    providers = []

    if 'xml' in sources:
        xml = EveXmlProvider(api_key=api_key)
    if 'esi' in sources:
        esi = EveSwaggerProvider(token=token)

    for source in sources:
        if source == 'xml':
            providers.append(xml)
        elif source == 'esi':
            providers.append(esi)
        else:
            raise ValueError('Unrecognized data source "%s"' % source)
    return EveAdapter(providers[0], providers[1], providers[2], providers[3])