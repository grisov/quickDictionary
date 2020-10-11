# NVDA Quick Dictionary

* Author: Oleksandr Gryshchenko
* Version: 1.2
* Download [stable version][1]
* Download [development version][2]

Welcome to NVDA Quick Dictionary addon, which will allow you to quickly get a dictionary article with the translation of a word or phrase into your chosen language by pressing a key combination. There are few keyboard shortcuts and they are all intuitive and convenient so you will remember them quickly.
Dictionary articles contain detailed information about a word, such as part of speech, gender, plural or singular, translation options, list of meanings, synonyms and detailed examples. Such information will be useful for people who are learning foreign languages, or seek to use in communication all the richness and diversity of their own language.
Below are all the features of the add-on and keyboard shortcuts to control them. By default all functions are called using two-layer commands. But for any of these methods, you can always assign convenient for you keyboard shortcuts. You can do it in the NVDA "Preferences" -> "Input gestures..." dialog.

## Receiving a dictionary article
In order to get an article from the dictionary, you must first select the word you are interested in or copy it to the clipboard. Then just press NVDA+Y twice.
There is also another way to get a dictionary entry: pressing NVDA+Y once switches the keyboard to add-on control mode, then just use the D key.

Note: Before making a request to a remote service, the add-on must receive a word or phrase that interests the user. The sequence of actions that add-on performs each time before accessing the dictionary:
* receive the selected text and execute the request;
* if there is no selected text - receive the text content of the clipboard and execute the request;
* if the clipboard is empty or its content is not text data - the add-on notifies the user and does not take further action.

## Add-on control mode
To access all the features of the add-on, you need to switch to add-on control mode, you can do this by pressing NVDA+Y once. You will hear a short low beep and will be able to use the other commands described below. When you press a key that is not used in the application, you will hear another signal notifying you of an erroneous command and the application control mode will be automatically turned off.

## Announcement of the selected pair of languages when working with the dictionary
To determine the current source language and destination language, follow these steps:
1. Enable add-on control mode with NVDA+Y.
2. Press A to listen to which languages are selected to retrieve data from the dictionary.

## Swap source and target languages
This can be done quickly as follows:
1. Select the word or phrase that interests you.
2. Enable add-on control mode with NVDA+Y and than press S.
You will hear a message that the languages have been swapped and the available information from the dictionary.

Note: Each time you swap languages, the add-on checks to see if a new pair of languages is available for translation in the remote dictionary. If there is no such language combination, you will hear a warning.

## Display a dictionary article in a separate browseable window
An article from the dictionary can also be displayed in a separate window as a formatted web page:
1. Select a word or phrase.
2. Enable add-on control mode - NVDA+Y.
3. Press W.

Note: In this window, you can use standard commands to navigate web page elements. To close the window just press Escape or Alt+F4.

## Copy the results of the last request to the clipboard
This can be done by following the steps below:
1. Enable add-on control mode - NVDA+Y.
2. Press C.
You will then hear a message that the data has been successfully copied and the dictionary entry itself.

Note: If you haven't previously made any requests to the remote dictionary, you will hear a warning.
If option "Copy dictionary response to clipboard" in the add-on settings is enabled, the data will be automatically copied after each successful request.

## Download the current list of available languages
Use the U key in add-on control mode to download from the online dictionary and save current list of available source and target languages.
After that you will hear a message about the status of the command.

## Add-on settings dialog
To change the add-on parameters you need to open the dialog box of its settings. This can be done this way: press NVDA+Y and then the key O.
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

## Add and manage voice synthesizers profiles
This add-on implements the ability to voice the received dictionary articles using associated and pre-configured voice synthesizers.
To take advantage of this feature, you must first create and save voice synthesizers profiles, and then associate these profiles with the languages in the add-on settings dialog.
After that, upon receipt of the translation, associated voice synthesizers will be switched for each specified language.

### Creating a voice synthesizer profile
You can create up to 9 configuration profiles for the various voice synthesizers available in NVDA.
To switch between profiles, use the number keys 1 to 9 in the add-on control mode.

For example, to create a profile number 5, follow these steps:
1. Switch to add-on control mode using NVDA+Y.
2. Press the 5 key. You will hear a message that the selected profile is number 5.
3. Go to the "Speech" section of the NVDA settings using NVDA+Ctrl+V and configure the desired voice synthesizer to be saved in the selected profile. Then press "Ok" button.
4. Save the configured synthesizer in the selected profile - press NVDA+Y and then V. You will hear a message about the successful saving of the voice synthesizer profile.

