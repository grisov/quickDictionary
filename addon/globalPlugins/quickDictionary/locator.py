# locator.py
# Find available online dictionary services and add them to the list
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
# In the development of this module were used ideas from the Service Locator module by Innolitics
# https://github.com/innolitics/service-locator

from __future__ import annotations

import os
from collections.abc import Callable
from importlib import import_module
from types import ModuleType
from typing import Any

from wx import Panel

from .service import Languages, Translator


def discover_services() -> None:
	"""Discover and import all valid services: each module in the services folder registers its service."""
	servicesDir = os.path.join(os.path.dirname(__file__), "services")
	for entry in os.scandir(servicesDir):
		name, extension = os.path.splitext(entry.name)
		if entry.is_file() and extension == ".py" and name != "__init__":
			_ = import_module(f".services.{name}", package=__package__)


class Lookup(object):
	"""Lookup, add and view all available services."""

	_lookup: dict[type[DictionaryService], list[DictionaryService]] = {}

	def add(self, service: type[DictionaryService], instance: DictionaryService) -> None:
		"""Add received instance to the end of the list for the specified service.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@param instance: an instance of the service that corresponds to the type specified in the first parameter
		@type instance: DictionaryService
		"""
		servs: list[DictionaryService] = self._lookup.get(service, [])
		if not servs:
			servs = []
			self._lookup[service] = servs
		servs.append(instance)

	def lookup_all(self, service: type[DictionaryService]) -> list[DictionaryService]:
		"""Return all instances of the specified service.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@return: a list of all instances of the specified service
		@rtype: list[DictionaryService]
		"""
		servs: list[DictionaryService] = self._lookup.get(service, [])
		servs = sorted(servs, key=lambda srv: srv.id)
		for i in range(len(servs)):
			servs[i].id = i
		return servs

	def lookup(self, service: type[DictionaryService]) -> DictionaryService | None:
		"""Return the first instance of the specified service or None.
		@param service: user-defined service type (usually class template)
		@type service: Type[DictionaryService]
		@return: the first instance of the specified service type
		@rtype: DictionaryService | None
		"""
		try:
			return self.lookup_all(service)[0]
		except IndexError:
			pass
		return None


# instance for the accumulation of services
global_lookup = Lookup()


def service_provider(
	*services: type[DictionaryService],
) -> Callable[[type[DictionaryService]], type[DictionaryService]]:
	"""This is a class decorator that declares a class to provide a set of services.
	It is expected that the class has a no-arg constructor and will be instantiated as a singleton.
	@param services: the types of the services that the class provides
	@type services: type[DictionaryService]
	@return: the class decorator
	@rtype: Callable[[type[DictionaryService]], type[DictionaryService]]
	"""

	def real_decorator(clazz: type[DictionaryService]) -> type[DictionaryService]:
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
	__package__: str = ""

	# Used to set the sort order of a list of services
	# The value must be assigned in the corresponding service description object
	id: int = 0

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
		return getattr(self[".api"], "serviceName", "Unknown_Service_Name")

	@property
	def summary(self) -> str:
		"""Service summary - Appears in the services list and in the settings panel.
		@return service summary
		@rtype: str
		"""
		return getattr(self[".dictionary"], "serviceSummary", "Undefined_Service_Summary")

	@property
	def confspec(self) -> dict[str, str]:
		"""Service configuration scheme.
		@return: configuration scheme
		@rtype: dict[str, str]
		"""
		return getattr(self[".dictionary"], "confspec", {})

	@property
	def translator(self) -> type[Translator]:
		"""A link to the class used by the service to receive translations from the online dictionary.
		@return: specific Translator class used by the service
		@rtype: type[<service_name>.dictionary.ServiceTranslator]
		"""
		return getattr(self[".dictionary"], "ServiceTranslator")

	@property
	def langs(self) -> Languages:
		"""An instance of the Languages class to interact with lists of languages available in the online service.
		@return: an instance of the service specific class to interact with the list of available languages
		@rtype: <service_name>.languages.ServiceLanguages
		"""
		return getattr(self[".languages"], "langs")

	@property
	def panel(self) -> type[Panel]:
		"""A link to the class that represents the settings panel of the selected service.
		@return: link to the service specific settings panel
		@rtype: type[<service_name>.settings.ServicePanel]
		"""
		return getattr(self[".settings"], "ServicePanel")

	@property
	def stat(self) -> dict[str, Any]:
		"""Statistics of using the online service.
		@return: various statistics data
		@rtype: dict[str, Any]
		"""
		return getattr(self[".api"], "stat", {})


# Discover all available services for use in the add-on
discover_services()
services = global_lookup.lookup_all(DictionaryService)
