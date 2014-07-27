import re
import logging
import importlib

import venusian

from .declaration import Column, ForeignKey
from .declaration.meta import db


log = logging.getLogger(__name__)


class table:
    """
    Decorator to register a table in a database.
    """
    _counter = 1

    def __init__(self, database, collation='en_US.UTF8', name=None):
        self.database = database
        self.collation = collation
        self.name = name

    def __call__(self, wrapped):

        def callback(scanner, name, ob):

            setattr(wrapped, '__meta__',
                    {'tablename': None,
                     'alias': 't{}'.format(self._counter),
                     'database': self.database,
                     'collation': self.collation,
                     'columns': None,
                     # Populate on column descriptors
                     'primary_key': {},
                     'pkv': None,
                     'foreign_keys': {},
                     })

            self.__class__._counter += 1

            if not self.name:
                self.name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2',
                                   wrapped.__name__)
                self.name = re.sub('([a-z0-9])([A-Z])', r'\1_\2',
                                   self.name).lower()
            wrapped.__meta__['tablename'] = self.name

            # Populate column descriptors
            columns = [getattr(wrapped, attr).name
                       for attr in dir(wrapped)
                       if isinstance(getattr(wrapped, attr), (Column,
                                                              ForeignKey))]
            wrapped.__meta__['columns'] = sorted(columns)

            log.info('Register table {}'.format(self.name))
            db[self.database][self.name] = wrapped

        venusian.attach(wrapped, callback, category='aiorm')
        return wrapped


def scan(*modules):
    scanner = venusian.Scanner()
    for mod in modules:
        log.info('Scanning {}'.format(mod))
        scanner.scan(importlib.import_module(mod))
