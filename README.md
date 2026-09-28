# Escape Room: Phone Line

A Filipino/Taglish-themed escape room kit: a 1000-name phonebook elimination puzzle, a phone simulator app players "call" numbers with, and print props (classifieds page, phonebook directory).

## Structure

```
app/            The call simulator (the actual game). app/index.html is the built,
                self-contained file — GitHub Pages serves it directly.
                app/template.html is the source template tools/build_app.py fills in.
printables/     Print-and-fold props: the classifieds page and the phonebook
                directory, each as both source .html and rendered .pdf.
data/           All game content as editable source of truth:
                  phonebook.csv / phonebook.yaml — the 1000 names + roles
                  filter_rules.yaml   — the 10 elimination clues players use
                  call_scripts.yaml   — what clue/special phone numbers say
                  app_config.yaml     — free-call limit, cooldown, ring timing,
                                        the secret reset code, the target's script
tools/          Build scripts and GM-only helpers (not needed by players):
                  build_app.py            — data/ + app/template.html -> app/index.html
                  build_phonebook_pdf.py  — data/phonebook.csv -> printables/phonebook_directory.html
                  filter_phonebook.py / filter_phonebook.ipynb — interactive elimination checker
                  wrong_scripts.py        — the 100 "wrong number" flavor lines
index.html      Redirects the site root to app/, so GitHub Pages "just works"
                whether Pages is pointed at the repo root or you open the site URL directly.
```

## Rebuilding after editing `data/`

Edits to `data/*.yaml` or `data/phonebook.csv` don't take effect until you rebuild —
these are baked into `app/index.html` and `printables/*.html` at build time, not read live.

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

./.venv/bin/python tools/build_app.py
./.venv/bin/python tools/build_phonebook_pdf.py

# re-render the PDFs (requires Google Chrome installed locally)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --print-to-pdf="printables/phonebook_directory.pdf" --print-to-pdf-no-header --no-pdf-header-footer \
  printables/phonebook_directory.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --print-to-pdf="printables/classifieds.pdf" --print-to-pdf-no-header --no-pdf-header-footer \
  printables/classifieds.html
```

To check your elimination puzzle still resolves to exactly one name after editing
`data/filter_rules.yaml`, run `./.venv/bin/python tools/filter_phonebook.py` (interactive CLI)
or open `tools/filter_phonebook.ipynb`.

## GitHub Pages

Push this repo and enable Pages (Settings → Pages → Deploy from branch → `main` / `root`).
No further config needed — `index.html` at the repo root redirects to `app/`, which is
the fully self-contained game.

**Before making the repo public**, know that everything in `data/` — including
`call_scripts.yaml` (the clue answers), `app_config.yaml` (the target's cure script and
the secret reset code), and `phonebook.csv` (which row is `target`) — is plain-text and
readable by anyone who browses the repo on GitHub, regardless of whether Pages is even
enabled. This is separate from the app itself: `app/index.html` also embeds all of this
data client-side (unavoidable for a static site with no backend), so anyone who opens
browser devtools on the deployed page can read it too. Neither is a problem for players
using the app normally, but if you want to keep the answers offline from anyone who
might poke around, keep the repo **private** until after the event (Pages on private
repos needs GitHub Pro/Team/Enterprise — Free tier only serves Pages from public repos).
