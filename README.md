# Wasichu Tap

## CI Book Tracker

A local-first reading tracker for language learners. Install it, start it,
and open `http://localhost:4000` in your browser:

```sh
brew install wasichu/tap/ci-book-tracker
ci-book-tracker
```

Stop it with Ctrl-C. The app creates its database and session secret on first
start and applies database migrations automatically. User data is kept outside
the Homebrew installation, so upgrades preserve it.

Native packages support Apple Silicon and Intel Macs running macOS 15+, and
x86-64 Linux with Ubuntu 24.04-compatible system libraries. See the
[application's distribution guide](https://github.com/wasichu/ci-book-tracker/blob/main/docs/distribution.md)
for configuration and Linux library requirements.

## How do I install these formulae?

`brew install wasichu/tap/<formula>`

Or `brew tap wasichu/tap` and then `brew install <formula>`.

Or, in a `brew bundle` `Brewfile`:

```ruby
tap "wasichu/tap"
brew "<formula>"
```

## Documentation

`brew help`, `man brew` or check [Homebrew's documentation](https://docs.brew.sh).

## go-whassup release automation

The hourly `brew bump` workflow discovers formula updates. For go-whassup only,
`scripts/publish-go-whassup.py` completes the handoff for a published stable
GitHub release: it checks the bot PR's exact formula diff/source checksum,
dispatches `tests.yml` on the expected commit, then runs `publish.yml` after
successful builds. No extra cross-repository token is needed. Other formulae
and general PRs retain manual review.

Run the release policy checks locally:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Failed checks or changed commits stop publication. Inspect/rerun the failed job
before retrying the hourly workflow. Manual `brew pr-pull` publishing remains
available through `publish.yml`; pass the expected PR head SHA.
