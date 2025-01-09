#!/usr/bin/python3
import os
import requests
import json
import yaml
import re
from bs4 import BeautifulSoup

from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
#from gcsa.recurrence import Recurrence, DAILY, SU, SA

from datetime import datetime, timedelta

# Functions
def get_lambgoat_releases(url: str) -> dict:
    # fetches the URL and converts <table> with releases into dictionary (json)
    releases = []

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
    except:
        print("Exception when fetching lambgoat")
        return releases
    
    rows = soup.find_all("tr")
    for row in rows:
        release = []
        cells = row.find_all("td")
        for cell in cells:
            #print(cell.text)
            if cell.text:
                release.append(cell.text)
        releases.append(release)

    return releases
    # 0 = date
    # 1 = band name
    # 2 = Album
    # 3 = Label

def get_theprpr_releases(url: str) -> dict:
    # fetches the URL and coverts div/span tags into dictionary (json)
    releases = []

    # theprp.com is blocking requests library default user-agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
    except:
        print("Exception when fetching lambgoat")
        return releases
    
    rows = soup.find_all("div", class_="rel_row")
    for row in rows:
        release = []
        cells = row.find_all("span")
        for cell in cells:
            if cell.text != "":
                #print(cell.text.replace("/25", "/2025")) # this is very dirty trick to replace date "01/01/24" with "01/01/2024"
                #release.append(cell.text.replace("/25", "/2025")) # this is very dirty trick to replace date "01/01/24" with "01/01/2024"
                cell_text = expand_date_if_short_year(cell.text)
                print(cell_text) # debug
                release.append(cell_text)
                
        releases.append(release)

    return releases

def remove_past_releases(releases: list) -> list:

    future_releases = []
    current_date = datetime.now()
    for release in releases:
        release_date = datetime.strptime(release[0], '%m/%d/%Y')
        if release_date >= current_date:
            future_releases.append(release)
    
    return future_releases

def create_release_event(calendar, release, tags):

    bullshit_genres = ["seen live", "pop", "soul", "rnb", "house", "instrumental"]

    tags_formatted = ""
    tags_clean = []
    i = 0
    while i < len(tags):
        if tags[i] not in bullshit_genres:
            tags_formatted = tags_formatted + tags[i] + ", "
            tags_clean.append(tags[i])
        i += 1
        if i >= 3: # only 3 tags
            break
    
    tags_formatted = tags_formatted.rstrip(", ")

    if tags_clean:
        event_name = "{} - {} [{}]".format(release[1], release[2], tags_clean[0])
    else:
        event_name = "{} - {}".format(release[1], release[2])

    datetime_object = datetime.strptime(release[0], '%m/%d/%Y')

    event = Event(
        event_name,
        description="Artist: {}\nAlbum: {}\nLabel: {}\nGenres: {}\n".format(release[1], release[2], release[3], tags_formatted),
        start=(datetime_object),
        end=(datetime_object + timedelta(days=1))
    )
    print("Creating event: {}".format(event_name))
    calendar.add_event(event)

def get_artist_tags_from_last_fm(artist: str, api_key: str, api_url: str) -> list:

    tags = []

    headers = {
        'user-agent': "python/requests"
    }

    payload = {
        'api_key': api_key,
        'method': 'artist.getinfo',
        'format': 'json',
        'artist': artist
    }
    try:
        response = requests.get(api_url, headers=headers, params=payload)
        response_json = response.json()
    except:
        print("Exception when fetching last.fm ocurred")
        return tags

    if response.status_code != 200:
        print("Non-200 status code: {}".format(response.status_code))
        return tags

    if 'error' in response_json:
        print("Error from last.fm API when fetching {} info: {}".format(artist, response_json['message']))
        return tags
    
    for tag in response_json['artist']['tags']['tag']:
        tags.append(tag['name'])

    return tags

def expand_date_if_short_year(date_str):
    # Regular expression to match the format DD/MM/YY
    pattern = r'^\d{2}/\d{2}/\d{2}$'

    # Check if the date string matches the pattern
    if re.match(pattern, date_str):
        # Find the last '/' to isolate the year
        last_slash_index = date_str.rfind('/')

        # Extract the two-digit year
        two_digit_year = date_str[last_slash_index + 1:]

        # Prepend '20' to the two-digit year
        expanded_year = '20' + two_digit_year

        # Construct the new date string
        expanded_date = date_str[:last_slash_index + 1] + expanded_year

        return expanded_date

    # Return the original string if it does not match the format
    return date_str

