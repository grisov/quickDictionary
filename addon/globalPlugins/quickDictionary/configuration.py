# configuration.py
# The name of the add-on and the access to the NVDA configuration
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 Oleksandr Gryshchenko <grisov.nvaccess@mailgw.com>

from collections.abc import MutableMapping
from typing import Any, cast

import addonHandler
import config

# The add-on of the running code; its manifest has no type annotations.
# The modules of the add-on import the name from here, not from the package, to avoid circular imports.
_addon = cast(Any, addonHandler).getCodeAddon()
addonName: str = _addon.manifest["name"]
addonSummary: str = _addon.manifest["summary"]


def getDocFilePath() -> str:
	"""Get the path to the documentation of the add-on in the language of NVDA.
	@return: the path to the readme.html file
	@rtype: str
	"""
	return _addon.getDocFilePath()


def getNvdaConfig() -> Any:
	"""Get the whole NVDA configuration with its profiles and specification.
	NVDA declares config.conf as None until the configuration is loaded, and it has no type annotations.
	@return: config.conf of NVDA
	@rtype: Any
	"""
	return cast(Any, config.conf)


def getAddonConfig() -> MutableMapping[str, Any]:
	"""Get the add-on section of the NVDA configuration in the current configuration profile.
	@return: the options of the add-on and of its services
	@rtype: MutableMapping[str, Any]
	"""
	return getNvdaConfig()[addonName]
