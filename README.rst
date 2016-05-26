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

2. Run `python manage.py migrate` to create the eveonline models.