# Main body
if __name__ == "__main__":

    # FEATURE FLAGS
    enable_calendar_event_creation = True
    clean_calendars = False

    # config
    with open("config.yml", "r") as config_file:
        CONFIG = yaml.load(config_file, Loader=yaml.FullLoader)

    releases = get_lambgoat_releases(CONFIG["lambgoat"]["url"])
    theprp_releases = get_theprpr_releases(CONFIG["theprp"]["url"])
    print(theprp_releases)

    future_releases = remove_past_releases(releases)
    future_theprp_releases = remove_past_releases(theprp_releases)
    # TEMPORARY - POPULATING THE CALENDAR WITH PAST EVENTS SO WE DON"T FILTER TEMPORARILY
    #future_releases = releases
    # TEMPORARY

    calendar = GoogleCalendar(CONFIG["gcal"]["id"])
    hardcore_calendar = GoogleCalendar(CONFIG["gcal"]["hardcore_id"])
    death_calendar = GoogleCalendar(CONFIG["gcal"]["death_id"])
    black_calendar = GoogleCalendar(CONFIG["gcal"]["black_id"])
    theprp_calendar = GoogleCalendar(CONFIG["gcal"]["theprp_id"])

    #collect all future events in common calendar - I use it as source of truth even for genre calendars
    releases_in_calendar = []
    for event in calendar:
        event_summary_without_genres = re.sub(' \[.*\]$', '', event.summary)
        releases_in_calendar.append(event_summary_without_genres)

    releases_in_theprp_calendar = []
    for event in calendar:
        event_summary_without_genres = re.sub(' \[.*\]$', '', event.summary)
        releases_in_calendar.append(event_summary_without_genres)

    # this is where the things happens
    events_created_count = 0
    hardcore_events_created_count = 0
    black_events_created_count = 0
    death_events_created_count = 0
    theprp_events_created_count = 0

    if enable_calendar_event_creation: # feature flag - change to False to stop creating events

        for release in future_theprp_releases:
            release_full_name = release[1] + " - " + release[2]

            if release_full_name not in releases_in_theprp_calendar:

                tags = get_artist_tags_from_last_fm(release[1], CONFIG["last_fm"]["api_key"], CONFIG["last_fm"]["api_url"])

                create_release_event(theprp_calendar, release, tags)
                theprp_events_created_count += 1
        
        print("Total {} THEPRP event(s) created.".format(theprp_events_created_count))

        for release in future_releases:
            release_full_name = release[1] + " - " + release[2]

            if release_full_name not in releases_in_calendar:

                tags = get_artist_tags_from_last_fm(release[1], CONFIG["last_fm"]["api_key"], CONFIG["last_fm"]["api_url"])

                hardcore_event_created = False
                black_event_created = False
                death_event_created = False

                for tag in tags:
                    if "core" in tag and not hardcore_event_created:
                        create_release_event(hardcore_calendar, release, tags)
                        hardcore_events_created_count += 1
                        hardcore_event_created = True
                    if "black" in tag and not black_event_created:
                        create_release_event(black_calendar, release, tags)
                        black_events_created_count += 1
                        black_event_created = True
                    if "death" in tag and not death_event_created:
                        create_release_event(death_calendar, release, tags)
                        death_events_created_count += 1
                        death_event_created = True
                    if hardcore_event_created and black_event_created and death_event_created: # we don't have to continue looping the tags if we've already created event in all 3 genre calendars
                        break

                create_release_event(calendar, release, tags)
                events_created_count += 1
    
    print("Total {} event(s) created.".format(events_created_count))
    print("Total {} hardcore event(s) created.".format(hardcore_events_created_count))
    print("Total {} black event(s) created.".format(black_events_created_count))
    print("Total {} death event(s) created.".format(death_events_created_count))

    ### REMOVE ALL EVENTS FLAG ###
    if clean_calendars:

        # for event in calendar.get_events(datetime(2021, 1, 1),datetime(2021, 12, 12)):
        #     calendar.delete_event(event.event_id)

        # for event in hardcore_calendar.get_events(datetime(2021, 1, 1),datetime(2021, 12, 12)):
        #     hardcore_calendar.delete_event(event.event_id)

        # for event in death_calendar.get_events(datetime(2021, 1, 1),datetime(2021, 12, 12)):
        #     death_calendar.delete_event(event.event_id)

        # for event in black_calendar.get_events(datetime(2021, 1, 1),datetime(2021, 12, 12)):
        #     black_calendar.delete_event(event.event_id)

        for event in theprp_calendar.get_events(datetime(2025, 1, 1),datetime(2025, 12, 12)):
            theprp_calendar.delete_event(event.event_id)
