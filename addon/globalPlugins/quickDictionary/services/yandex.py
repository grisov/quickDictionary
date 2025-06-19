# yandex.py
# Online dictionary service description
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2025 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import os.path
from ..locator import service_provider, DictionaryService


@service_provider(DictionaryService)
class YandexDictionary(DictionaryService):
	"""Representation of the online dictionary service."""
	__package__ = __name__.replace('.' + os.path.basename(os.path.dirname(__file__)), '')
	id = 1
