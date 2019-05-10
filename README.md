# Twicorder Search
A Twitter crawler for Python 3 based on Twitter's public API

## Installation
```bash
pip install twicorder-search
```

## Config
### Environment variables
Twicorder relies on environment variables for Twitter API authentication. Before starting the application, make sure you have set the following environment variables:

```
CONSUMER_KEY
CONSUMER_SECRET
ACCESS_TOKEN
ACCESS_SECRET
```
### preferences.yaml
```yaml
# Save location, file name and extension for collected data
save_dir: "~/Twicorder"
save_extension: ".zip"

# How often this config will be reloaded by the listener (minutes)
config_reload_interval: 15

# Additionally store tweets in MongoDB
use_mongo: False

# For every tweet with mentions, look up each mention's full user data
full_user_mentions: True

# When performing user lookups, cache the user and don't check again for this
# interval (minutes)
user_lookup_interval: 15

```
Use this file to configure how the application runs. Set the output directory, file format, whether to expand user data for mentions etc
### tasks.yaml
```yaml
user_timeline:
  - frequency: 60
    output: "github/timeline"
    kwargs:
      screen_name: github

free_search:
  - frequency: 60
    output: "github/mentions"
    kwargs:
      q: "@github"
  - frequency: 60
    output: "github/replies"
    kwargs:
      q: "to:github"
  - frequency: 60
    output: "github/hashtags"
    kwargs:
      q: "#github"
```

Use this file to define the queries you wish to run and where to store their output data, relative to the output directory. Frequency is given in minutes and defines how often a new scan will be triggered for the given query.

