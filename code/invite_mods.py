import praw
import random
import logging
from prawcore.exceptions import Forbidden
from prawcore.exceptions import NotFound
from praw.exceptions import RedditAPIException
import auth


max_size = 8000000000
min_size = 1000
n_sr_to_contact = 3
TO_CONTACT_FILE = 'data/subreddits_to_contact.csv'
CONTACTED_FILE = 'data/contacted_subreddits.csv'

#logging.basicConfig(level=logging.DEBUG)

def contact_sr(sr, conn):
    subject = 'Chatbot intervention study'
    msg = f'''Hello r/{sr} moderators,
    
    YOUR RECRUITMENT MESSAGE HERE. 
    
    '''
    try:
        conn.subreddit(sr).message(subject=subject, message=msg)
    except (NotFound, RedditAPIException) as e:
        print(e)
        return e


def main():
    reddit = praw.Reddit(
        client_id=auth.client_id,
        client_secret=auth.client_secret,
        user_agent=auth.u_agent,
        username=auth.username,
        password=auth.password
    )

    candidates = []
    with open(TO_CONTACT_FILE, 'r') as f:
        for line in f.readlines():
            candidates.append(line.strip())
    n_candidates = len(set(candidates))

    contacted = []
    with open(CONTACTED_FILE, 'r') as f:
        for line in f.readlines():
            contacted.append(line.strip())

    candidates = set(candidates) - set(contacted)

    assert len(candidates) < n_candidates
    assert len(candidates) > 0
    candidates = list(candidates)
    print(candidates)

    to_contact = []
    while len(to_contact) < n_sr_to_contact and len(candidates) > 0:
        curr_sr = random.choice(candidates)
        print(curr_sr)
        if curr_sr in to_contact:
            continue
        try:
            curr_sr_subscribers = reddit.subreddit(curr_sr).subscribers
            print(curr_sr_subscribers)
        except Forbidden:
            logging.error(f"We can't get subscribers for {curr_sr}")
            candidates.remove(curr_sr)
            continue
        except NotFound:
            logging.error(f"The subreddit {curr_sr} doesn't seem to exist")
            candidates.remove(curr_sr)
            continue

        if curr_sr_subscribers > max_size or curr_sr_subscribers < min_size:
            candidates.remove(curr_sr)
            continue
        to_contact.append(curr_sr)
        candidates.remove(curr_sr)


    for sr in to_contact:
        logging.debug(f'Contacting subreddit {sr}')
        contact_sr(sr, conn=reddit)
        with open(CONTACTED_FILE, 'a') as f:
            f.write(f"{sr}\n")


if __name__ == '__main__':
    main()