### Activate voice synthesizer by default
To return to using the default voice synthesizer, press NVDA+Y, then press R. This will restore the default voice synthesizer and you will hear its name and the selected voice.

### Switch between profiles
As mentioned earlier, you can switch between voice synthesizers profiles using the number keys.
If the profile already has previously saved voice synthesizer settings, the corresponding voice will be activated and you will hear a message with information about the number of the activated profile, the name of the synthesizer and the name of the voice.
Otherwise, if the selected profile does not yet contain any data - a message will be displayed only about its number and the synthesizer will not switch.

Note: In either case, you can return to default voice using the R key in add-on control mode (NVDA+Y).

### Notification of the currently selected profile
To hear which profile is currently selected, use the G key in add-on control mode (NVDA+Y).
If the profile contains voice synthesizer settings, the name of the synthesizer and voice will be announced in addition to the number. Otherwise, you will only hear the active profile number.

### Announce a list of all customized voice synthesizers profiles
To listen to a list of all voice synthesizers profiles that have been configured before, press the P key in add-on control mode (NVDA+Y).
For each profile will be announced its number, synthesizer name, voice name, and the language associated with that profile.

Note: By default, the associated language is set to "- Immutable language -". This means that switching to this synthesizer will not be performed.
The process of changing the associated language for each profile will be described below.

### Delete settings from the selected profile
To delete the voice synthesizer settings from the currently selected profile, use the Delete key in add-on control mode (NVDA+Y).
You will hear a message about the successful deletion of the profile with the specified number.

### Save changes
After each manipulation of the profile (create/update/delete) it is necessary to save changes using V key in the add-on control mode (NVDA+Y).
By pressing this key you will hear the message about successful saving of the changes.

### Choice of associated language
To associate a profile with the desired language, follow these steps:
1. Open the add-on settings dialog using NVDA+Y and then O.
2. Find and enable the "Switch between voice synthesizers for selected languages" checkbox.
3. Tab to desired profile and select the language from the drop-down list to which it will be used.
4. Press "OK".

Note:
* If no profile has been previously created, you will see a warning about it in the add-on settings dialog.
* Each language can be associated with only one profile. If you select a language for one of the profiles, it will be automatically removed from the drop-down lists for the other profiles.
* In order not to use the profile to switch synthesizers - associate it with the first item "- Immutable language -".

### The process of switching voice synthesizers
After making the previous settings, the voice synthesizer of your choice will automatically turn on when you receive data from the dictionary. And after the announcement of the article, the default synthesizer will turn on again.

Note: Switching synthesizers occurs at the beginning and after the announcement of the dictionary article. If you interrupt the current speech, the default synthesizer will not be activated automatically. So you have to switch to it manually. This can be done very simply by pressing NVDA+Y and then R. Done.

## Brief reference information
To listen to short help, switch to add-on control mode with NVDA+Y, then press H. You will hear a message with a list of all available keyboard commands and add-on features.

## Contributions
We are very grateful to everyone who made the effort to develop, translate and maintain this add-on:
* Cagri Dogan - Turkish translation;

Several good solutions from other ingenious developments were used in the Quick Dictionary add-on. Thanks to the authors of the following add-ons:
* Instant Translate - Alexy Sadovoy, Beqa Gozalishvili, Mesar Hameed, Alberto Buffolino and other NVDA contributors.
* To work with voice synthesizers profiles were used ideas from the Switch Synth add-on (thanks to Tyler Spivey).

## Change log

### Version 1.2
* Added the ability to automatically switch voice synthesizers for selected languages;
* added the ability to download the current list of languages available in the online-dictionary;
* Turkish translation added thanks to Cagri Dogan;

### Version 1.1
* changed some keyboard shortcuts which conflicted with other add-ons;
* changed the description of the main add-on features;
* updated help and translation of the add-on;
* removed some keyboard shortcuts and gave to user opportunity to setup them yourself;
* Fixed error in Ukrainian translation (thanks to Volodymyr Perig);
* added russian translation.

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

[1]: https://github.com/grisov/quickDictionary/releases/download/v1.2/quickDictionary-1.2.nvda-addon
[2]: https://github.com/grisov/quickDictionary/releases/download/v1.2/quickDictionary-1.2.nvda-addon
