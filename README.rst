=====
Adarnauth-EVEOnline
=====

Adarnauth-EVEOnline is a simple Django app which houses models and
methods for manipulating and storing data structures from EVE Online.

Quick start
-----------

1. Add "eveonline" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'eveonline',
    ]

2. Include the eveonline URLconf in your project urls.py like this::

    url(r'^eve/', include('eveonline.urls')),

3. Run `python manage.py migrate` to create the eveonline models.
