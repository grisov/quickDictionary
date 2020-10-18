#locator.py
import os
import fnmatch
import config
from importlib import import_module
from . import _addonName


def discover_services():
	matches = []
	dir = 'dictionaries'
	dir_path = os.path.join(os.path.dirname(__file__), dir)
	filenames = [file.name for file in os.scandir(dir_path) if file.is_file()]
	for filename in fnmatch.filter(filenames, '*.py'):
		if filename != "__init__.py":
			matches.append(os.path.join(dir_path, dir, filename))
	rel_files = [file[len(dir_path)+1:] for file in matches]
	modules = [rel_file.replace('/', '.').replace('\\', '.')[:-3] for rel_file in rel_files]
	imported_mods = [import_module(".." + module, package=__name__) for module in modules]


class Lookup(object):
	_lookup = {}

	def add(self, service, instance):
		list = self._lookup.get(service)
		if not list:
			list = []
			self._lookup[service] = list
		list.append(instance)

	def lookup_all(self, service):
		list = self._lookup.get(service) or []
		return list


	def lookup(self, service):
		try:
			return self.lookup_all(service)[0]
		except IndexError:
			return None


global_lookup = Lookup()


def service_provider(*services):
	"""
	This is a class decorator that declares a class to provide a set of services.
	It is expected that the class has a no-arg constructor and will be instantiated
	as a singleton.
	"""

	def real_decorator(clazz):
		instance = clazz()
		for service in services:
			global_lookup.add(service, instance)
		return clazz

	return real_decorator


class DictionaryService(object):
	"""This class only contains the software contract that must be fulfilled by all dictionary services."""

	@property
	def name(self):
		pass

	@property
	def summary(self):
		pass

	@property
	def confspec(self):
		pass

	@property
	def translator(self):
		pass

	@property
	def langs(self):
		pass

	@property
	def settings(self):
		pass


discover_services()
services = global_lookup.lookup_all(DictionaryService)
