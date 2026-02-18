# Reddit Conversation Laboratory - Copilot Instructions

## Project Overview

This repository contains the **Reddit Conversation Laboratory (RCL)**, a Python-based toolkit for conducting field experiments with AI agents on Reddit. The software identifies participants, recruits and consents them, and conducts conversational experiments with researcher-designed AI chatbots. It also records participant behavior before and after conversations and includes scripts for data collection, augmentation, and summarization.

### Key Technologies
- **Language**: Python 3.12
- **Package Manager**: Conda/Miniforge
- **Workflow Manager**: Snakemake
- **Main Dependencies**: PRAW (Reddit API), OpenAI API, Anthropic API, Pandas, PyArrow
- **Environment**: Conda environment named `rcl` (defined in `environment.yml`)

## Repository Structure

```
.
├── code/                          # All Python scripts
│   ├── chatbot.py                 # Main chatbot controller
│   ├── auth.py                    # Reddit authentication utilities
│   ├── config.yaml                # Active configuration (messages, paths, models)
│   ├── example_config.yaml        # Template configuration
│   ├── get_convos.py              # Conversation aggregation
│   ├── get_prospective_users.py   # Participant identification
│   ├── invite_mods.py             # Subreddit moderator recruitment
│   ├── get_noncontacted_control.py # Control group creation
│   ├── augment_data/              # Scripts to add toxicity scores and metadata
│   ├── fetch_comms/               # Scripts to fetch Reddit comments
│   └── summarize_data/            # Scripts to generate summary CSVs
├── data/                          # Input/output data directories
├── environment.yml                # Conda environment specification
├── Snakefile                      # Snakemake pipeline rules
├── crontab.example                # Example cron scheduling
├── .env.example                   # Template for API credentials
└── .github/
    └── copilot-instructions.md    # This file
```

## Environment Setup

### Prerequisites
- Conda/Miniforge/Anaconda installed
- Snakemake installed (can be installed via conda)

### Setup Steps

**ALWAYS follow these steps when setting up the environment:**

1. **Create the conda environment** (only needed once):
   ```bash
   conda env create -f environment.yml
   ```
   - Default environment name is `rcl`
   - To change, edit the first line of `environment.yml`

2. **Activate the environment** (required before running any scripts):
   ```bash
   conda activate rcl
   ```

3. **Set up API credentials** (required for chatbot operation):
   ```bash
   cp .env.example .env
   # Edit .env with real credentials
   ```
   - **Reddit API credentials** (required for all Reddit interactions):
     - `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`: From your Reddit app
     - `REDDIT_USERNAME` and `REDDIT_PASSWORD`: Your Reddit account credentials
     - `REDDIT_USER_AGENT`: Custom identifier (format: `platform:app_id:version (by /u/username)`)
   - Optional: `OPENAI_API_KEY` (for OpenAI chatbot responses)
   - Optional: `ANTHROPIC_API_KEY` (for Anthropic/Claude chatbot responses)
   - Optional: `PERSPECTIVE_API_KEY` (for toxicity scoring in augmentation scripts)
   - The `.env` file is gitignored to prevent credential leaks

## Running the Software

### Chatbot Operation

The chatbot runs from the `code/` directory:

```bash
cd code
python chatbot.py
```

**How it works:**
- Maintains conversation records in CSV files
- Checks Reddit inbox for new messages
- Uses OpenAI/Anthropic to generate responses
- Supports three messaging flows: 'default' (modmail → DM), 'dm' (DM only), 'modmail' (modmail only)
- Handles consent collection and conversation state management

### Data Collection

Run participant identification (scans mod logs for toxic comments):
```bash
cd code
python get_prospective_users.py
```

Fetch participant comments:
```bash
cd code
python fetch_comms/retrieve_latest_user_comments.py
```

### Snakemake Pipeline

The Snakemake pipeline handles data augmentation and summarization:

**Important Environment Note:** 
- The `environment.yml` defines a conda environment named `rcl`
- The `Snakefile` rules reference a conda environment named `toxic_talk`
- This is a known bug in the repository that should be corrected

**Recommended fix** (Update Snakefile to use the correct environment name):
```bash
sed -i 's/conda: "toxic_talk"/conda: "rcl"/g' Snakefile
```

**Alternative workaround** (if you cannot modify Snakefile):
```bash
conda create --name toxic_talk --clone rcl
```

**Dry-run (see what would execute):**
```bash
snakemake -n
```

**Run the pipeline:**
```bash
snakemake -j 4  # Uses up to 4 cores
```

**Pipeline outputs:**
- `data/filtered_convos.csv` - Cleaned conversation records
- `data/summarized_data/summarized_conversations.csv` - Conversation summaries
- `data/summarized_data/participant_info.csv` - Participant information
- `data/augmented_data/` - Augmented comments, conversations, suspension data

**Pipeline steps:**
1. `clean_conversations` - Aggregates and filters conversations
2. `augment_comments` - Adds toxicity scores to participant comments
3. `augment_conversations` - Adds toxicity scores to conversations
4. `augment_suspended` - Normalizes suspension data
5. `summarize_conversations` - Creates conversation-level summaries
6. `make_participant_file` - Generates participant information

## Configuration

### Main Configuration File: `code/config.yaml`

**Key settings:**
- `max_interactions`: Maximum conversation turns (default: 50)
- `max_tokens`: Token limit for prompts (default: 30000)
- `gai_models`: OpenAI and Claude models to use
- `subreddits`: List of subreddits to monitor
- File paths: `to_contact_file`, `participants_file`, `conversations_file`, `subreddits_file`, `bad_accounts_file`
- Message templates: `initial_message`, `clarifying_message`, `handoff_message`, `first_consented_message`, `gai_prompt`, `goodbye_message`
  - These are multiline strings with formatting placeholders like `{username}`, `{subreddit}`, `{comment}`

