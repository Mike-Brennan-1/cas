# CAS: Create a Sim

A Streamlit app, which I made for my Sims-obsessed wife. Plan characters for The Sims 4. Pick a name, hometown, traits and an aspiration, then have an OpenAI model write a backstory based on those choices.

> Need a last-minute entertainer for a birthday party? Mike owns a llama costume and refuses to explain why.
>
> *From the generated backstory of Mike Brennan, an Ambitious, Practice Makes Perfect, Goofball Sim from Willow Creek who wants to be a Renaissance Sim. The [full example](src/cas/data/sims/mike_brennan.json) is included in the repo.*

<img width="1824" height="803" alt="image" src="https://github.com/user-attachments/assets/531dc42b-0997-460d-873a-9dc4caf817bc" />

<img width="1832" height="794" alt="image" src="https://github.com/user-attachments/assets/076f16af-6f8d-4337-8e76-07caa40f1e17" />

<img width="1811" height="807" alt="image" src="https://github.com/user-attachments/assets/39f53254-2b9e-4b37-82f4-aae57ea48711" />

<img width="1738" height="797" alt="image" src="https://github.com/user-attachments/assets/f485a3b2-6cb5-4a77-83a8-8784309d1010" />

## Features

- **Build a profile:** set a name, date of birth, hometown and portrait.
- **Browse game data:** choose from 21 traits, 103 aspirations and 31 worlds. Selecting an aspiration also shows its bonus trait.
- **Generate a backstory:** write one in English or Russian, using the descriptions of the chosen traits and aspiration as context. Adding other supported languages is as simple as updating the Streamlit dropdown.
- **Add a portrait easily:** upload an image, or paste one straight from the clipboard. (`Grateful thanks to Mr Claude for this bit`)
- **Save and reload Sims:** Sims are stored as local json files.

## Tools

| Area | Tool |
| --- | --- |
| Interface | Streamlit |
| Data loading and cleaning | Polars |
| Backstory generation | OpenAI Responses API |
| Image validation | Pillow |
| Dependency management | Poetry |

## Quickstart

You'll need Python 3.12+, [Poetry](https://python-poetry.org/) and an OpenAI API key. The app won't start without a key, even if you don't generate a backstory.

1. Install the dependencies from the project root:

   ```bash
   poetry install
   ```

2. Copy `src/.env.example` to `src/.env`, then replace the placeholder with your key:

   ```
   OPEN_AI_API_KEY=your-key-here
   ```

3. Start the app:

   ```bash
   poetry run streamlit run src/cas/app.py
   ```

To use a different model or change the system prompt, edit [config.py](src/cas/config.py).

## Running the tests

```bash
poetry run pytest
```

The tests don't need an API key. OpenAI is faked and saves go to a temporary folder, so they make no API calls and leave your saved Sims alone.

## How it works

1. Polars loads and cleans the CSV files in `src/cas/data/`, and Streamlit caches the results.
2. When you ask for a backstory, the app looks up the description of each selected trait and aspiration and adds them to the Sim's details. The prompt then carries what each choice means, as well as its name.
3. The details go to the model as JSON, with an extra instruction if the backstory shouldn't be in English.
4. Saved Sims are written to `src/cas/data/sims/` as a `.json` file, with the portrait alongside in a `.image` file.

Clipboard paste isn't built into Streamlit, so it uses a small custom component written in JavaScript. Pasted and uploaded files are both checked with Pillow before they're accepted.

## Project structure

```
tests/                  # pytest suite
src/cas/
├── app.py              # Streamlit interface
├── ai.py               # Backstory prompt
├── open_ai_client.py   # OpenAI API wrapper
├── config.py           # API key, model and system prompt
├── sim_image.py        # Image upload and clipboard paste
├── sim_store.py        # Saving and loading Sims
├── traits.py           # Loading traits, aspirations and worlds
└── data/               # CSV data and saved Sims
```

## To do

- Allow users to refine backstories.
- Reverse the existing workflow to allow users to write a backstory and have the LLM select traits.

## Disclaimer

This is an unofficial fan project, and it isn't affiliated with or endorsed by Electronic Arts or Maxis. The Sims is a trademark of Electronic Arts Inc.
