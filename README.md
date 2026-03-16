# Reddit Conversation Laboratory

Authors: Dr. Jeremy Foote ([jdfoote@purdue.edu](mailto:jdfoote@purdue.edu)), Dr. Deepak Kumar ([kumarde@ucsd.edu](mailto:kumarde@ucsd.edu)), Hitesh Goel ([hitesh.goel@research.iiit.ac.in](mailto:hitesh.goel@research.iiit.ac.in)), Loizos Bitsikokos ([lbitsiko@purdue.edu](mailto:lbitsiko@purdue.edu))

Reddit Conversation Laboratory (RCL) is a software toolkit and pipeline for conducting field experiments with AI agents on Reddit. It is Python-based software that identifies participants, recruits and consents them, and conducts conversational experiments with researcher-designed AI chatbots. 

In addition to conducting experiments and storing conversations, the software can also record participant behavior before and after conversations. The toolkit contains scripts to fetch Reddit comments, prepare conversation-level data, augment comments with moderation and suspension signals, and generate summarized outputs for downstream analysis. In addition to this documentation, there is [an academic paper](https://doi.org/10.5117/CCR2026.2.5.FOOT) which provides a more extended expalanation and argument for when, why, and how researchers might use RCL.


## Installation

### Requirements

RCL is designed to be run on a Linux server, using the `cron` scheduling system. It requires at least 2 cores and at least 4GB of RAM. Working with really large samples may require additional resources.

Required software:
- Python 3.10+
- Conda / Miniconda

## Setup (create environment)

Clone this repository, and create the conda environment using the `environment.yml` file.

```bash
conda env create -f environment.yml
conda activate rcl
```

The default name for the environment is `rcl`. To change this, edit the first line in the `environment.yml` file.

## Running experiments and collecting data

In order to run chatbot experiments, you will need to set up Reddit API credentials and an API key to one or more LLM providers (currently, the system supports OpenAI and Anthropic). On Reddit, this means setting up a Reddit app to get a client ID and secret. See the [PRAW documentation](https://praw.readthedocs.io/en/stable/getting_started/authentication.html) for details.

It is also recommended that you work with moderators of the subreddits that you are recruiting from. In the default implementation, the chatbot sends modmail messages to prospective participants, so you will need to have moderator permissions for the subreddits you are recruiting from. You can modify the included `invite_mods.py` script to send invitations to moderators to participate in the study, and to keep track of which subreddits have been contacted.


### Environment variables (.env)

Once you have set up your Reddit app and obtained your API credentials, copy the `.env.example` file to `.env` and fill in your real credentials:

```bash
cp .env.example .env
```

The `.env` file is ignored by git to avoid accidentally committing your keys.

## Chatbot flow

The chatbot is designed to work as follows, from the user's perspective:

1. Via modmail, the bot sends an initial message to a prospective participant (e.g., "Hi, I noticed your comment in r/subreddit. Would you be interested in chatting with an AI about your experience?").
2. If the user replies with a response starting with "Yes", the bot assigns them to a condition or to control and sends a handoff message (e.g., "Thanks so much! If you are selected for the study, you will receive a direct message from this account soon.")
2a. If the user replies with something other than "Yes", the bot sends a clarifying message (e.g., "Sorry, I just want to confirm that you are interested in chatting with an AI about your experience. If so, please reply with 'Yes'.")
3. For users who consent and are not in control, the bot sends another hardcoded message (`first_consented_message`), which should be designed to elicit a response. After this, the chatbot passes the conversation and its history to the LLM, which uses the `gai_prompt` templates to generate responses. The bot continues to reply until the conversation ends (e.g., user stops replying, or a certain number of messages is reached), at which point it sends a goodbye message.


## Configuration

The heart of the RCL system is the chatbot, which is designed to be flexible and adaptable for different research questions. To configure the chatbot, RCL uses a YAML configuration file that defines the chatbot's behavior, settings, and message templates. This allows you to customize the chatbot for different studies. For many options, researchers can provide a dictionary of multiple values which will be randomly assigned to participants (e.g., different LLM models, different initial messages, etc.), enabling easy experimentation with different conditions. The file itself (`code/config.yaml`) is well-commented to explain the purpose of each option and how to use it, but here is a quick overview of the key configuration options:

  - `gai_models` - list of LLM models the chatbot can use (currently supports OpenAI and Anthropic models, but can be extended to other providers).
  - `conversations_file`, `to_contact_file`, `participants_file`, `subreddits_file`, `bad_accounts_file` - relative paths to project CSVs. Defaults are set to the `data/` folder, but you can change these if you want to organize your files differently.
  - `initial_message` - a list of recruitment messages to send to prospective participants. If you provide multiple messages, the chatbot will randomly select one for each participant.
  - `clarifying_message` - message sent when a user replies with something other than "Yes" or "No" to the initial recruitment message, asking them to clarify their interest.
  - `handoff_message` - message sent when a user consents and is assigned to a condition.
  - `first_consented_message` - message sent to users who have consented and are not in the control group.
  - `gai_prompt` - dictionary of system prompts used by the chatbot. These are multiline strings and may include formatting placeholders like `{subreddit}` and `{comment}`, which will be filled in with data from the participant CSV.
  - `goodbye_message` - final message shown when the bot reaches its maximum number of messages.
  - `subreddits` - subreddits for which the chatbot is a moderator. The `to_contact` file must include a `subreddit` column, and the chatbot will message users using modmail from these subreddits.

#### Using Custom Fields in Message Templates

Any custom fields you add to `to_contact.csv` or `participants.csv` can be used in your message templates by including them in curly braces:

```yaml
first_consented_message:
  message_1: |
    Thank you for agreeing to chat. I noticed your post in r/{subreddit} where you mentioned {topic}.
    Your account karma is {post_karma} and you've been active for {account_age} days.
```

## Recruiting Participants

The default implementation of RCL identifies prospective participants by scanning subreddit moderation logs for removed comments, and then scores those comments for toxicity using the Perspective API. The `get_prospective_users.py` script is responsible for this, and it writes a `to_contact.csv` file with the list of users to contact, along with relevant metadata (e.g., the comment that got them identified, the toxicity score, etc.). You can modify this script to use different criteria for identifying participants if you want to study a different population. For example, you might look for the most recently active users in a subreddit, or users who have posted about a certain topic, etc. The important thing is that the output of this script should be a `to_contact.csv` file with a `username` column and a `subreddit` column, which the chatbot will use to send recruitment messages.

## Scheduling / Automation

The repository includes an example crontab file ([crontab.example](crontab.example)) that demonstrates how to schedule the RCL scripts to run automatically. The recommended schedule is:

- **Chatbot** ([code/chatbot.py](code/chatbot.py)): Every minute - checks for new messages and responds to conversations
- **Participant identification / modlog collection** ([code/get_prospective_users.py](code/get_prospective_users.py)): Twice per day - scans subreddit mod logs to identify prospective participants (default implementation looks for removed comments and scores them for toxicity, but can be customized for other use cases)
- **Participant data collection** ([code/fetch_comms/retrieve_latest_user_comments.py](code/fetch_comms/retrieve_latest_user_comments.py)): Once per day - fetches recent comments and suspension status

### Preventing Concurrent Executions

The chatbot may take longer than a minute to complete, and without locking, cron would start multiple overlapping instances. The example crontab uses the `flock` command to prevent this:

```bash
* * * * * flock -n /tmp/chatbot.lock -c "cd /path/to/code && python chatbot.py" >> logs/chatbot.log 2>&1
```

The `-n` flag makes flock non-blocking: if another instance is running, the command exits immediately rather than waiting.

To use the example crontab:

1. Copy and edit `crontab.example` to match your installation paths
2. Create a `logs/` directory in the repository root for log files
3. Install with `crontab your-edited-file`
4. Verify with `crontab -l`

See [crontab.example](crontab.example) for detailed instructions and alternative configurations.

## Code files (brief descriptions generated by Copilot)

Top-level scripts in `code/`:

- [code/chatbot.py](code/chatbot.py) - Main chatbot controller: reads conversations, inbox/modmail, decides whether to reply, and sends messages via PRAW/OpenAI; contains conversation and run logic.
- [code/get_convos.py](code/get_convos.py) - Aggregate and clean conversation records into [data/filtered_convos.csv](data/filtered_convos.csv) (groups messages by user, filters by AI replies and test subreddits).
- [code/get_toxic_moderated_comments.py](code/get_toxic_moderated_comments.py) - **(Toxicity-specific)** Scans subreddit mod logs for removed comments, scores them with Perspective API, records toxic removed comments or comments containing certain keywords for contacting. Can be adapted for other participant identification criteria.
- [code/fetch_comms/retrieve_latest_user_comments.py](code/fetch_comms/retrieve_latest_user_comments.py) - Fetches recent comments for users (uses PRAW), writes [data/participant_comments.csv](data/participant_comments.csv) and suspended status.
- [code/invite_mods.py](code/invite_mods.py) - Script to contact subreddit moderators (used to recruit subreddits for the study).
- [code/get_noncontacted_control.py](code/get_noncontacted_control.py) - Builds an uncontacted control sample from moderation logs and appends matched controls to [data/participants.csv](data/participants.csv). Can be adapted for different control group selection criteria.

Augmentation scripts in `code/augment_data/`:

- [code/augment_data/augment_comments.py](code/augment_data/augment_comments.py) - Add toxicity scores to participant comments and write augmented CSV / feather outputs.
- [code/augment_data/augment_conversations.py](code/augment_data/augment_conversations.py) - Add toxicity scores to conversation-level texts and append to augmented conversations file.
- [code/augment_data/augment_moderation.py](code/augment_data/augment_moderation.py) - Parse moderation log CSVs, filter removal actions for our participants, and produce augmented moderation data.
- [code/augment_data/augment_suspended.py](code/augment_data/augment_suspended.py) - Normalize suspension files and convert date strings to `created_utc` timestamps.
- [code/augment_data/prep_data.py](code/augment_data/prep_data.py) - one-off preprocessing that computes conversation stats and writes aggregated augmented outputs.
- [code/augment_data/get_toxicity.py](code/augment_data/get_toxicity.py) - Wrapper around the Perspective API client used by augmentation scripts to get toxicity and severe toxicity scores.

Summarization scripts in `code/summarize_data/`:

- [code/summarize_data/clean_participant_info.py](code/summarize_data/clean_participant_info.py) - Cleans and produces a `participant_info.csv` file from raw participants and moderation outputs.
- [code/summarize_data/make_conversation_summaries.py](code/summarize_data/make_conversation_summaries.py) - Generates conversation-level summary CSVs from augmented conversations.