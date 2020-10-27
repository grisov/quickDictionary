#locator.py
# Find available online dictionary services and add them to the list
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
# In the development of this module were used ideas from the Service Locator module by Innolitics
# https://github.com/innolitics/service-locator

import os
import fnmatch
from importlib import import_module


def discover_services() -> None:
	"""Discover and import all valid services."""
	matches = []
	dir = 'services'
	dir_path = os.path.join(os.path.dirname(__file__), dir)
	filenames = [file.name for file in os.scandir(dir_path) if file.is_file()]
	for filename in fnmatch.filter(filenames, '*.py'):
		if filename != "__init__.py":
			matches.append(os.path.join(dir_path, dir, filename))
	rel_files = [file[len(dir_path)+1:] for file in matches]
	modules = [rel_file.replace('/', '.').replace('\\', '.')[:-3] for rel_file in rel_files]
	imported_mods = [import_module(".." + module, package=__name__) for module in modules]


class Lookup(object):
	"""Lookup, add and view all available services."""
	_lookup = {}

	def add(self, service: object, instance: object) -> None:
		"""Add received instance to the end of the list for the specified service.
		@param service: user-defined service type (usually class template)
		@type service: object
		@param instance: an instance of the service that corresponds to the type specified in the first parameter
		@type instance: service
		"""
		list = self._lookup.get(service)
		if not list:
			list = []
			self._lookup[service] = list
		list.append(instance)

	def lookup_all(self, service: object) -> list:
		"""Return all instances of the specified service.
		@param service: user-defined service type (usually class template)
		@type service: object
		@return: a list of all instances of the specified service
		@rtype: list
		"""
		list = self._lookup.get(service) or []
		list = sorted(list, key=lambda srv: srv.id)
		for i in range(len(list)):
			list[i].id = i
		return list

	def lookup(self, service: object) -> list:
		"""Return the first instance of the specified service or None.
		@param service: user-defined service type (usually class template)
		@type service: object
		@return: the first instance of the specified service type
		@rtype: service
		"""
		try:
			return self.lookup_all(service)[0]
		except IndexError:
			return None


# instance for the accumulation of services
global_lookup = Lookup()


def service_provider(*services):
	"""This is a class decorator that declares a class to provide a set of services.
	It is expected that the class has a no-arg constructor and will be instantiated as a singleton.
	"""
	def real_decorator(clazz):
		instance = clazz()
		for service in services:
			global_lookup.add(service, instance)
		return clazz
	return real_decorator


class DictionaryService(object):
	"""A template that specifies the type of online dictionary services.
	This class only contains the software contract that must be fulfilled by all dictionary services.
	"""

	# Used to set the sort order of a list of services
	id: int = 0

	@property
	def name(self) -> str:
		"""Short service name.
		Matches the name of the file representing the service and - the name of the directory containing the service modules.
		@return: service name
		@rtype: str
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def summary(self) -> str:
		"""Service summary - Appears in the services list and in the settings panel.
		@return service summary
		@rtype: str
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def confspec(self) -> dict:
		"""Service configuration scheme.
		@return: configuration scheme
		@rtype: dict
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def translator(self) -> object:
		"""A link to the class used by the service to receive translations from the online dictionary.
		@return: object type used by the service
		@rtype: object, usually inherited from <service_name>.dictionary.Translator
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def langs(self) -> object:
		"""An instance of the Languages class to interact with lists of languages available in the online service.
		@return: an instance of the class to interact with the list of available languages
		@rtyp: object, usually instance of <service_name>.languages.Languages
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def panel(self) -> object:
		"""A link to the class that represents the settings panel of the selected service.
		@return: link to the add-on settings panel
		@rtype: wx.Panel
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def stat(self) -> dict:
		"""Statistics of using the online service.
		@return: various statistical data
		@rtype: dict
		"""
		raise NotImplementedError("This property must be overridden in the child class!")


# Discover all available services for use in the add-on
discover_services()
services = global_lookup.lookup_all(DictionaryService)
