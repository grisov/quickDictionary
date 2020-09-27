# NVDA Quick Dictionary
* Version 1.0.1
* Download [stable version][1]

Welcome to NVDA Quick Dictionary addon, which will allow you to quickly get a dictionary article with the translation of a word or phrase into your chosen language by pressing a key combination. There are few keyboard shortcuts and they are all intuitive and convenient so you will remember them quickly.
Dictionary articles contain detailed information about a word, such as part of speech, gender, plural or singular, translation options, list of meanings, synonyms and detailed examples. Such information will be useful for people who are learning foreign languages, or seek to use in communication all the richness and diversity of their own language.

## Receiving a dictionary article
In order to get an article from the dictionary, you must first select the word you are interested in or copy it to the clipboard. Then just press NVDA+E twice.
There is also another way to get a dictionary entry: pressing NVDA+E once switches the keyboard to add-on control mode, then just use the D key.

Note: Before making a request to a remote service, the add-on must receive a word or phrase that interests the user. The sequence of actions that add-on performs each time before accessing the dictionary:
* receive the selected text and execute the request;
* if there is no selected text - receive the text content of the clipboard and execute the request;
* if the clipboard is empty or its content is not text data - the add-on notifies the user and does not take further action.

## Add-on control mode
For quick access to the most used functions of the add-on, there are three keyboard shortcuts:
* Press NVDA+E twice to get a dictionary entry for the selected word or phrase.
* NVDA+Ctrl+E - to swap the source and target languages and get a translation for the new combination.
* NVDA+Alt+E - to open the add-on settings dialog.

To access all other features of the add-on, you need to switch to add-on control mode, you can do this by pressing NVDA+E once. You will hear a short low beep and will be able to use the other commands described below. When you press a key that is not used in the application, you will hear another signal notifying you of an erroneous command and the application control mode will be automatically turned off.

## Announcement of the selected pair of languages when working with the dictionary
To determine the current source language and destination language, follow these steps:
1. Enable add-on control mode with NVDA+E.
2. Press A to listen to which languages are selected to retrieve data from the dictionary.

## Swap source and target languages
This can be done quickly as follows:
1. Select the word or phrase that interests you.
2. Press NVDA+Ctrl+E.
You will hear a message that the languages have been swapped and the available information from the dictionary.

The same can be done using the add-on control mode:
1. Select the word or phrase that interests you.
2. Enable add-on control mode with NVDA+E and than press S.

Note: Each time you swap languages, the add-on checks to see if a new pair of languages is available for translation in the remote dictionary. If there is no such language combination, you will hear a warning.

## Display a dictionary article in a separate browseable window
An article from the dictionary can also be displayed in a separate window as a formatted web page:
1. Select a word or phrase.
2. Enable add-on control mode - NVDA+E.
3. Press W.

Note: In this window, you can use standard commands to navigate web page elements. To close the window just press Escape or Alt+F4.

## Copy the results of the last request to the clipboard
This can be done by following the steps below:
1. Enable add-on control mode - NVDA+E.
2. Press C.
You will then hear a message that the data has been successfully copied and the dictionary entry itself.

Note: If you haven't previously made any requests to the remote dictionary, you will hear a warning.
If option "Copy dictionary response to clipboard" in the add-on settings is enabled, the data will be automatically copied after each successful request.

## Add-on settings dialog
To change the add-on parameters you need to open the dialog box of its settings. This can be done in two ways:
1. Using the keyboard shortcut NVDA+Alt+E.
2. Through the add-on control mode: press NVDA+E and then the key O.
The standard NVDA settings dialog with the open section of our add-on will appear on the screen.

### Choice of languages for translation
When you open the add-on settings dialog, the NVDA cursor is immediately placed on the drop-down list of source language selection. You can select the language from the list and press Enter or Tab to go to the target language selection.

Note: The list of available target languages depends on the selected source language, so the target language should only be selected after the source language is set

### Checkbox "Copy dictionary response to clipboard"
After checking this box, the data received from the dictionary will be copied to the clipboard after each request.

### Checkbox "Auto-swap languages"
After enabling this option, the add-on will try to retrieve the data a second time by swapping the source and target language if the dictionary query didn't return any results.

Note: If the reverse language combination isn't available, you will hear a warning each time.

### Checkbox "Use alternative server"
After enabling this option, the add-on will not send requests directly to the remote dictionary, but will use an alternate intermediate server that forwards all requests further.

### Dictionary access token
To use the remote dictionary service, it is recommended to get your own access token. By default, the add-on already uses a pre-registered access code. But the remote dictionary service used in the add-on imposes certain restrictions and query limits on each free user. Therefore, with the mass use of one access token - sooner or later it can be blocked. To avoid this, it is recommended to register your own access code and specify it in the add-on settings.
You will find a link to register below the field for entering the access token, by clicking on it, you will go to the appropriate web page.

Note: The registration link is displayed only when using the default access token. Once you enter your own access code in the settings, this link will be hidden. To restore the default access token, simply clear the field for entering it and click "OK". The default access code will be restored in the add-on configuration and you will see it the next time you open the settings dialog.

## Brief reference information
To listen to short help, switch to add-on control mode with NVDA+E, then press H. You will hear a message with a list of all available keyboard commands and add-on features.

## Change log

### Version 1.0.1
* Changed keyboard shortcuts that are duplicated in NVDA;
* Fixed error in Ukrainian translation (thanks to Volodymyr Perig);

### Version 1.0: features of implementation
* execution of requests to the remote server in a separate thread to avoid blocking the operation of NVDA;
* signals while waiting for a response from the server;
* caching of the last 100 requests to reduce the load on the remote dictionary service;
* switching to add-on control mode;
* possibility to use an alternative server;
* add-on settings dialog.

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

[1]: https://github.com/grisov/quickDictionary/releases/download/v1.0/quickDictionary-1.0.nvda-addon
