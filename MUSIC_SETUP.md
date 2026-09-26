# Music playback

JioSaavn resolution and fallback have been removed. Text searches use YouTube,
with SoundCloud search as a fallback. A selected URL plays from its actual
source; it is not silently replaced with a different recording.

On the machine running the bot, use a working Python environment and install
the updated requirements:

```powershell
python -m pip install -U -r requirements.txt
```

FFmpeg and either a supported Node.js or Deno must be available on PATH.
The resolver enables installed Node.js/Deno runtimes and the requirements include
yt-dlp's challenge solver dependencies. See the
[official yt-dlp setup guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Restart the bot after updating. Use `!play <song or YouTube/SoundCloud URL>`,
then `!autoplay` to enable matching recommendations. `!stop` clears the queue
and disables autoplay; `!autoplay` enables it again. Use your configured prefix
if it differs from `!`.

Offline checks:

```powershell
python -m unittest discover -s tests -v
python -m py_compile music_cog.py bot.py
```

Live acceptance check: request two songs, skip once, let autoplay choose the next
song, then stop while it is finding a recommendation. Confirm that audio matches
the displayed song and that stop leaves playback stopped. Network/provider
restrictions still require testing on the actual hosting machine.

The checked-in local `venv` launcher currently references a Python installation
under another Windows user and could not run during verification. Offline tests
were run with a separate available Python runtime; the bot was not started.

Additional verification used isolated dependencies under `.local/music-verify`:
music module import, agent reply formatting, a public YouTube song search, stream
resolution, and two seconds of FFmpeg audio decoding passed. This does not test
Discord voice delivery, every song/source, or hosting-provider restrictions.

AI chat now retains conversation roles and images in gateway requests, keeps
Markdown/code intact, and reports provider outages instead of inventing an answer.
The gateway model can be selected with `OMNIROUTE_MODEL`; Gemini still uses
`GEMINI_MODEL`. Chat quality depends on the selected model and provider availability.
Live AI requests were not tested. Provider safeguards remain in place.
