Simple Access
==
A simple access system built around tidy club

Video to prototype - https://goo.gl/photos/FiFTz3ucazfKPxP98

Security Considerations
--
This works like nearly every other access card system used in commercial environments. Card ID is checked against the database to see if the user auth'd. This means any NFC/mifare compliant card should be able to be used, such as public transport cards and body implants. Because only the card id is checked it is possible for cards to be cloned easily. This should be discouraged via administration of your club via rules / penalties. Furthermore video recordings are recommended for entry and exit locations.

A more advanced version may be introduced that writes a series of tokens or authentication system onto the card each read.

Such as a sha2(salt + an incrementing nonce) and store the nonce unencrypted on the card as well so that offline databases can see where the nonce is up to and only trust future auths. It still wouldn't be perfect but it would be close enough.

Requirements
--
  - pytidyclub with membership additions - https://bitbucket.org/theskorm/pytidyclub-1
  - libnfc
  - pynfc (https://github.com/ikelos/pynfc)
  - pygame
  - python dataset (pip install dataset)
  - python requests (pip install requests[security] )
  - libnfc device configured not to scan(takes up time) and configured to work (nfc-poll should work)
  - Composite video out

Setup
--

1. Install requirements
1. Setup api keys in tidy club application prefs
1. Add a cusotm field in tidyclub for tagID
1. edit access.py and tidyclubupdater.py with database details
1. Run python tidyclubupdater.py and fill out details
1. Add tidyclubupdater.py to cron to update member details regularly.
1. Run python access.py
