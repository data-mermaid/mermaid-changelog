#!/usr/bin/env python

import json
import os
import sys

import boto3
import botocore
from trello import TrelloClient


def get_list_env_var(key, default=None):
    val = os.environ.get(key) or default
    if val is None:
        return val
    return [v.strip() for v in val.split(",")]


TRELLO_BOARD_NAME = os.environ["TRELLO_BOARD_NAME"]
AWS_S3_BUCKET = os.environ["AWS_S3_BUCKET"]
APP_LABELS = get_list_env_var("APP_LABELS", "Collect App, API, Summary API")
BUG_LABELS = get_list_env_var("BUG_LABELS", "Bug, Hotfix")
CHANGELOG_FILE = os.environ.get("CHANGELOG_FILE") or "changelog.json"

client = TrelloClient(
    api_key=os.environ["TRELLO_API_KEY"], token=os.environ["TRELLO_TOKEN"]
)


class NotFoundError(ValueError):
    pass


def get_board(board_name):
    for board in client.list_boards():
        if board.name == board_name:
            return board
    return None


def get_cards(trello_list):
    return trello_list.list_cards()


def get_apps(card):
    labels = card.labels or []
    return [label.name for label in labels if label.name in APP_LABELS]


def get_card_number(card):
    return card.url.split("/")[-1].split("-")[0]


def is_bug(card):
    labels = card.labels or []
    for label in labels:
        if label.name in BUG_LABELS:
            return True
    return False


def get_card_details(card):
    return dict(
        name=card.name,
        url=card.url,
        apps=get_apps(card),
        number=get_card_number(card),
        is_bug=is_bug(card),
    )


def get_cards_by_git_tag(tag):
    honeycrisp_board = get_board(TRELLO_BOARD_NAME)
    version_list = None
    for t_list in honeycrisp_board.open_lists():
        if t_list.name == tag:
            version_list = t_list
            break

    if version_list is None:
        raise NotFoundError("'{}' not found".format(tag))

    return [get_card_details(card) for card in get_cards(version_list)]


def download_changelog_from_s3():
    s3 = boto3.client("s3")
    try:
        download_path = "/tmp/{}".format(CHANGELOG_FILE)
        s3.download_file(AWS_S3_BUCKET, CHANGELOG_FILE, download_path)
        return download_path
    except botocore.exceptions.ClientError as e:
        if int(e.response["Error"]["Code"]) == 404:
            return None
        raise e


def upload_changelog_to_s3(local_path):
    s3 = boto3.client("s3")
    return s3.upload_file(
        local_path,
        AWS_S3_BUCKET,
        CHANGELOG_FILE,
        ExtraArgs={"ContentType": "application/json"},
    )


def read_changelog_contents(changelog_path):
    if changelog_path is None:
        return []
    else:
        with open(changelog_path, "r") as f:
            return json.loads(f.read())


def get_version_index(version, changelog_content):
    for n, entry in enumerate(changelog_content):
        if entry.get("version") == version:
            return n
    return None


def update_changelog_file(version, changes, changelog_path):
    changelog_contents = read_changelog_contents(changelog_path)
    new_version_content = dict(version=version, changes=changes)
    version_index = get_version_index(version, changelog_contents)
    if version_index is None:
        changelog_contents.insert(0, new_version_content)
    else:
        changelog_contents[version_index] = new_version_content

    with open(changelog_path, "w") as fw:
        fw.write(json.dumps(changelog_contents))


def main():
    try:
        version = sys.argv[1]
        changes = get_cards_by_git_tag(version)
        num_changes = len(changes)
        if num_changes == 0:
            print("No entries to add to changelog.")
            exit()

        changelog_path = download_changelog_from_s3() or "/tmp/{}".format(
            CHANGELOG_FILE
        )
        update_changelog_file(version, changes, changelog_path)
        upload_changelog_to_s3(changelog_path)
        os.remove(changelog_path)

        print("Version '{}' updated with {} changes.".format(version, num_changes))

    except IndexError:
        print("chlog <VERSION>")
    except NotFoundError as nfe:
        print(str(nfe))


if __name__ == "__main__":
    main()
