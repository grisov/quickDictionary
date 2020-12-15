# NVDA Quick Dictionary

* Author: Oleksandr Gryshchenko
* Version: 2.0
* Download [stable version][1]
* Download [development version][2]

Welcome to NVDA Quick Dictionary addon, which will allow you to quickly get a dictionary article with the translation of a word or phrase into your chosen language by pressing a key combination. There are few basic keyboard shortcuts and they are all intuitive and convenient so you will remember them quickly.  
Dictionary articles contain detailed information about a word, such as part of speech, gender, plural or singular, translation options, list of meanings, synonyms and detailed examples. Such information will be useful for people who are learning foreign languages, or seek to use in communication all the richness and diversity of their own language.  
The add-on supports several online dictionary services. You can select the desired remote dictionary in the appropriate dialog box or by using keyboard shortcuts. Each available service has its own settings panel.  
There are also advanced opportunities for working with profiles of the voice synthesizers. You can associate a voice synthesizer profile with a specific language, after that translations into this language will be automatically voiced by the selected synthesizer.  
Below are all the features of the add-on and keyboard shortcuts to control them. By default all functions are called using two-layer commands. But for any of these methods you can always assign convenient for you keyboard shortcuts. You can do it in the NVDA "Preferences" -> "Input gestures..." dialog.  

## Receiving a dictionary article
In order to get an article from the dictionary, you must first select the word you are interested in or copy it to the clipboard. Then just press NVDA+Y twice.
There is also another way to get a dictionary entry: pressing NVDA+Y once switches the keyboard to add-on control mode, then just use the D key.

Note: Before making a request to a remote service, the add-on must receive a word or phrase that interests the user. The sequence of actions that add-on performs each time before accessing the dictionary:
* receive the selected text and execute the request;
* if there is no selected text - receive the text content of the clipboard and execute the request;
* if the clipboard is empty or its content is not text data - the add-on notifies the user and does not take further action.

## Add-on control mode
To access all the features of the add-on, you need to switch to add-on control mode, you can do this by pressing NVDA+Y once. You will hear a short low beep and will be able to use the other commands described below. When you press a key that is not used in the add-on, you will hear another signal notifying you of an erroneous command and the add-on control mode will be automatically turned off.

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

## Text preparation
Sometimes it is necessary to change the text before sending it for translation, or just enter the text yourself.
To do this, you can use the text pre-edit command - press the E key in the add-on control mode (NVDA+Y). A dialog box opens with a multi-line field for editing text. After editing, just press Ctrl+Enter or the corresponding button.

The following commands are also available in the edit field:
* Ctrl+A - select all;
* Ctrl+E - clear text from non-alphabetic characters;
* Ctrl+R - clear editor field;
* Ctrl+U - restore original text.

Note: If before calling the dialog for editing text, the text was previously selected or copied to the clipboard, then it will be placed in the editor field in this dialog.

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

## Choosing an online service
There are several ways to select a remote dictionary to send queries from the add-on.
* Using the NVDA menu: press NVDA+N, go to the "Tools" submenu, then - "Quick Dictionary" and activate the command "Select online service...". After that a dialog box will appear for selecting a remote service. In this dialog, use the up or down keys to navigate to the desired item and press Enter. Or just press the number that corresponds to the ID of the online service you are interested in.
* The service selection dialog can also be called by pressing the F key in the add-on control mode.
* Each available service is also assigned a function key starting from F1 in the add-on control mode.
* Finally, the service can be selected directly in the add-on settings panel.

Note: Each online service has its own settings panel and all its parameters are stored separately.

## Information about the selected service
By pressing Q in the add-on control mode, you can listen to the following data:
* name of the selected online service;
* number of supported languages;
* dictionary section (if supported);
* statistics and using limits of the current service;
* state of the cache (hits/misses/size/used).

## Add-on settings dialog
To change the add-on parameters you need to open the dialog box of its settings. This can be done this way: press NVDA+Y and then the key O.  
The standard NVDA settings dialog with the open section of our add-on will appear on the screen.  
You can also open this dialog via the NVDA menu: press NVDA+N, go to the "Tools" submenu, then "Quick Dictionary" and activate menu item "Options...".

### Choose an online service
When you open the add-on settings dialog, the NVDA cursor is immediately placed on the drop-down list of online service selection. You can select the service from the list and press Enter or Tab to go to the next parameter.  
As mentioned above - each service has its own settings panel. Therefore, all subsequent parameters for each service may be different. Consider the most common of them.

### Choice of languages for translation
In the list of source languages, use the up or down keys to select the desired language and press Tab to move to the selection of the target language.

Note:
* The list of available target languages depends on the selected source language, so the target language should only be selected after the source language is set.
* In some services, the lists of available languages are depend on the selected section of the dictionary.

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
After that, upon receipt of the translation, associated voice synthesizers will be automatically switched for each specified language.  
To manage the profiles, you can use keyboard commands or the corresponding dialog box. To open a dialog with a list of voice synthesizers profiles - press NVDA+N, go to the "Tools" submenu, then - "Quick Dictionary" and activate the command "Voice synthesizers profiles..." or just press the P key in the add-on control mode (NVDA+Y).

