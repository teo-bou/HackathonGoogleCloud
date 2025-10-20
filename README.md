# HackathonGoogleCloud — Getting Started

## Setup (recommended)

Run these commands from the repository root (macOS / zsh):

```bash
# create and activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

Copy the .env.example file, rename it to .env and fill the GOOGLE_API_KEY with an API key you can find here : https://aistudio.google.com/app/u/4/api-keys?pli=1

## Running

```bash
adk run my-agent
```
