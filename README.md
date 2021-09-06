# Twicorder Search
A Twitter crawler for Python 3 based on Twitter’s public API.

[![DOI](https://zenodo.org/badge/185946239.svg)](https://zenodo.org/badge/latestdoi/185946239)

## Supported end points
Twicorder Search currently supports the following end points:

* `/1.1/followers/ids`
* `/1.1/friends/list`
* `/1.1/search/tweets`
* `/1.1/statuses/lookup`
* `/1.1/statuses/user_timeline`
* `/1.1/users/lookup`

To add a new end point, fork the repository and add a new query type to 
`src/twicorder/queries/request/endpoints`. New endpoints should inherit from 
`BaseQuery` or one of its derivatives and must implement `name`, `endpoint` and 
`result_type`.

## Installation
Twicorder Search can be installed using PIP:

```bash
pip install twicorder-search
```

For a more comprehensive guide using a virtual environment, see 
[Installation using Python 3 virtual environments](../main/INSTALL.md)

## Running Twicorder
After installing, there will be a new executable available, `twicorder`. Use this to run the 
application:
```bash
$ twicorder
Usage: twicorder [OPTIONS] COMMAND [ARGS]...

  Twicorder Search

Options:
  --project-dir TEXT  Root directory for project
  --help              Show this message and exit.

Commands:
  run    Start crawler
  utils  Utility functions

```

The project dir is where Twicorder stores temporary files and logs. To specify a project directory 
other than the default, use the flag `--project-dir`.:

```bash
$ twicorder --project-dir /path/to/my_project
```

If not provided, the current working directory is used.

## Configuration
Twicorder can be configured by passing parameters in the command line interface or by setting 
environment variables. The environment variables are laid out similar to their CLI counterparts.

**Specifying a task generator with CLI**
```bash
$ twicorder run --task-gen user_timeline 
```

**Specifying a task generator with environment variable**
```bash
$ export TWICORDER_RUN_TASK_GEN="user_timeline"
```

Full list of CLI options:

```bash
$ twicorder run --help
Usage: twicorder run [OPTIONS]

  Start crawler

Options:
  --consumer-key TEXT             Twitter consumer key  [required]
  --consumer-secret TEXT          Twitter consumer secret  [required]
  --access-token TEXT             Twitter access token  [required]
  --access-secret TEXT            Twitter access secret  [required]
  --out-dir TEXT                  Custom output dir for crawled data
  --out-extension TEXT            File extension for crawled files (.txt or
                                  .zip)
  --task-file TEXT                Yaml file containing tasks to execute
  --full-user-mentions            For mentions, look up full user data
  --appdata-token TEXT            App data token
  --user-lookup-interval INTEGER  Minutes between lookups of the same user
                                  [default: 15]
  --appdata-timeout FLOAT         Seconds to timeout for internal data store
                                  [default: 5.0]
  --task-gen <TEXT TEXT>...       Task generator(s) to use. Example: "user_id
                                  name_pattern=/tmp/**/*_ids.txt,delimiter=,"
                                  [default: config]
  --remove-duplicates             Ensures duplicated tweets/users are not
                                  recorded. Saves space, but can slow down the
                                  crawler.  [default: True]
  --help                          Show this message and exit.

```

## Task generators

Twicorder can be configured with one or more task generators for creating API requests. 

### Tasks file
The tasks file is the default task generator for Twicorder and is used when no generator is 
specified. By default Twocorder searches the project root for a file called `tasks.yaml`.

```bash
PROJECT_ROOT
 ├── appdata
 │   └── twicorder.sql
 ├── logs
 │   └── twicorder.log
 └── tasks.yaml
```

It is however possible to specify a different file path using `--task-file`:

```bash
$ twicorder --task-file /path/to/my_file.yaml
```

#### Example tasks.yaml file

Use this file to define the queries you wish to run and where to store their output data, relative 
to the output directory. Frequency is given in minutes and defines how often a new scan will be 
triggered for the given query.

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

### User Lookup

The User Lookup generator takes one or more files with delimited user ids or 
user names as input. It then generates tasks to fetch user objects for each id 
or user name.

```bash
$ twicorder run --task-gen user_lookups name_pattern=/taskgen/*.txt,lookup_method=username
```

| Keyword Argument | Type  | Description                |
| ---------------- | ----- | -------------------------- |
| `name_pattern`   | `str` | POSIX style search pattern |
| `delimiter`      | `str` | Default: `"\n"`            |
| `lookup_method`  | `str` | `"id"` or `"username"`     |

### User Timeline

The User Timeline generator takes one or more files with delimited user ids or 
user names as input. It then generates tasks to fetch tweets for each user's 
timeline.

```bash
$ twicorder run --task-gen user_timeline name_pattern=/taskgen/*.txt,lookup_method=id,max_requests=5 
```

| Keyword Argument | Type  | Description                                                            |
| ---------------- | ----- | ---------------------------------------------------------------------- |
| `name_pattern`   | `str` | POSIX style search pattern                                             |
| `delimiter`      | `str` | Default: `"\n"`                                                        |
| `lookup_method`  | `str` | `"id"` or `"username"`                                                 |
| `max_requests`   | `int` | Max number of requests before the task is considered done              |
| `max_age`        | `int` | Max age in days for a tweet before the query should be considered done |

## Create new task generator

Twicorder supports creating custom task generators. To create a generator, create a class that inherits from `BaseTaskGenerator` and 
implement the `name` class attribute and the `fetch()` method. See 
`twicorder/tasks/generators/user_lookup_generator.py` for an example.

Place the custom task 
generator in a suitable directory and point to said directory with the 
environment variable `TWICORDER_TASKGEN_PATH`:

```bash
export TWICORDER_TASKGEN_PATH="/path/to/my/generator_dir"
```

The task generator file name must end in `_generator.py`:

```bash
$TWICORDER_TASKGEN_PATH
 ├── __init__.py
 └── custom_task_generator.py
```

## Clearing temporary files or logs

Use the `utils` command to clean up temporary files and logs:

```bash
$ twicorder utils --help
Usage: twicorder utils [OPTIONS]

  Utility functions

Options:
  --clear-cache  Clear cache and exit
  --purge-logs   Purge logs and exit
  --help         Show this message and exit.

```

## Docker

### Docker Compose Examples

Crawl data based on entries in the [tasks file](#tasks-file).

```yaml
version: "3"

services:
  twicorder-search:
    build: ./
    image: twicorder-search:dev
    restart: unless-stopped
    container_name: twicorder-search
    network_mode: bridge
    environment:
      - TWICORDER_RUN_CONSUMER_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_CONSUMER_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_ACCESS_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_ACCESS_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_REMOVE_DUPLICATES=0
      - TWICORDER_RUN_APPDATA_TOKEN=search
    volumes:
      - /home/user/project/data:/data
      - /home/user/project/config:/config
```

Crawl tweets using the `user_timeline` task generator. The generator reads all *.txt files located 
in `/home/user/project/taskgen` on the host system (`name_pattern=/taskgen/*.txt`) and expects to 
find one user ID (`lookup_method=id`) per line. For each user the number of page results are limited 
to 5 (`max_requests=5`).

```yaml
version: "3"

services:
  twicorder-timeline:
    build: ./
    image: twicorder-timeline:dev
    restart: on-failure
    container_name: twicorder-timeline
    network_mode: bridge
    environment:
      - TWICORDER_RUN_CONSUMER_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_CONSUMER_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_ACCESS_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_ACCESS_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      - TWICORDER_RUN_FULL_USER_MENTIONS=0
      - TWICORDER_RUN_REMOVE_DUPLICATES=0
      - TWICORDER_RUN_APPDATA_TOKEN=timeline
      - TWICORDER_RUN_TASK_GEN=user_timeline name_pattern=/taskgen/*.txt,lookup_method=id,max_requests=5
    volumes:
      - /home/user/project/data:/data
      - /home/user/project/taskgen:/taskgen
```
