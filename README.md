MERMAID Changelog
-----------------


## Requirements

* Requires Python 3.x (initial development using Python 3.7.x)

## Install

`pip install git+https://github.com/data-mermaid/mermaid-changelog.git`


## Install for Development

Development environment includes:


* Black for code formatting
* isort for formatting imports
* flake8 for styling and code quality


1. `pyenv virtualenv 3.7.1 geotrellis-cli-env`
2. `pyenv activate geotrellis-cli-env`
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
AWS_S3_BUCKET=

TRELLO_BOARD_NAME=

# Default: "Collect App, API, Summary API, Dash App"
APP_LABELS = 
# Default: "Bug, Hotfix"
BUG_LABELS = 
# Defaults: "changelog.json"
CHANGELOG_FILE=

```

## Usage


`chlog <version>`

Example: `chlog v0.10.3`