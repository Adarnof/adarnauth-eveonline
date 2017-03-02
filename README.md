# adarnauth-eveonline

Django app which houses models and methods for retrieving and storing data structures from EVE Online.

## Quick start

1. Add "eveonline" to your INSTALLED_APPS setting like this:

```
INSTALLED_APPS = [
    ...
    'eveonline',
]
```

2. Run `python manage.py migrate` to create models.

## Retrieving Data

### Objects

Data can be retrieved from the XML API or EVE Swagger Interface through a common provider interface. The core of this system is the provider object system, a series of classes which return data in an identical format no matter the source.

These objects also provide convenience properties to access related objects: for instance, the `Character` object can provide a `Corporation` object for that character's corporation by accessing the `corporation` property.

Objects are available for `Character`, `Corporation`, `Alliance`, `Faction`, and `ItemType` data types.

### Providers

Providers are the API clients which provide data. Two providers are defined, one for XML and one for ESI. The `EveXmlProvider` accepts an optional API key tuple of `(api_id, verification_code)`. The `EveSwaggerProvider` accepts an optional `token` argument, being a `esi.models.Token` model from [adarnauth-esi](https://github.com/adarnof/adarnauth-esi).

Objects can be retrieved by calling the provider's `get_` methods and supplying the desired ID: for instance, to get a character, call `provider.get_character(234899860)`.

A provider factory is available for easy provider creation, `eveonline.providers.eve_provider_factory`. This returns the default provider as defined by `settings.EVEONLINE_DEFAULT_PROVIDER`. If unset, this defaults to the `EveSwaggerProvider`. Accepted values are `xml` and `esi`.

It is highly recommended to use the `EveSwaggerProvider` as default due to the depreciated status of the XML API. But the `EveXmlProvider` is available should ESI experience issues.

### Caching

The provider factory returns a wrapper provider which automatically caches results. This will greatly speed up related calls. The default caching time can be altered by defining `settings.EVEONLINE_OBJ_CACHE_DURATION`, in secods.

Objects are cached as per the django project configuration. Longer caching timers will reduce API calls to speed up the app, but will consume more memory and not be as up-to-date. Select a caching time accordingly.

## Storing Data

### Models

Models for `Character`, `Corporation`, `Alliance`, `Faction`, and `ItemType` are available. These are best used when explicit foreign keys are needed, or filtering by fields other than ID is required.

Models can be created manually, or by providing an API object from a provider:

    char = provider.get_character(234899860)
    return Character.from_provider_obj(char)

This automatically populates a new `Character` model with data from the provider.

Models can also be updated from provider objects:

    char = Character.objects.get(id=234899860)
    char.update()

This performs a similar function to `from_provider_obj`, mapping the provider object attributes to the model's fields. Passing `commit=True` saves the model.

Models are not guaranteed to be up-to-date. They are automatically updated every 8 hours by default; this can be altered through celerybeat schedule configuration. Only `Character` and `Corporation` models are updated as `Alliance`, `Faction` and `ItemType` will not change without CCP intervention.

## Snapshots

Snapshots are useful when the current relationships of an EVE object are the focus of future queries. Snapshots embed the current relations into a given model and provide ways of retrieving historically accurate object relations.

Mixins are provided for models: `AllianceSnapshotMixin`, `FactionSnapshotMixin`, `CorporationSnapshotMixin`, and `CharacterSnapshotMixin`. Each of these stores the ID and name of the current object into the model. Objects can be retrieved by accessing the `alliance`, `faction`, `corporation`, or `character` properties of models with the mixin. These return a provider object with relations matching those when the snapshot was taken.

These mixins are inherited: the `CharacterSnapshotMixin` also embeds corporation, alliance and faction data. If desired, all these objects can be retrieved in the future for an accurate picture of historic relations.

To use a snapshot, inherit the mixin in your model. For instance, in a fleet participation link:

    class PapLink(CharacterSnapshotMixin, models.Model):

Then during model creation, pass a `Character` provider object to the `character` property:

    pap = PapLink(**data)
    pap.character = provider.get_character(234899860)

Passing to a `character` property will also store that character's corporation in the `corporation` property, that corporation's alliance in the `alliance` property, and that corporation's faction in the `faction` property.

Each property can be accessed individually, or the relational links can also be followed. For instance, both of these will return the same object:

    pap.character.corporation
    pap.corporation

Note that not all fields on the returned object are guaranteed to be historically accurate, merely the relations. For instance, `pap.alliance.member_corps` will not be a historically accurate list of member corps, but rather the current list.

Alliance and faction mixins are also available in a nulled variant, allowing blank values (these are inherited by the `CorporationSnapshotMixin`), named `NullAllianceSnapshotMixin` and `NullFactionSnapshotMixin`. If no alliance or faction is saved, they return `None`.

## Fields

Custom model fields are best used when queries about object attributed other than ID are not essential, or there's an emphasis on getting the most current information about an object. These store the ID and retrieve the rest of the object's attributes when accessed.

All fields inherit from `django.db.models.BigIntegerField` to ensure IDs greater than 2^31 will function should CCP begin using them. Fields validate data in two ways above the usual `BigIntegerField` validators:
 
  - Entered values must be greater than zero. CCP does not use negative IDs.
  - Entered values must be valid for the given object type. For instance, `CharacterField` checks the ID supplied to make sure it is actually a character. This is done by attempting to retrieve the object from the default provider.

Fields can be set by passing either a provider object or an ID integer.

Fields are inherently more susceptible to API outages - if the default provider is unable to connect to the API, values will not be able to be stored nor retrieved.

Additionally, if the default provider is `xml`, any `AllianceField` with a closed alliance ID will not be able to retrieve the alliance object due to limitations of the XML API. For this reason it is highly recommended to keep the default provider as `esi`.
