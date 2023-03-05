# new hc/metal releases to google calendar

Script for scraping Lambgoat new releases and putting them into public calendar. Meant to be run as cron on per-month or per-week basis.

## How to use

 1. Clone the rpo

 2. Create google calendar and get the ID:
   - https://calendar.google.com
   - click three dots next to calendar name -> Calendar settings
   - scroll almost to the bottom of the page to get the ID of calendar. It comes in `xyz@group.calendar.google.com` format.

 2. generate API credentials for Google Calendar: 
   - https://developers.google.com/calendar/api/quickstart/python
   - You need to create `Desktop` application
   - You can't use the application unless
   - on `Oauth consent screen` you must publish the application to production otherwise you're not able to use it
   - get credentials from `Credentials` screen
   - credentials must be in `~/.credentials/credentials.json`

 3. Generate API credentials for last.fm (you'll find guide on internet)

 4. Create `config.yml` file in the directory with the script in following format:

```
    last_fm:
      api_url: "https://ws.audioscrobbler.com/2.0/"
      api_key: "LAST_FM_API_KEY"
    lambgoat:
      url: "https://lambgoat.com/albums/releases/2023"
    gcal:
      id: "a@group.calendar.google.com"
      hardcore_id: "b@group.calendar.google.com"
      death_id: "c@group.calendar.google.com"
      black_id: "d@group.calendar.google.com"
```

 4. Run manually: `python3 new-hc-metal-releases-to-calendar.py` 

 5. Every day at 10 AM: `0 10 * * * cd /Users/username/new-hc-metal-releases-to-calendar/ && /usr/bin/python3 new-hc-metal-releases-to-calendar.py >cron.log 2>cron.log`

## TODO

 - 'artist country' in summary
 - 'for fans of' in summary
 - improve how genre calendars are treated - lots of copy pasting, must be possible to disable
 - 2023 lambgoat page is hardcoded - there is no way how to show all future releases so we should iterate over current year + next year release page not to miss future year's early releases