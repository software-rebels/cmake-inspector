import requests
import csv
import time
from tqdm import tqdm
from datetime import datetime, timezone
from dateutil import parser, tz
import time

ACCESS_TOKEN = '1b65d4758a76efe3655fdc8c415fe06ae915bf33'
CSV_FILE_INPUT = 'projects_with_cmake_20200516.csv'
CSV_FILE_OUTPUT = 'projects_detail_{}.csv'.format(time.time())
FILED_NAMES = ['owner', 'name', 'isFork', 'isArchived', 'isDisabled', 'isLocked', 'isMirror', 'mentionableUsers', 'primaryLanguage', 'pushedAt', 'createdAt', 'stars', 'commits', 'cmake_content']
CURRENT_TIMEZONE = tz.tzlocal()

headers = {"Authorization": "bearer " + ACCESS_TOKEN}


def run_query(query): # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

        
# The GraphQL query (with a few aditional bits included) itself defined as a multi-line string.       
query = """
query {{
  rateLimit {{
    cost,
    limit,
    remaining,
    resetAt
  }}
  repository(owner:"{}", name:"{}") {{
    isFork,
    isArchived,
    isDisabled,
    isLocked,
    isMirror,
    mentionableUsers {{
      totalCount
    }},
    primaryLanguage {{
      name
    }},
    pushedAt,
    createdAt,
    stargazers {{
      totalCount
    }},
    defaultBranchRef {{
      target {{
        ... on Commit {{
         history {{
          totalCount
        }} 
        }}
      }}
    }},
    cmakeContent: object(expression: "master:CMakeLists.txt"){{
      ... on Blob {{
        text
      }}
    }}
  }}
}}
"""

with open(CSV_FILE_INPUT, 'r') as csv_in:
    lines = csv_in.read().splitlines()

with open(CSV_FILE_OUTPUT, 'w') as csv_out:
    writer = csv.DictWriter(csv_out, fieldnames = FILED_NAMES)
    writer.writeheader()
    for line in tqdm(lines):
        owner, name = line.split('/')
        while True:
            try:
                result = run_query(query.format(owner, name))
                rate_limit = result["data"]["rateLimit"]
                if rate_limit["remaining"] == 0:
                    resetAt = parser.parse(rate_limit["resetAt"])
                    currentTime = datetime.utcnow()
                    sleepTime = (resetAt - currentTime).seconds
                    print("We are out of rate limit, reset at {}, sleeping for {}".format(resetAt.astimezone(CURRENT_TIMEZONE), sleepTime+1))
                    time.sleep(sleepTime)
                else:
                    break
            except Exception:
                print("We encountered an error! sleeping for 5 second")
                time.sleep(5)
        data = result["data"]["repository"]
        if "errors" in result:
            # writer.writerow({
            #     'owner' : owner,
            #     'name' : name,
            # })
            continue
        try:
            writer.writerow({
                'owner' : owner,
                'name' : name,
                'isFork' : data["isFork"],
                'isArchived' : data["isArchived"],
                'isDisabled' : data["isDisabled"],
                'isLocked' : data["isLocked"],
                'isMirror' : data["isMirror"],
                'mentionableUsers' : data["mentionableUsers"]["totalCount"],
                'primaryLanguage' : data["primaryLanguage"]["name"] if data["primaryLanguage"] else "",
                'pushedAt' : data["pushedAt"],
                'createdAt' : data["createdAt"],
                'stars' : data["stargazers"]["totalCount"],
                'commits' : data["defaultBranchRef"]["target"]["history"]["totalCount"], 
                'cmake_content' : data["cmakeContent"]["text"] if data["cmakeContent"] else ""
            })
        except Exception:
            continue