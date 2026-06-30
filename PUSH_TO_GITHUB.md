# How to put this on GitHub

Run these from inside the `veeder-root-pi` folder. Pick ONE of the two options.

The repo is safe to make **public**: `config.py` (with the real password) is
git-ignored, so only the placeholder template gets pushed. A public repo means
no GitHub login is needed on any Pi.

## Option A — with the GitHub CLI (`gh`), easiest

If you have the `gh` CLI installed and logged in (`gh auth login`):

```bash
cd veeder-root-pi
git init
git add .
git commit -m "Initial commit: Veeder-Root Pi capture + SFTP upload"
gh repo create veeder-root-pi --public --source=. --push
```

Use `--private` instead if you prefer — but then each Pi needs a token to
clone (see note at the bottom).

## Option B — plain git, create the repo on github.com first

1. Go to https://github.com/new and create an empty repo named
   `veeder-root-pi` (no README, no .gitignore — this folder already has them).
2. Then run:

```bash
cd veeder-root-pi
git init
git add .
git commit -m "Initial commit: Veeder-Root Pi capture + SFTP upload"
git branch -M main
git remote add origin https://github.com/YOURUSER/veeder-root-pi.git
git push -u origin main
```

Replace `YOURUSER` with your GitHub username.

## After it's pushed

On any new Pi, the whole setup becomes:

```bash
git clone https://github.com/YOURUSER/veeder-root-pi.git
cd veeder-root-pi
sudo ./install.sh
nano config.py        # set store name, serial port, SFTP password
```

## If you make the repo private instead

A private repo needs authentication to clone on the Pi (a GitHub username +
password will NOT work). Easiest is a read-only Personal Access Token:

1. github.com → Settings → Developer settings → Fine-grained tokens → generate
   one with read access to this repo.
2. Clone with the token embedded:

```bash
git clone https://YOURUSER:[email protected]/YOURUSER/veeder-root-pi.git
```

Keeping the repo public avoids all of this, which is why it's recommended.
