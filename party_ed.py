import json
from openai import OpenAI

def party_ed(path, minyear=-1, pos=None):
    """
    Provides information about a member of Congress using a source file from the
    official congressional database, and basic filters to only return information
    if true. Most recent job position (that passes the "pos" filter) is used for party info.

    Uses OpenAI API to determine education level.

    :param path: JSON file containing Congress member's bio data.
    :param minyear: Member must have served in this year, default = current year,
                    None = no year filter.
    :param pos: Indicates "position" filter. Defaults to None for any position in Congress,
                1 checks only for House, 2 checks only for Senate, 3 for a member
                who has served in both the House and Senate.
    :return: If the member passes the given filters, return a dictionary of
            their party and educational attainment. Else, return None.
    """

    with open(path) as source:
        data = json.load(source)["data"]

    def end_year(job):
        """
        Provide ending year from a Congress job.
        :param job: Dict of Congress info, using "yyyy-mm-dd" date format.
        :return: Last year of Congress that position was part of, as int.
        """
        if type(job) is not dict:
            return -1
        else:
            return int(job["congressAffiliation"]["congress"]["endDate"].split("-")[0])

    # variables for initial eval of filters, and to get most recent job
    # has this member served in the House/Senate?
    rep = False
    sen = False

    # track latest job
    latest = -1

    for entry in data["jobPositions"]:
        end = end_year(entry)

        if end > end_year(latest) and end >= minyear:
            if pos:
                if entry["job"]["name"] == "Representative":
                    rep = True
                    if pos == 1:
                        latest = entry
                elif entry["job"]["name"] == "Senator":
                    sen = True
                    if pos == 2:
                        latest = entry
                if pos == 3 and rep and sen:
                    latest = entry
            else:
                latest = entry

    # check year
    if latest == -1:
        return None

    # init OpenAI client
    with open("api.secret") as key, open("org.secret") as org, open("proj.secret") as proj:
        client = OpenAI(
            api_key=key.read(164),
            organization=org.read(28),
            project=proj.read(29)
        )

    # passed filters; ask ChatGPT about bachelor's

    prompt = """I'm giving the biography of a Congress member and need to know their level of education. Reply
                "no" if they haven't earned a bachelor's or the equivalent of an undergraduate degree, and also have
                not earned a graduate degree, such as a master's, JD, or PhD. Reply "un" if they only have an 
                undergraduate or bachelor's degree, "both" if they have an undergraduate degree and a graduate
                degree, and "gr" if they have only a graduate degree, though this final case is unlikely. 
                Here is the biography, enclosed in quotation marks:\n"""
    prompt += f'"{data["profileText"]}"'

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # get response and make the dict
    ed = completion.choices[0].message.content
    un = False
    gr = False

    if ed == "both":
        un = True
        gr = True
    elif ed == "un":
        un = True
    elif ed == "gr":
        gr = True

    vals = {
        "Caucus Party" : latest["congressAffiliation"]["caucusAffiliation"][0]["party"]["name"],
        "Undergrad" : un,
        "Graduate" : gr
    }

    return vals