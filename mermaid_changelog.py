#!/usr/bin/env python

import argparse
import json
import os
import re
import tempfile
from argparse import RawDescriptionHelpFormatter
from datetime import datetime

import boto3
import botocore
from trello import TrelloClient


def get_list_env_var(key, default=None):
    val = os.environ.get(key) or default
    if val is None:
        return val
    return [v.strip() for v in val.split(",")]


TRELLO_BOARD_NAME = os.environ["TRELLO_BOARD_NAME"]
AWS_S3_BUCKET = os.environ["AWS_CHANGELOG_BUCKET"]
APP_LABELS = get_list_env_var("APP_LABELS", "Collect App, API, Summary API")
BUG_LABELS = get_list_env_var("BUG_LABELS", "Bug, Hotfix")
TMPDIR = tempfile.gettempdir() or os.getcwd()
CHANGELOG_FILE = os.environ.get("CHANGELOG_FILE") or "changelog.json"
CHANGELOG_PATH = os.path.join(TMPDIR, "{}".format(CHANGELOG_FILE))
VERSION_PATTERN = re.compile(r"v[0-9]+(\.[0-9]+)+$", re.IGNORECASE)

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
    board = get_board(TRELLO_BOARD_NAME)
    version_list = None
    for t_list in board.open_lists():
        if t_list.name == tag:
            version_list = t_list
            break

    if version_list is None:
        raise NotFoundError("'{}' not found".format(tag))

    return [get_card_details(card) for card in get_cards(version_list)]


def get_cards_by_open_releases():
    board = get_board(TRELLO_BOARD_NAME)
    version_lists = []
    for t_list in board.open_lists():
        if VERSION_PATTERN.match(t_list.name):
            changes = [get_card_details(card) for card in get_cards(t_list)]
            version_content = dict(version=t_list.name, changes=changes)
            version_lists.append(version_content)
    return sorted(version_lists, key=lambda k: k["version"], reverse=True)


def download_changelog_from_s3():
    s3 = boto3.client("s3")
    try:
        return s3.download_file(AWS_S3_BUCKET, CHANGELOG_FILE, CHANGELOG_PATH)
    except botocore.exceptions.ClientError as e:
        if int(e.response["Error"]["Code"]) == 404:
            return None
        raise e


def upload_changelog_to_s3():
    s3 = boto3.client("s3")
    return s3.upload_file(
        CHANGELOG_PATH,
        AWS_S3_BUCKET,
        CHANGELOG_FILE,
        ExtraArgs={"ContentType": "application/json"},
    )


def read_changelog_contents():
    if CHANGELOG_PATH is None:
        return []
    else:
        with open(CHANGELOG_PATH, "r") as f:
            return json.loads(f.read())


def get_version_index(version, changelog_content):
    for n, entry in enumerate(changelog_content):
        if entry.get("version") == version:
            return n
    return None


def update_changelog_file(version, release_date, changes):
    changelog_contents = read_changelog_contents()
    new_version_content = dict(
        version=version, release_date=release_date, changes=changes
    )
    version_index = get_version_index(version, changelog_contents)
    if version_index is None:
        changelog_contents.insert(0, new_version_content)
    else:
        changelog_contents[version_index] = new_version_content

    with open(CHANGELOG_PATH, "w") as fw:
        fw.write(json.dumps(changelog_contents))


def get_date():
    timestamp = datetime.utcnow()
    return str(timestamp.date())


def _get_version_release_dates(changelog_path):
    with open(changelog_path) as f:
        contents = json.loads(f.read())
        return {e["version"]: e.get("release_date") for e in contents}


def main():
    parser = argparse.ArgumentParser(
        description=u"""
    Update changelog json file stored in S3 bucket based on open Trello lists with semantic versioning names, 
    e.g. 'v0.10.0'. If called with a version argument, only the content of that version will be updated in the 
    changelog; otherwise, all changelog versions matching open version Trello lists will be updated. 
    """,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        help=u"Optional version tag to update in the changelog. Leave out to update all versions matching open "
        u"version Trello lists.",
    )
    args = parser.parse_args()

    download_changelog_from_s3()
    release_dates = _get_version_release_dates(CHANGELOG_PATH)

    if args.version:
        version = args.version
        if not VERSION_PATTERN.match(version):
            print("Invalid version '{}'".format(version))
            exit()

        changes = get_cards_by_git_tag(version)
        num_changes = len(changes)
        if num_changes == 0:
            print("No entries to add to changelog.")
            exit()

        release_date = release_dates.get(version) or get_date()
        update_changelog_file(version, release_date, changes)
        upload_changelog_to_s3()
        os.remove(CHANGELOG_PATH)

        print("Version '{}' updated with {} changes.".format(version, num_changes))

    else:
        open_releases = get_cards_by_open_releases()
        num_releases = len(open_releases)
        if num_releases == 0:
            print("No open releases to add to changelog.")
            exit()

        for release in open_releases:
            version = release.get("version")
            changes = release.get("changes")
            if version and changes:
                num_changes = len(changes)
                if num_changes == 0:
                    print(
                        "No entries to add to changelog for version {}.".format(version)
                    )
                    exit()
                release_date = release_dates.get(version) or get_date()
                update_changelog_file(version, release_date, changes)
                print(
                    "Version '{}' updated with {} changes.".format(version, num_changes)
                )

        upload_changelog_to_s3()
        os.remove(CHANGELOG_PATH)
        print("Changelog finished updating and uploaded to S3.")


if __name__ == "__main__":
    main()
