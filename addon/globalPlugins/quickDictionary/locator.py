# locator.py
# Find available online dictionary services and add them to the list
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
# In the development of this module were used ideas from the Service Locator module by Innolitics
# https://github.com/innolitics/service-locator

from __future__ import annotations
from typing import Any, Optional, Callable, List, Dict
from types import ModuleType
import os
import fnmatch
from importlib import import_module
from wx import Panel
from .service import Translator, Languages


def discover_services() -> None:
	"""Discover and import all valid services."""
	matches: List[str] = []
	dir = 'services'
	dir_path = os.path.join(os.path.dirname(__file__), dir)
	filenames: List[str] = [file.name for file in os.scandir(dir_path) if file.is_file()]
	for filename in fnmatch.filter(filenames, '*.py'):
		if filename != "__init__.py":
			matches.append(os.path.join(dir_path, dir, filename))
	rel_files: List[str] = [file[len(dir_path) + 1:] for file in matches]
	modules: List[str] = [rel_file.replace('/', '.').replace('\\', '.')[:-3] for rel_file in rel_files]
	imported_mods: List[ModuleType] = [import_module(".." + module, package=__name__) for module in modules]  # noqa F841


class Lookup(object):
	"""Lookup, add and view all available services."""
	_lookup: Dict[DictionaryService, List[DictionaryService]] = {}

	def add(self, service: DictionaryService, instance: DictionaryService) -> None:
		"""Add received instance to the end of the list for the specified service.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@param instance: an instance of the service that corresponds to the type specified in the first parameter
		@type instance: DictionaryService
		"""
		servs: List[DictionaryService] = self._lookup.get(service, [])
		if not servs:
			servs = []
			self._lookup[service] = servs
		servs.append(instance)

	def lookup_all(self, service) -> List[DictionaryService]:
		"""Return all instances of the specified service.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@return: a list of all instances of the specified service
		@rtype: List[DictionaryService]
		"""
		servs: List[DictionaryService] = self._lookup.get(service, [])
		servs = sorted(servs, key=lambda srv: srv.id)
		for i in range(len(servs)):
			servs[i].id = i
		return servs

	def lookup(self, service: DictionaryService) -> Optional[DictionaryService]:
		"""Return the first instance of the specified service or None.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@return: the first instance of the specified service type
		@rtype: Optional[DictionaryService]
		"""
		try:
			return self.lookup_all(service)[0]
		except IndexError:
			pass
		return None


# instance for the accumulation of services
global_lookup = Lookup()


def service_provider(*services) -> Callable:
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

	# The path to the remote service description file
	# The value must be assigned in the corresponding service description object
	# Typical value:
	# __package__ = __name__.replace('.' + os.path.basename(os.path.dirname(__file__)), '')
	__package__: str

	# Used to set the sort order of a list of services
	# The value must be assigned in the corresponding service description object
	id: int

	def __getitem__(self, name: str) -> ModuleType:
		"""Get the instance of the imported module by the specified name.
		@param name: target module name
		@type name: str
		@return: the instance of the imported module
		@rtype: ModuleType
		"""
		return import_module(name, package=self.__package__)

	@property
	def name(self) -> str:
		"""Short service name.
		Matches the name of the file representing the service
		and - the name of the directory that contains the service modules.
		@return: service name
		@rtype: str
		"""
		return getattr(self['.api'], 'serviceName', 'Unknown_Service_Name')

	@property
	def summary(self) -> str:
		"""Service summary - Appears in the services list and in the settings panel.
		@return service summary
		@rtype: str
		"""
		return getattr(self['.dictionary'], 'serviceSummary', 'Undefined_Service_Summary')

	@property
	def confspec(self) -> Dict[str, str]:
		"""Service configuration scheme.
		@return: configuration scheme
		@rtype: Dict[str, str]
		"""
		return getattr(self['.dictionary'], 'confspec', {})

	@property
	def translator(self) -> Translator:
		"""A link to the class used by the service to receive translations from the online dictionary.
		@return: specific Translator class used by the service
		@rtype: <service_name>.dictionary.ServiceTranslator
		"""
		return getattr(self['.dictionary'], 'ServiceTranslator', object)

	@property
	def langs(self) -> Languages:
		"""An instance of the Languages class to interact with lists of languages available in the online service.
		@return: an instance of the service specific class to interact with the list of available languages
		@rtyp: <service_name>.languages.ServiceLanguages
		"""
		return getattr(self['.languages'], 'langs', object)

	@property
	def panel(self) -> Panel:
		"""A link to the class that represents the settings panel of the selected service.
		@return: link to the service specific settings panel
		@rtype: <service_name>.settings.ServicePanel
		"""
		return getattr(self['.settings'], 'ServicePanel', object)

	@property
	def stat(self) -> Dict[str, Any]:
		"""Statistics of using the online service.
		@return: various statistics data
		@rtype: Dict[str, Any]
		"""
		return getattr(self['.api'], 'stat', {})


# Discover all available services for use in the add-on
discover_services()
services = global_lookup.lookup_all(DictionaryService)
