import praw
import os
import urllib
import re
import sys
import sqlite3

# the regex used to find the excuse on the website http://developerexcuses.com
excuse_regex = "<a .*?>(.*?)</a>"

# the amount of posts to get per fetch
submission_limit = 5

# the file name with the submissions that have already been replied to
posts_replied_to_file = "posts-replied-to.txt"

# ask the user to start the bot
start_script_question = input("Do u want to start the bot (y/n): ")

# if the user chooses n the script will exit
if "n" in start_script_question:
    sys.exit()

# create a connection to our sqlite database
connection = sqlite3.connect('subreddits.sqlite')
cursor = connection.cursor()

# create a table named subreddits if it does not already exist
cursor.execute("create table if not exists subreddits (id, name, added_by)")

# check if file exists
if not os.path.isfile(posts_replied_to_file):
    # create new empty list for new posts
    posts_replied_to = []
else:
    # open the file in read mode of the existing posts
    with open(posts_replied_to_file, "r") as f:

        # read the replied posts file
        posts_replied_to = f.read()

        # create an entry in the list for every line
        posts_replied_to = posts_replied_to.split("\n")

        # filter undefined/null entries in the lists
        posts_replied_to = list(filter(None, posts_replied_to))


# function that fetches a random developer excuse from the website
def get_random_excuse():
    # fetch the developer excuses page
    resp = urllib.request.urlopen('http://developerexcuses.com')

    # read the page and decode with utf-8 for regex usage
    page = resp.read().decode('utf-8')

    # search html response with regex
    excuse_search = re.search(excuse_regex, page, re.IGNORECASE)

    # select group 2 with the excuse (group 1 has some html tag properties)
    return excuse_search.group(1)


# function that checks if an there is an item in a list with the given index
def index_exists(list, index):
    try:
        list[index]
        return True
    except IndexError:
        return False


# look through the given array of users and return true if the user is in the list
def check_moderator(mods, user):
    for moderator in mods:
        if moderator.name == user:
            return True

    return False


# function that returns all subreddits to watch in a list
def get_subreddits_to_watch():
    subreddits_to_watch = []

    cursor.execute("select name from subreddits")

    data = cursor.fetchall()

    for subreddit in data:
        subreddits_to_watch.append(subreddit[0])

    if len(subreddits_to_watch) < 1:
        return "DeveloperExcusesBot"

    return "+".join(subreddits_to_watch)


# initiate a new reddit bot instance
reddit = praw.Reddit('bot1')

print("The Bot is now watching " + get_subreddits_to_watch())
print("")

while True:
    # define the subbreddit the bot should run on
    subreddit = reddit.subreddit(get_subreddits_to_watch())

    # for every unread message in the inbox
    for message in reddit.inbox.unread(limit=None):

        # split the message where there is a space
        message_body = message.body.split()

        # check if the message begins with an exclamation mark
        if message.body[0] != "!":

            # mark the message as read so it does not get picked up anymore
            message.mark_read()

            # reply to the message that the command was invalid
            message.reply(
                body=message.body + " Is not an valid command, u can use !add [subreddit] and !remove [subreddit] to add the bot")

            # if the message is not a command stop logic early
            continue

        # check if first part of message matches a command else reply with info message
        if message_body[0] == "!add":

            # check if the commands includes a subreddit
            if not index_exists(message_body, 1):
                message.mark_read()
                message.reply(
                    body="You are missing an argument of the !add command usage: !add [subreddit]")
                continue

            # search for the subbreddit with the 1st message argument
            new_subreddit = reddit.subreddit(message_body[1])

            # check if there is a search result
            if not new_subreddit:

                # mark the message as read
                message.mark_read()

                # reply to message with not found warning
                message.reply(
                    body="The Following subbreddit could not be found: " + message_body[1])
                continue

            # search the subreddit and check if it exists
            if new_subreddit:

                # check if the user is moderator of such subreddit
                if check_moderator(new_subreddit.moderator(), message.author.name):

                    print("added subreddit: " + new_subreddit.display_name +
                          " by: " + message.author.name)

                    # add new subreddit to subbreddit table with columns (id, name, added_by)
                    cursor.execute(
                        "insert into subreddits (id, name, added_by) values (?, ?, ?)", (new_subreddit.name, new_subreddit.display_name, message.author.name))

                    # save changes so they are persistent over sessions
                    connection.commit()

                    # mark the message as read
                    message.mark_read()

                    # reply to the message with a successful response message
                    message.reply(body="Successfully added subbreddit " +
                                  new_subreddit.display_name + " to watchlist!")

                else:
                    print("user is not a moderator of the selected sub")

                    # mark the message as read
                    message.mark_read()

                    # reply to the message with a message with a permission warning
                    message.reply(
                        body="You are not a Moderator of the subreddit: " + new_subreddit.display_name + " so u are not allowed to add the bot, please ask an moderator to add the bot!")
                    continue

        elif message_body[0] == "!remove":

            # check if the commands includes a subreddit
            if not index_exists(message_body, 1):
                message.mark_read()
                message.reply(
                    body="You are missing an argument of the !remove command usage: !remove [subreddit]")
                continue

            # search for the subbreddit with the 1st message argument
            new_subreddit = reddit.subreddit(message_body[1])

            # check if there is a search result
            if not new_subreddit:

                # mark the message as read
                message.mark_read()

                # reply to message with not found warning
                message.reply(
                    body="The Following subbreddit could not be found: " + message_body[1])
                continue

            # search the subreddit and check if it exists
            if new_subreddit:

                # check if the user is moderator of such subreddit
                if check_moderator(new_subreddit.moderator(), message.author.name):

                    print("removed subreddit: " + new_subreddit.display_name +
                          " by" + message.author.name)

                    # remove subbreddit where id matches
                    cursor.execute(
                        "delete from subreddits where id = :subID", {"subID": new_subreddit.name})

                    # save changes so they are persistent over sessions
                    connection.commit()

                    # mark the message as read
                    message.mark_read()

                    # reply to the message with a successful response message
                    message.reply(body="Successfully removed subbreddit " +
                                  new_subreddit.display_name + " from watchlist!")

                else:
                    print("user is not a moderator of the selected sub")

                    # mark the message as read
                    message.mark_read()

                    # reply to the message with a message with a permission warning
                    message.reply(
                        body="You are not a Moderator of the subreddit: " + new_subreddit.display_name + " so u are not allowed to remove the bot, please ask an moderator to remove the bot!")
                    continue

        else:
            message.mark_read()
            message.reply(
                body=message_body[0] + " is and invalid command try: !add, !remove")
            continue

    # for every 5 new submissions/posts
    for submission in subreddit.new(limit=submission_limit):

        # if the submission has not been replied to
        if submission.id not in posts_replied_to:

            # check if the submission has one of the following flairs
            if submission.link_flair_text in ['bug', 'help', 'not working']:

                # upvote the post
                submission.upvote()

                # reply with a random developer excuse
                submission.reply(body=get_random_excuse())

                # log reply to submission
                print("Bot replied to : ", submission.title +
                      " in " + submission.subreddit.name)

                # add submission id to list
                posts_replied_to.append(submission.id)

                # open file and update the list
                with open(posts_replied_to_file, "w") as f:
                    for post_id in posts_replied_to:
                        f.write(post_id + "\n")
