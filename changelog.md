## Version 2.2.4

### Changed

- The add-on has been updated to the latest NVDA add-on template.
- The translations of the add-on are now managed in Crowdin, in the community project for translating NVDA add-ons.
- The code has been updated for Python 3.13 and the strict code checks of the add-on template.
- Tested with NVDA 2026.3.

### Fixed

- The add-on turned off the verification of HTTPS certificates for the whole NVDA, e.g. for the NVDA Add-on Store and the other add-ons. It now concerns only the requests of its online dictionaries.
- The Yandex dictionary entries with an empty list of meanings or synonyms and the Lexicala entries with several translations into the target language could not be shown.
- The voice synthesizer profiles created without settings shared the same settings.
- An error on NVDA exit when the settings panel of the add-on had already been removed.
