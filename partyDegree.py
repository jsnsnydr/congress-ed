import json
from datetime import datetime


def party_degree(path, year=datetime.now().year, pos=None):
    """
    Provides information about a member of Congress using a source file from the
    official congressional database, and basic filters to only return information
    if true.
    Most recent position (passing "pos" filter) is used for party info.
    :param path: JSON file containing Congress member's bio data.
    :param year: Member must have served in this year, default = current year,
                None = no year filter.
    :param pos: Indicates "position" filter. Defaults to None for any position in Congress,
                1 checks only for House, 2 checks only for Senate, 3 for a member
                who has served in both the House and Senate.
    :return: If the member passes the given filters, return a dictionary of
            their party and educational attainment. Else, return None.
    """
    def end_year(job):
        """
        Provide ending year from a Congress job.
        :param job: Dict of Congress info, using "yyyy-mm-dd" date format.
        :return: Last year of Congress that position was part of, as int.
        """
        return int(job["congressAffiliation"]["congress"]["endDate"].split("-")[0])

    with open(path) as source:
        data = json.load(source)["data"]

    # variables for initial eval of filters, and to get most recent job
    # has this member served in the House/Senate?
    rep = False
    sen = False

    # track latest job
    latest = None

    for entry in data["jobPositions"]:
        rep = rep or entry["job"]["name"] == "Representative"
        sen = sen or entry["job"]["name"] == "Senator"

        if end_year(entry) > latest:
            latest = entry

    # check year
    if end_year(latest) >= year:
        if pos:
            if pos == 1 and not rep:
                return None
            if pos == 2 and not sen:
                return None
            if pos == 3 and not rep or not sen:
                return None
    else:
        return None

    # passed filters; ask ChatGPT about bachelor's
    prompt = """I'm giving you the biography of a current or former member of Congress. Reply with only the word 
                "yes" if the biography entry states that the member has attained a bachelor's degree or the
                equivalent of an undergraduate college degree. Reply only the word "no" if they have an associate's
                degree, or no college degree at all. Here is the Congress member's bio, enclosed by quotation marks:\n"""
    prompt += f'"{latest["profileText"]}"'

