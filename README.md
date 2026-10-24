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
