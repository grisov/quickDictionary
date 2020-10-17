#service.py


class DictionaryService(object):
	"""
	This class only contains the software contract that must be fulfilled by all dictionaries.
	"""

	@property
	def label(self):
		pass

	def translator(self):
		pass

	def langs(self):
		pass

	def settings(self):
		pass

	def secret(self):
		pass
