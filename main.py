import praw
import os
import urllib
import re
import sys

# the regex used to find the excuse on the website http://developerexcuses.com
excuse_regex = "<a .*?>(.*?)</a>"

# the amout of posts to get per fetch
submission_limit = 5

# the file name with the submissions that have already been replied to
posts_replied_to_file = "posts-replied-to.txt"

# ask the user to start the bot
start_script_question = input("Do u want to start the bot (y/n): ")

# if the user chooses n the script will exit
if "n" in start_script_question:
    sys.exit()

# ask the user what subbredit to watch
subbreddit_to_watch = input(
    "What subbredit do u want the bot to watch? leave empty to use 'DeveloperExcusesBot' (without 'r/')")

#  if no input was given set subbreddit to default: DeveloperExcusesBot
if not subbreddit_to_watch:
    subbreddit_to_watch = "DeveloperExcusesBot"

# check if file exists
if not os.path.isfile(posts_replied_to_file):
    # create new empty list for new posts
    posts_replied_to = []
else:
    # open the file in read mode of the exsisting posts
    with open(posts_replied_to_file, "r") as f:

        # read the replied posts file
        posts_replied_to = f.read()

        # create an entry in the list for every line
        posts_replied_to = posts_replied_to.split("\n")

        # filter undefined/null entries in the lists
        posts_replied_to = list(filter(None, posts_replied_to))

# initiate a new reddit bot instance
reddit = praw.Reddit('bot1')

# define the subbreddit the bot should run on
subreddit = reddit.subreddit(subbreddit_to_watch)


def get_random_exuse():
    # fetch the developer exuses page
    resp = urllib.request.urlopen('http://developerexcuses.com')

    # read the page and decode with utf-8 for regex ussage
    page = resp.read().decode('utf-8')

    # search html response with regex
    excuse_search = re.search(excuse_regex, page, re.IGNORECASE)

    # select group 2 with the excuse (group 1 has some html tag properties)
    return excuse_search.group(1)


while True:
    # for every 5 new submissions/posts
    for submission in subreddit.new(limit=submission_limit):

        # if the submission hasnt been replied to
        if submission.id not in posts_replied_to:

            # check if the submission has one of the following flairs
            if submission.link_flair_text in ['bug', 'help', 'not working']:
                # reply with a random developer excuse
                submission.reply(body=get_random_exuse())

                # log reply to submission
                print("Bot replyed to : ", submission.title)

                # add submission id to list
                posts_replied_to.append(submission.id)

                # open file and update the list
                with open(posts_replied_to_file, "w") as f:
                    for post_id in posts_replied_to:
                        f.write(post_id + "\n")