**Important:** Message templates can have multiple variants (e.g., `initial_message_1`, `initial_message_2`) for A/B testing.

## Automation / Scheduling

The repository includes `crontab.example` showing recommended scheduling:

- **Chatbot** (`code/chatbot.py`): Every minute - responds to new messages
- **Participant identification** (`code/get_prospective_users.py`): Twice per day - scans mod logs
- **Comment fetching** (`code/fetch_comms/retrieve_latest_user_comments.py`): Once per day - fetches user activity

**Preventing concurrent executions:**
Use `flock` to prevent overlapping chatbot instances:
```bash
# Note: Ensure conda environment is activated in your shell profile, 
# or add 'conda activate rcl &&' before the python command
* * * * * flock -n /tmp/chatbot.lock -c "cd /path/to/code && python chatbot.py" >> logs/chatbot.log 2>&1
```

## Important Workflows

### Working Directory
**ALWAYS `cd` to the `code/` directory before running Python scripts:**
```bash
cd code
python chatbot.py  # Correct
python get_convos.py  # Correct
```

Scripts expect to be run from `code/` because:
- `config.yaml` uses relative paths like `../data/`
- Scripts import other modules in `code/` (e.g., `import auth`)

### Data Files

**Critical CSV files in `data/`:**
- `to_contact.csv` - Users to contact; populated by `get_prospective_users.py`
- `participants.csv` - Participant records with conditions and UUIDs
- `conversations.csv` - All messages (bot and user)
- `subreddit_rules.csv` - Subreddit-specific rules
- `bad_accounts_file.csv` - Accounts to exclude
- `participant_comments.csv` - Collected user comments
- `participant_data/suspended_ids.csv` - Suspension status

### Testing Changes

There are **no automated tests** in this repository. To validate changes:

1. **For chatbot changes:**
   - Set up test subreddits in `config.yaml`
   - Use test Reddit accounts
   - Monitor `logs/chatbot.log` for errors
   - Verify conversations appear in `data/conversations.csv`

2. **For data processing changes:**
   - Run on sample data first
   - Verify CSV outputs are well-formed
   - Check that Snakemake pipeline completes successfully

3. **For configuration changes:**
   - Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('code/config.yaml'))"`
   - Test with small batches before production

## Common Issues and Solutions

### Import Errors
**Problem:** `ModuleNotFoundError` when running scripts
**Solution:** 
1. Ensure conda environment is activated: `conda activate rcl`
2. Run scripts from `code/` directory: `cd code && python script.py`

### Configuration Not Found
**Problem:** `FileNotFoundError` for `config.yaml` or data files
**Solution:** Run scripts from `code/` directory (scripts expect relative paths from there)

### API Credentials
**Problem:** Authentication failures with Reddit/OpenAI/Anthropic
**Solution:**
1. Verify `.env` file exists and contains valid credentials
2. Check that `.env` is in the repository root
3. Ensure environment variables are loaded by the script

### Snakemake Failures
**Problem:** Snakemake rule failures, especially conda environment errors
**Solution:**
1. Run with `-n` flag first to see planned actions
2. Ensure required input files exist (check `data/` directory)
3. If encountering conda environment errors, see the environment naming bug and recommended fix in the "Snakemake Pipeline" section above
4. Run individual scripts manually to debug

### Concurrent Chatbot Executions
**Problem:** Multiple chatbot instances causing conflicts
**Solution:** Use `flock` in crontab to ensure only one instance runs at a time

## Development Guidelines

### Making Changes
1. **Always test in isolation first** - use test subreddits and accounts
2. **Preserve existing CSV structures** - many scripts depend on specific column names
3. **Update `config.yaml` carefully** - message templates are interpolated with placeholders
4. **Don't commit `.env`** - it's gitignored for security
5. **Run Snakemake dry-run** before pushing changes: `snakemake -n`

### Code Style
- Scripts use descriptive variable names
- Configuration-driven behavior (avoid hardcoding)
- CSV operations use pandas
- Reddit operations use PRAW
- Error handling with try/except for API calls

### Adding New Features
1. Update `config.yaml` with new settings
2. Modify relevant scripts in `code/`
3. Update `Snakefile` if new data processing steps are needed
4. Test thoroughly with sample data
5. Update this instructions file if workflow changes

## Key Dependencies and APIs

### Reddit API (PRAW)
- Used for all Reddit interactions (messages, mod logs, comments)
- Requires app credentials from Reddit
- Rate-limited; scripts handle throttling

### OpenAI API
- Used for chatbot responses
- Model specified in `config.yaml` under `gai_models.openai`
- Supports multiple models for A/B testing

### Anthropic API
- Alternative to OpenAI for chatbot responses
- Model specified in `config.yaml` under `gai_models.claude`

### Perspective API
- Used for toxicity scoring in augmentation scripts
- Optional; required for `augment_data/` scripts

## Quick Reference

**Start a development session:**
```bash
conda activate rcl
cd code
```

**Run the chatbot once:**
```bash
cd code
python chatbot.py
```

**Process all data:**
```bash
snakemake -j 4
```

**Validate configuration:**
```bash
python -c "import yaml; f = open('code/config.yaml'); print(yaml.safe_load(f)); f.close()"
```

**Check what Snakemake would do:**
```bash
snakemake -n
```

**Clean and restart pipeline:**
```bash
# Remove outputs and rerun
rm -rf data/augmented_data/* data/summarized_data/*
snakemake -j 4
```
