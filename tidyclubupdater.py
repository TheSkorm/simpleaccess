# pip install dataset
# pip install pytidyclub (https://bitbucket.org/theskorm/pytidyclub-1/src/bb28254e30a01161c3a14cf19a4d5bd0829f9604?at=theskorm/added-membership-lookup-1439467378850)

from pytidyclub import pytidyclub
from datetime import datetime
import argparse
import dataset
import traceback

#this script updates the database with the tidy club details.

# TODO
#
# Email alerts when something goes wrong.

#sqlite is fine for testing however a real database is needed if you want this to run at the same time as the access control system
db = dataset.connect('sqlite:///test.db')

parser = argparse.ArgumentParser(description='Simple Access System using TinyClub')
parser.add_argument('--reauth', help='Resets auth tokens', action="store_true")
parser.add_argument('--reset', help='Resets', action="store_true")
args = parser.parse_args()

config = db['config']

if not config.find_one(name='token') or args.reauth or args.reset:
    if not config.find_one(name='slug') or not config.find_one(name='client_id') or not config.find_one(name='client_secret') or args.reset:
        config.upsert(dict(name='slug', value=raw_input("slug: ")),"name")
        config.upsert(dict(name='client_id', value=raw_input("client_id: ")),"name")
        config.upsert(dict(name='client_secret', value=raw_input("client_secret: ")),"name")
    club = pytidyclub.Club(
        slug = config.find_one(name='slug')["value"],
        client_id = config.find_one(name='client_id')["value"],
        client_secret = config.find_one(name='client_secret')["value"]
    )
    print club.auth_authcode_get_url("urn:ietf:wg:oauth:2.0:oob")
    club.auth_authcode_exchange_code(raw_input("Click the link above and enter the code here: "), "urn:ietf:wg:oauth:2.0:oob")
    config.upsert(dict(name='token', value=club.token),"name")
else:
    club = pytidyclub.Club(
        slug = config.find_one(name='slug')["value"],
        client_id = config.find_one(name='client_id')["value"],
        client_secret = config.find_one(name='client_secret')["value"]
    )
    club.token = config.find_one(name='token')["value"]
    club.authorized = True

contacts = club.contacts()

members =[] #we want to cache all the members we grab off tidy club and import into the DB at once
#pytidyclub isn't very pythonic so we need to tame it
for contact in contacts:
    member = { "id": contact['id'], "firstname": contact['first_name'], "lastname": contact['last_name']} #just grab the details we need
    tags = contact['custom_fields']
    for tag in tags:
        if tag["title"] == "tagID":
            member['tagid'] = tag["value"]

    memberships = club.memberships(contact=contact['id'])
    dates = []
    for membership in memberships:
        # if membership['state'] == "activated": ## only activated memberships allowed - if we do this we can't warn about expiring users
        dates.append(datetime.strptime(membership['end_date'],"%Y-%m-%d"))
    dates = sorted(dates)
    if len(dates) > 0:
        member["expires"] = dates[-1]  #take the furthest out expiry date
    members.append(member)

db['members'].delete() # delete everyone from db
for member in members:
    db['members'].insert(member)
