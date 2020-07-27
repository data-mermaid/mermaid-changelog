MERMAID Changelog
-----------------
Update changelog json file stored in S3 bucket based on open Trello lists with semantic versioning names, 
e.g. 'v0.10.0'. If called with a version argument, only the content of that version will be updated in the 
changelog; otherwise, all changelog versions matching open version Trello lists will be updated. 


## Requirements

* Requires Python 3.x (initial development using Python 3.7.x)

## Install

`pip install git+https://github.com/data-mermaid/mermaid-changelog.git`


## Install for Development

Development environment includes:


* Black for code formatting
* isort for formatting imports
* flake8 for styling and code quality


1. `pyenv virtualenv 3.7.1 mermaid-changelog`
2. `pyenv activate mermaid-changelog`
3. `git clone https://github.com/data-mermaid/mermaid-changelog.git`
4. `cd mermaid-changelog`
5. `pip install --editable .`
6. `pip install -r requirements-dev.txt`


## Environment Variables

```
# Get API key and token from https://trello.com/app-key
TRELLO_API_KEY=
TRELLO_TOKEN=

# AWS Key and Secret with S3 Read/Write permissions
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
# AWS S3 Bucket where changelog will be written to
AWS_CHANGELOG_BUCKET=

TRELLO_BOARD_NAME=

# Default: "Collect App, API, Summary API, Dash App"
APP_LABELS = 
# Default: "Bug, Hotfix"
BUG_LABELS = 
# Defaults: "changelog.json"
CHANGELOG_FILE=

```

## Usage


`chlog -v <version>` or `chlog --version <version>`: Update specific changelog version from corresponding open Trello
 list  
 `chlog`: Update all changelog versions with corresponding open Trello lists

Example: `chlog -v v0.10.3`