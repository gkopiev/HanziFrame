# HanziFrame agent guide

This file is for coding and installation agents. Human readers should start with
`README.md` or `README.ru.md` and follow the matching guide in `docs/INSTALL*`.

## Project model and invariants

HanziFrame is a Home Assistant + ESPHome E-Ink flashcard display for learning
Chinese characters. Keep the device a thin client: Home Assistant selects a word
and renders the image; the ESP32 only downloads and displays it.

- Home Assistant Pyscript owns vocabulary selection, state, fonts, layout and
  image rendering.
- `todo.chinese_words` is the primary vocabulary source. CSV is an import/backup
  source and a fallback only when the Todo service is unavailable. An available
  but empty Todo means that there are no active words.
- The bundled CSV is a small ten-entry themed starter set, not a full vocabulary.
- Pyscript publishes `sensor.current_hanzi_word` for dashboard status and image
  cache-busting.
- The output is a 960x540 RGB `/config/www/word.png`, inverted exactly once with
  `ImageOps.invert()` before saving. Never invert it again in ESPHome.
- ESPHome downloads `/local/word.png` as `GRAYSCALE`, uses
  `update_interval: never`, and refreshes only on request.
- PSRAM is mandatory for the 960x540 online-image buffer.
- Keep the vendored `esphome/custom_components/t547/` self-contained. Do not
  replace it with a remote runtime dependency.
- Keep the dashboard header free of a separate current-word Markdown block; the
  E-Ink preview already shows that information.

## Main entry points

- `pyscript/word_generator.py` — Todo/CSV services and image rendering.
- `homeassistant/automation.yaml` — fresh-install/merge reference; never use it
  to overwrite a complete live `automations.yaml`.
- `esphome/lilygo-display.yaml` — public device configuration.
- `docs/INSTALL.md` and `docs/INSTALL.ru.md` — practical installation and
  troubleshooting guides for home users.
- `THIRD_PARTY_NOTICES.md` — licence boundaries and upstream credits.

Runtime state, build output, firmware binaries, live backups and credentials are
not public source files.

## Supported baseline and stable IDs

- Home Assistant Core 2026.8.1; Pyscript 2.0.1; exact ESPHome 2026.7.4.
- Native `esp-idf` toolchain with `framework: type: arduino`.
- LILYGO T5 4.7-inch ESP32-S3, 960x540, octal PSRAM.
- Python dependency: Pillow.

Fresh installations use these identifiers:

- device: `hanzi-frame`;
- refresh: `button.hanzi_frame_refresh_chinese_word`;
- vocabulary/status: `todo.chinese_words`, `sensor.current_hanzi_word`;
- next word: `input_button.hanziframe_next_word`;
- add form: `input_text.hanziframe_new_chinese`,
  `input_text.hanziframe_new_pinyin`,
  `input_text.hanziframe_new_translation`,
  `input_button.hanziframe_add_word`;
- imports: `input_text.hanziframe_csv_import_words`,
  `input_button.hanziframe_import_words`,
  `input_button.hanziframe_import_csv_file`.

Do not silently rename an existing installation. Preserve its working IDs or
give the user an explicit migration plan.

## Safety and change gates

- Never read, print, copy or commit secret values, `.env` files, private keys,
  Home Assistant storage/databases or raw logs that may contain credentials.
- Public ESPHome YAML uses only `!secret` references: `wifi_ssid`,
  `wifi_password`, `api_encryption_key` and `ota_password`. The user's ignored
  `secrets.yaml` is edited only by the user.
- Inspect and merge only the intended HanziFrame pieces. Never replace a whole
  live Home Assistant configuration tree.
- Live Home Assistant writes require explicit approval.
- A successful compile is not deployment. USB flashing and OTA uploading each
  require separate explicit approval, an identified artifact and a rollback
  plan.
- Ask before adding dependencies, changing stable IDs, changing the image
  format or default image URL, or editing vendored `t547` implementation files.
- Do not commit, push, open a pull request or publish a release unless the user
  explicitly asks for that exact action.
- Before an approved commit or push, inspect the exact staged manifest/diff and
  repeat a redacted secret/private-artifact scan of that staged snapshot.

## Compatibility traps

- Pyscript 2.0.1 interpreted functions do not support generator expressions.
  Use explicit loops or keep native-only helpers inside `@pyscript_compile`.
- Move blocking file and Pillow work through `task.executor()` or a suitable
  Pyscript executor boundary.
- Publish sensor attributes with `state.set(..., new_attributes={...})`.
- Treat `todo.get_items()` as a response action and validate its returned data.
- Store Todo items as `{chinese} | {pinyin} | {translation}` and parse them with
  `split(" | ", 2)` so translations may contain `|`.
- Keep CSV UTF-8 without BOM and preserve the header
  `chinese,pinyin,translation`; add/import services must remain duplicate-safe.
- In ESPHome use `image:` with `platform: online_image`, `type: GRAYSCALE`,
  `resize: 960x540` and `update_interval: never`.
- Keep first-class `psram:` configuration: octal, 80 MHz,
  `ignore_not_found: false`. `toolchain: esp-idf` does not replace
  `framework: type: arduino`.
- Do not add `invert_alpha` or restore manual Arduino USB flags without a
  physical test proving a need.
- A resolution or PNG-to-BMP change must update both Python and ESPHome and
  requires the user's approval.

## Validation and evidence

Report only the strongest level actually completed:

1. Static — syntax, CSV parsing and config/schema checks.
2. Build — clean compile and link.
3. Device — boot, PSRAM, driver allocation and physical display.
4. Live system — Home Assistant entities, services, automation and end-to-end
   refresh.

Never present config success as a build, a build as a flash, or a brief device
check as long-duration stability evidence. Reuse recorded evidence only when its
scoped files, dependency versions and relevant environment are unchanged. A
CPython syntax check alone does not prove compatibility with the Pyscript
runtime.

Safe local checks from the repository root:

```sh
python -m py_compile pyscript/word_generator.py
python -c "import csv; list(csv.DictReader(open('pyscript/apps/chinese_display/data/chinese_words.csv', encoding='utf-8')))"
git diff --check
```

Run `esphome config esphome/lilygo-display.yaml` only after the user has created
an ignored local secrets file, or in an isolated copy with dummy secrets. Never
use a validation route that prints fully substituted configuration.

## Documentation and licences

- Keep English and Russian docs aligned on architecture, versions, entities,
  installation, limitations and licences. Write INSTALL as one practical path
  for a home DIY user; keep release audits, evidence matrices and agent workflow
  out of the public guide. Keep it focused on a fresh installation unless an
  update path is actually supported and needed.
- Lead README with the learner benefit. Keep hardware summaries at the
  board-and-MCU level; retain panel and memory constraints in technical
  configuration and this guide.
- Keep public examples generic: no personal paths, private entity IDs, rollout
  diaries, firmware hashes or environment-specific claims.
- The repository is mixed-licence, not MIT-only. Preserve the notices and
  bundled licence files described in `THIRD_PARTY_NOTICES.md`.
- Update this guide when architecture, dependencies, stable IDs, safety gates or
  validation policy changes.
