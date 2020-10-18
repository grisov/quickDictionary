#template.py
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import os


# Template for displaying HTML content.
htmlTemplate = ''.join(["&nbsp;",
	"<!DOCTYPE html>",
	"<html>",
	"<head>",
	'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
	"<title></title>"
	'<link rel="stylesheet" type="text/css" href="%s">' % os.path.join(os.path.dirname(__file__), 'style.css'),
	"</head>",
	"<body>{body}</body>",
	"</html>"
])