### Creating a voice synthesizer profile
You can create up to 9 configuration profiles for the various voice synthesizers available in NVDA.  
To switch between profiles, use the number keys 1 to 9 in the add-on control mode.

For example, to create a profile number 5, follow these steps:
1. Switch to add-on control mode using NVDA+Y.
2. Press the 5 key. You will hear a message that the selected profile is number 5.
3. Go to the "Speech" section of the NVDA settings using NVDA+Ctrl+V and configure the desired voice synthesizer to be saved in the selected profile. Then press "Ok" button.
4. Save the configured synthesizer in the selected profile - press NVDA+Y and then V. You will hear a message about the successful saving of the voice synthesizer profile.

Note: You can also perform this and other operations in the dialog "Voice Synthesizers Profiles...".

### Activate voice synthesizer by default
To return to using the voice synthesizer that was set when NVDA started, press NVDA+Y, then press R. This will restore the default voice synthesizer and you will hear its name and the selected voice.

### Switch between profiles
As mentioned earlier, you can switch between voice synthesizers profiles using the number keys in the add-on control mode.  
If the profile already has previously saved voice synthesizer settings, the corresponding voice will be activated and you will hear a message with information about the number of the activated profile, the name of the synthesizer and the name of the voice. Otherwise, if the selected profile does not yet contain any data - a message will be displayed only about its number and the synthesizer will not switch.

Note: In either case, you can return to default voice using the R key in add-on control mode (NVDA+Y).

### Switch to the previous voice synthesizer
You can quickly return to the previous voice synthesizer by pressing the B key in the addon control mode.

### Notification of the currently selected profile
To hear which profile is currently selected, use the G key in add-on control mode (NVDA+Y).  
If the profile contains voice synthesizer settings, the name of the synthesizer and voice will be announced in addition to the number. Otherwise, you will only hear the active profile number.

### Delete settings from the selected profile
To delete the voice synthesizer settings from the currently selected profile, use the Delete key in add-on control mode (NVDA+Y).  
You will hear a message about the successful deletion of the profile with the specified number.

### Save changes
After each manipulation of the profile (create/update/delete) it is necessary to save changes using V key in the add-on control mode (NVDA+Y).  
By pressing this key you will hear the message about successful saving of the changes.

### Dialog "Voice Synthesizers Profiles"
You can open a dialog with a list of voice synthesizers profiles from the NVDA menu - press NVDA+N, go to the "Tools" submenu, then - "Quick Dictionary" and activate the item "Voice synthesizers profiles..." or just press the P key in add-on control mode.  
For each profile in list specified its number, synthesizer name, voice name, and the language associated with that profile.  
To activate a profile, go to it with up or down arrow keys and press Enter, or just press the number that corresponds to the profile number.  
Other operations with voice synthesizers profiles are also available in the specified dialog. To perform one of the following actions - go to the corresponding button in the dialog or use the key indicated in brackets:
* create new profile (F7)
* change selected profile (F4)
* delete selected profile (F8 or Delete)
* refresh the list (F5)
* save changes (F2)

Note: By default, the associated language is set to "- Immutable language -". This means that switching to this synthesizer will not be performed. The process of changing the associated language for each profile will be described below.

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
After making the above settings, the voice synthesizer of your choice will automatically turn on when you receive data from the dictionary. And after the announcement of the article, the previous synthesizer will turn on again.

Note: If for some reason switching to the previous voice synthesizer didn't happen - you can do it manually by pressing the B or R key in the add-on control mode.

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

### Version 2.0.2
* added a dialog to edit the text before sending to remote service;
* separated add-on help page from ReadMe;
* Turkish translation added (thanks to Cagri Dogan).

### Version 2.0
* added the ability to connect other online dictionary services;
* added Lexicala service and its settings panel;
* added a dialog for choosing an online service from the list of available ones;
* added a command to get information about the selected service;
* added a dialog for working with profiles of voice synthesizers;
* implemented the procedure for switching to the previous voice synthesizer;
* implemented a parallel thread to monitor the state of the synthesizer;
* due to an increase in the number of functions in the add-on - help for commands is now displayed in a separate window;
* updated procedure for caching requests to online services;
* added add-on submenu to NVDA menu;
* updated ReadMe.

### Version 1.2
* added the ability to automatically switch voice synthesizers for selected languages;
* added the ability to download the current list of languages available in the online-dictionary;
* Turkish translation added thanks to Cagri Dogan.

### Version 1.1
* changed some keyboard shortcuts which conflicted with other add-ons;
* changed the description of the main add-on features;
* updated help and translation of the add-on;
* removed some keyboard shortcuts and gave to user opportunity to setup them yourself;
* fixed error in Ukrainian translation (thanks to Volodymyr Perig);
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

[1]: https://github.com/grisov/quickDictionary/releases/download/v2.0/quickDictionary-2.0.nvda-addon
[2]: https://github.com/grisov/quickDictionary/releases/download/v2.0/quickDictionary-2.0.nvda-addon
