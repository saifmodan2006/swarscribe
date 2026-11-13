# Contributing to FlowScribe

Thanks for stopping by. FlowScribe grows the way good open source does: small, tested, focused changes.

## Ground rules

1. **The core stays dependency free.** New heavy libraries belong behind an optional extra in `pyproject.toml`, like `whisper`, `parakeet`, `api` and `desktop` already are.
2. **Local first is not negotiable.** A feature that uploads audio or text by default will not be merged, however shiny it is.
3. **Every feature ships with a test.** The suite is plain stdlib `unittest`, so it runs anywhere Python does, and under pytest too.
4. **Keep PRs small.** One feature or one fix per PR, with the demo still passing.

## Getting started

```bash
git clone https://github.com/saifmodan2006/flowscribe.git
cd flowscribe
pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
```

## Where things live

- Cleanup behaviour: `src/flowscribe/cleanup.py` and `formats.py`
- Voice editing: `commands.py` · Code dictation: `codemode.py`
- Meetings: `meeting.py` · Learning: `learn.py`
- Web demo: `web/` (a faithful JS port of the cleanup pipeline, keep the two in step when you change behaviour)

## Good first contributions

- A spoken format FlowScribe does not know yet (dates, times, amounts, addresses)
- A phrasebook pair for translation mode
- A per-app style for an app you dictate into every day
- A cleanup edge case with a failing test that proves it
