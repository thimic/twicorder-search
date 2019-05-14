# Twicorder Search
A Twitter crawler for Python 3 based on Twitter’s public API.

[![DOI](https://zenodo.org/badge/185946239.svg)](https://zenodo.org/badge/latestdoi/185946239)

## Installation
Twicorder Search can be installed using PIP:

```bash
pip install twicorder-search
```

For a more comprehensive guide using a virtual environment, see [Installation using Python 3 virtual environments](../master/INSTALL.md)

## Running Twicorder Search
After installing, there will be a new executable available, `twicorder`. Use this to run the application:
```bash
twicorder
```

To specify a project directory, other than the default, use the flag `--project-dir`:

```bash
twicorder --project-dir /path/to/my_project
```

## Config
Twicorder Search requires two config files to be set up before it will run - `preferences.yaml` and `tasks.yaml`. Both files must be created and installed to the project directory. Correct layout of the project directory is:

```bash
PROJECT_ROOT
└── config
    ├── preferences.yaml
    └── tasks.yaml
```

### API credentials
Twicorder has two ways of setting API credentials. They can either be set in the config file as seen below, or set as environment variables:

```
CONSUMER_KEY
CONSUMER_SECRET
ACCESS_TOKEN
ACCESS_SECRET
```

### preferences.yaml

```yaml

# API Login credentials
consumer_key:
consumer_secret:
access_token:
access_secret:

# Save location, file name and extension for collected data
save_dir:
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

# (Advanced) Number of seconds Twicorder will wait for write locks to be
# released on its internal data store
appdata_connection_timeout: 5.0

```

Use this file to configure how the application runs. Set the output directory, file format, whether to expand user data for mentions etc

### tasks.yaml

```yaml

# Tasks
#
# Queries are added on the form listed below.
#
# free_search:                  # endpoint name
#   - frequency: 60             # Interval between repeating queries in minutes
#     output: github/mentions   # Output directory, relative to project directory
#     kwargs:                   # Keyword Arguments to feed to endpoint
#       q: @github              #   "q" for "query" in the case of free_search
#
# See https://developer.twitter.com/en/docs/tweets/search/guides/standard-operators
# for how to use free search to find mentions, replies, hashtags etc.
#
# See https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
# for keyword arguments to use with search.
#
# See https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline
# for keyword arguments to use with user timelines.

user_timeline:
  - frequency: 60
    output: "github/timeline"
    kwargs:
      screen_name: "github"
  - frequency: 120
    output: "nasa/timeline"
    kwargs:
      screen_name: "NASA"

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
