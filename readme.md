# NVDA Quick Dictionary

* Author: Oleksandr Gryshchenko
* Version: 2.1
* NVDA compatibility: 2019.3 and beyond
* Download [stable version][1]

Welcome to NVDA Quick Dictionary addon, which will allow you to quickly get a dictionary article with the translation of a word or phrase into your chosen language by pressing a key combination. There are few basic keyboard shortcuts and they are all intuitive and convenient so you will remember them quickly.

Dictionary articles contain detailed information about a word, such as part of speech, gender, plural or singular, translation options, list of meanings, synonyms and detailed examples. Such information will be useful for people who are learning foreign languages, or seek to use in communication all the richness and diversity of their own language.

The add-on supports several online dictionary services. You can select the desired remote dictionary in the appropriate dialog box or by using keyboard shortcuts. Each available service has its own settings panel.

There are also advanced opportunities for working with profiles of the voice synthesizers. You can associate a voice synthesizer profile with a specific language, after that translations into this language will be automatically voiced by the selected synthesizer.

Below are all the features of the add-on and keyboard shortcuts to control them. By default all functions are called using two-layer commands. But for any of these methods you can always assign convenient for you keyboard shortcuts. You can do it in the NVDA "Preferences" -> "Input gestures..." dialog.

## Receiving a dictionary article
In order to get an article from the dictionary, you must first select the word you are interested in or copy it to the clipboard. Then just press NVDA+Y twice.

There is also another way to get a dictionary entry: pressing NVDA+Y once switches the keyboard to add-on control mode, then just use the D key.

## Add-on control mode
To access all the features of the add-on, you need to switch to add-on control mode, you can do this by pressing NVDA+Y once. You will hear a short low beep and will be able to use the other commands described below. When you press a key that is not used in the add-on, you will hear another signal notifying you of an erroneous command and the add-on control mode will be automatically turned off.

## Add-on commands list
Basic dictionary commands:

* D - announce a dictionary entry for a selected word or phrase (same as NVDA+Y);
* W - show dictionary entry in a separate browseable window;
* S - swap languages and get Quick Dictionary translation;
* A - announce the current source and target languages;
* C - copy last dictionary entry to the clipboard;
* E - edit text before sending;
* U - download from online dictionary and save the current list of available languages;
* function keys - select online dictionary service;
* Q - statistics on the using the online service;
* F - choose online service.

Voice synthesizers profiles management:

* from 1 to 9 - selection of the voice synthesizer profile;
* G - announce the selected profile of voice synthesizers;
* B - back to previous voice synthesizer;
* R - restore default voice synthesizer;
* Del - delete the selected voice synthesizer profile;
* V - save configured voice synthesizer profile;
* P - display a list of all customized voice synthesizers profiles.

Press O to open add-on settings dialog.

## Help on add-on commands
You can see a list of all the commands used in the add-on as follows:

* Via the NVDA menu - by pressing NVDA+N, go to the submenu "Tools", then - "Quick Dictionary" and activate the menu item "Help on add-on commands".
* Press the H key in add-on control mode (NVDA+Y).

## Add-on help
To open the add-on help - press NVDA+N, go to the "Tools" submenu, then - "Quick Dictionary" and activate the menu item "Help".

## Contributions
We are very grateful to everyone who made the effort to develop, translate and maintain this add-on:

* Cagri Dogan - Turkish translation;
* Wafiqtaher - Arabic translation.

Several good solutions from other developments were used in the Quick Dictionary add-on. Thanks to the authors of the following add-ons:

* Instant Translate - Alexy Sadovoy, Beqa Gozalishvili, Mesar Hameed, Alberto Buffolino and other NVDA contributors.
* To work with voice synthesizers profiles were used ideas from the Switch Synth add-on (thanks to Tyler Spivey).

## Change log

### Version 2.1.5
* the source code is significantly optimized and added MyPy type hints;
* the add-on is adapted to support Python versions 3.7 and 3.8;
* fixed formatting errors in Markdown files;
* added a dialog to edit the text before sending to remote service;
* separated add-on help page from ReadMe;
* Turkish translation added (thanks to Cagri Dogan).

## Altering NVDA QuickDictionary
You may clone this repo to make alteration to NVDA Quick Dictionary.

### Third Party dependencies
These can be installed with pip:

- markdown
- scons
- python-gettext

### To package the add-on for distribution:
1. Open a command line, change to the root of this repo
2. Run the **scons** command. The created add-on, if there were no errors, is placed in the current directory.

[1]: https://addons.nvda-project.org/files/get.php?file=quickdictionary
