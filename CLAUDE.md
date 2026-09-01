# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**EIGUIT / "Guitar Studio IA"** — a fullscreen desktop app for guitarists: an interactive virtual
fretboard, a harmonic-field / CAGED engine, real-time mic pitch detection, a tablature
editor/player, mini-games, and AI audio-to-tab transcription. The core is a single Pygame
process; transcription runs as a separate microservice stack with a React web frontend.

The repo hosts **four independently-run programs**:

| Program | Entry point | Runtime |
|---|---|---|
| Desktop app (main product) | `main.py` | Python 3.12, Pygame 60 FPS loop |
| Music-theory CLI | `studio_cli.py` | Python 3.12, `rich` TUI |
| Transcription API + worker | `services/transcription/` | **Python 3.11**, own venv `venv_ia` |
| Web frontend | `web_frontend/` | Node / Create React App |

## Commands

### Desktop app
```bash
uv sync                 # install deps from pyproject.toml + uv.lock (Python 3.12)
uv run python main.py    # run (or: activate a venv and `python main.py`)
uv run python studio_cli.py
```
The app opens a customtkinter **login window first** (`ui/tela_login.py`); it will not start
without authenticating against the cloud Postgres DB, which must be reachable.

### Transcription service (separate 3.11 environment)
```bash
cd services/transcription
../scripts/Start-IA.ps1          # creates venv_ia (py -3.11), installs requirements.txt, starts Celery
# or manually:
python main.py                   # FastAPI on :8000
python -m celery -A tasks worker --loglevel=info -P solo
```
Requires a Redis broker on `localhost:6379` (the batch file starts one via Docker). The
pipeline shells out to `demucs` (stem isolation) then `basic-pitch` (transcription).

### Full stack at once (Windows)
`Ligar_GuitarStudio.bat` boots the "orchestra": Redis (Docker) → FastAPI → Celery → React.

### Web frontend
```bash
cd web_frontend && npm install && npm start   # dev server, talks to the API on :8000
```

### Tests / lint
There is **no test suite and no linter/formatter configured.** `robo_testes_ui.py` is an
ad-hoc `pyautogui` UI-clicking robot, not an automated test. The `.github/workflows/deploy.yml`
pygbag→WASM→GitHub Pages job is experimental and does not reflect how the app is normally run.

## Architecture

The codebase was refactored from a flat layout into layered packages. **The README's
"How to Run" and file-tree sections are stale** (they describe the pre-refactor flat files and
`pip install pygame-ce ...`); trust `pyproject.toml` and the actual directories instead.

### Desktop app data flow
- **`main.py`** — initialization + the 60 FPS `while` loop only. No feature logic goes here.
  Each frame: pull audio analysis → translate events → run module logic → render workspace →
  render fixed UI → flip.
- **`core/estado_app.py` → `EstadoGlobal`** — the single source of truth. One instance is
  created in `main.py` and threaded through nearly every function. New global/runtime state
  belongs here (or on `Configuracoes` for user preferences).
- **`core/controlador_eventos.py`** — the only input handler. Consumes the translated Pygame
  event queue and mutates `EstadoGlobal` / modules.
- **`ui/renderizador_ui.py`** — owns all draw calls. `desenhar_workspace()` draws the
  pannable content; `desenhar_ui_fixa()` + `desenhar_painel_superior()` draw the fixed chrome.
- **`core/config.py` → `Configuracoes`** — user-adjustable preferences (colors, fonts, theme,
  language, note-display mode), persisted per profile.
- **`config/` package** (`theme.py`, `ui_metrics.py`, `app_settings.py`) — static design
  tokens / layout constants, wildcard-imported (`from config.theme import *`). Note this is a
  *different* thing from `core/config.py`.

### Virtual camera / viewport
`core/modulos/modulo_camera.py → CameraWorkspace` renders the scene to an off-screen virtual
surface with pan/zoom, then blits it into the viewport **below `ALTURA_TOPBAR`** (the top bar
is fixed, non-pannable). `main.py` monkey-patches `pygame.mouse.get_pos` so all downstream code
sees *virtual* mouse coordinates; mouse events are re-emitted with translated `pos`. When
touching input or hit-testing, be aware coordinates may be virtual-space.

### Feature modules — `core/modulos/`
Self-contained features, each with a `processar_logica(...)` and/or a `desenhar_*` method:
`modulo_campo_harmonico` (interval math + CAGED overlay), `modulo_metronomo` (threaded BPM),
`modulo_processamento` (DSP / FFT pitch detection), `modulo_synth` + `audio/tab_synth.py`
(numpy tablature synthesizer), `modulo_songsterr` (Songsterr tab search API),
`modulo_perfil` (profile load/save), `modulo_ia_transcricao` (HTTP client to the FastAPI
service), `modulo_dados_tab` (tablature data structure). Scale/mode dictionaries are generated
by `ui/fabrica_escalas.py` from the `modulos_escala_*` / `modulos_modos` / `modulos_penta*`
data files.

### Other subsystems
- **`audio/global_audio.py → GlobalAudioEngine`** — mic capture + continuous polyphonic pitch
  analysis; `main.py` reads `freq_detectada` / `notas_polifonicas` from it every frame.
- **`Jogos/`** — gamification (`Jogos_interativos.py` manager + `acerte_a_nota.py` etc.).
- **`DragDrop/`** — draggable UI panels (`ElementoArrastavel`) and snap-guide rendering; the
  various `dragger_*` attributes on `EstadoGlobal` are these movable panels.
- **`BD/gerenciador_remoto_db.py → GerenciadorDB`** — Neon (cloud PostgreSQL) via `psycopg`.
  Tables: `usuarios`, `perfis` (settings as JSONB), `projetos` (saved tablatures as JSON text),
  `favoritos`. The connection string is currently hard-coded in this file.
- **`core/i18n.py`** — runtime translation via `deep-translator` (Google), exposed as a
  `_t` / `_t()` builtin, cached in `translation_cache.json`.

### Transcription service
`services/transcription/main.py` (FastAPI) accepts an upload, saves it to `temp_audio/`, and
enqueues a Celery task in `tasks.py`. The task runs Demucs → basic-pitch → `music21`
MIDI→JSON, plus `librosa` BPM detection, and returns notes + BPM. The desktop app polls
`GET /status/{task_id}`; the React frontend renders results with alphaTab.

## Conventions (from CONTRIBUTING.md)

- **Code identifiers are in Portuguese.** `snake_case` for functions/variables, `PascalCase`
  for classes. Match this in new code.
- Keep `main.py` limited to init + loop; put logic in a module.
- **Do not create `Surface`s inside render loops** — pre-build them. The intentional exception
  is `SRCALPHA` surfaces for the CAGED transparency effect.
- New panels/menus must use the existing custom scroll + clipping-mask system in
  `renderizador_ui.py`, not roll their own.
- Portuguese docstrings follow a fixed auto-generated template ("Como funciona / Para que serve
  / Onde é usada"). They are boilerplate — verify against the actual code, don't rely on them.

## Repo noise to ignore

Root-level one-off scripts left over from the refactor: `fix_imports*.py`,
`refactor_clean_arch.py`, `docstring_generator.py`, `robo_testes_ui.py`, plus `utils/*.py`
analysis scripts, `1.png`, `rec_*.wav`, `*_cache.json`, `tasks_docstrings.json`. `build/`,
`dist/`, `venv*/`, `.venv/`, `TranscriptionService/`, and `services/transcription/temp_audio/`
are generated/local.

## Licensing

Proprietary — "Copyright Reserved", non-commercial, educational use only (see `License`).
