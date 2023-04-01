# Shoes testing
Long story short: my boyfriend runs. A lot. And he's good at it. So he tests running gears such as shoes. And he needs to keep track of his runs with the gear he's testing.  
This repo contains a codebase that extracts activities from Strava and uploads data into a Google Spreadsheets that looks like this:
```

+-----------+---------------+-------------------+--------------------+---------------------+----------------------+------------+---------------+-----------------+
|   Name    | Distance (km) | Moving time (min) | Elapsed time (min) | Total elevation (m) |      Start date      |     ID     | Average speed | Average cadence |
+-----------+---------------+-------------------+--------------------+---------------------+----------------------+------------+---------------+-----------------+
| Lunch Run |         13,67 |             74,18 |              77,23 |               132,9 | 2023-03-26T11:12:18Z | 8779455702 |         11,06 |           166,4 |
+-----------+---------------+-------------------+--------------------+---------------------+----------------------+------------+---------------+-----------------+

```

Here's how to get the needed credentials.

### Google spreadsheet
To use the code, you need to create a project in [Google Cloud](https://console.cloud.google.com/). You'll then need to generate an OAuth 2.0 client ID for a desktop application.  
Download the json file containing the credentials and put it into the `sheet` directory.  
You'll also need to create a spreadsheet and to put the ID (that can be found in the URL) in `retrieve_data.py`.

### Strava
Create a [Strava app](https://www.strava.com/settings/api) and create a `credentials.json` file in the `strava` directory containing the following data:
```json
{
    "client_id": CLIENT_ID,
    "auth_uri": "https://www.strava.com/oauth/authorize/",
    "token_uri": "https://www.strava.com/oauth/token",
    "client_secret": CLIENT_SECRET,
    "redirect_uris":
    [
        "http://localhost"
    ]
}
```
The first you run the code, this will open a prompt asking you to accept some stuff. Your refresh token will be saved until it expires, at which point the prompt will open again and so on.