# Installing HanziFrame

[Русская версия](INSTALL.ru.md)

This guide walks through installing HanziFrame on a 4.7-inch LILYGO T5 and
connecting it to Home Assistant. Home Assistant stores the vocabulary and
renders each card; the display downloads and shows the finished image.

The project is tested with **Home Assistant Core 2026.8.1**, **Pyscript 2.0.1**,
and **ESPHome 2026.7.4**. If a build fails with another ESPHome version, try
2026.7.4 first.

> If you are adding HanziFrame to an existing Home Assistant installation,
> create a backup first. Merge the new sections into `configuration.yaml` and
> `automations.yaml`; do not replace either file wholesale.

## What you need

- a LILYGO T5 4.7-inch ESP32-S3;
- a working Home Assistant server and access to its `/config` directory;
- HACS for installing Pyscript;
- ESPHome Device Builder or the ESPHome CLI;
- a data-capable USB-C cable and stable power;
- 2.4 GHz Wi-Fi from which the display can reach Home Assistant.

The `t547` display driver, fonts, and other required files are already in this
repository. You do not need to download the driver separately.

## 1. Download the project

Clone the repository:

```console
git clone https://github.com/gkopiev/HanziFrame.git
cd HanziFrame
```

Alternatively, choose **Code → Download ZIP** on GitHub and unpack the archive.
You can transfer files into Home Assistant with Studio Code Server, File editor,
Samba, or another method you already use.

If an AI agent is helping, give it the repository URL; it will find the project
rules in `AGENTS.md`. Enter passwords and keys yourself and never paste them into
the chat.

## 2. Set up Home Assistant

### 2.1. Install Pyscript and copy the files

1. Install **Pyscript** through HACS and add the integration to Home Assistant.
2. Copy everything inside the repository's `pyscript/` directory to
   `/config/pyscript/`. This includes `word_generator.py`, `requirements.txt`,
   the CSV file, both fonts, and their licence files.
3. Create `/config/www/` if it does not already exist. HanziFrame writes
   `word.png` there.
4. Enable **Allow all imports** in the Pyscript integration options. If Pyscript
   is configured through YAML, merge this setting into its existing section:

```yaml
pyscript:
  allow_all_imports: true
```

Restart Home Assistant. These actions should appear under **Developer Tools →
Actions**:

- `pyscript.generate_word_image`;
- `pyscript.add_chinese_word`;
- `pyscript.bulk_import_words`;
- `pyscript.import_words_from_csv`.

### 2.2. Create the vocabulary and helpers

Add the official **Local to-do** integration, create a list named
`Chinese words`, and set its entity ID to exactly:

```text
todo.chinese_words
```

Items use the format `Chinese | pinyin | translation`. This Todo list is the
main vocabulary; the bundled CSV is for the initial words and later imports.

Add the following block to `/config/configuration.yaml`. If `input_button:` or
`input_text:` already exists, add only the child entries below it. Do not create
a second top-level section with the same name.

<details>
<summary>Ready-to-copy helper YAML</summary>

```yaml
input_button:
  hanziframe_next_word:
    name: "HanziFrame — Next word"
    icon: mdi:skip-next
  hanziframe_add_word:
    name: "HanziFrame — Add word"
    icon: mdi:plus
  hanziframe_import_words:
    name: "HanziFrame — Import pasted words"
    icon: mdi:playlist-plus
  hanziframe_import_csv_file:
    name: "HanziFrame — Import CSV file"
    icon: mdi:file-import

input_text:
  hanziframe_new_chinese:
    name: "HanziFrame — Chinese"
    max: 100
  hanziframe_new_pinyin:
    name: "HanziFrame — Pinyin"
    max: 100
  hanziframe_new_translation:
    name: "HanziFrame — Translation"
    max: 100
  hanziframe_csv_import_words:
    name: "HanziFrame — Pasted CSV"
    max: 255
```

</details>

Run Home Assistant's configuration check and restart it. The
`sensor.current_hanzi_word` entity appears later, after the first image is
generated.

### 2.3. Generate the first card

Under **Developer Tools → Actions**, call these actions in order:

1. `pyscript.import_words_from_csv` — imports the ten starter words into Todo;
2. `pyscript.generate_word_image` — chooses a word and renders the card.

Confirm that `sensor.current_hanzi_word` now exists and that
`http://YOUR_HOME_ASSISTANT_ADDRESS:8123/local/word.png` shows the card. If it
does, the Home Assistant side is ready.

## 3. Prepare and flash the display

### 3.1. Copy the ESPHome configuration

Copy these into your ESPHome working directory:

- `esphome/lilygo-display.yaml`;
- the complete `esphome/custom_components/t547/` directory;
- `esphome/secrets.example.yaml` as the starting point for local secrets.

Inside Home Assistant, the usual layout is:

```text
/config/esphome/
├── lilygo-display.yaml
├── secrets.yaml
└── custom_components/
    └── t547/
```

If `secrets.yaml` already exists, do not replace it: add the four keys from
`secrets.example.yaml`. Otherwise copy the example to `secrets.yaml`. Fill in
the Wi-Fi details, API encryption key, and OTA password. Never publish or commit
the file containing real values.

`api_encryption_key` must be 32 random bytes encoded as Base64. If needed, you
can generate it and an OTA password locally:

```console
openssl rand -base64 32
openssl rand -hex 24
```

Use the first result for `api_encryption_key` and the second for
`ota_password`.

`lilygo-display.yaml` uses this image URL by default:

```text
http://homeassistant.local:8123/local/word.png
```

If other devices on your network cannot open `homeassistant.local`, replace
only the host with Home Assistant's local IP address.

### 3.2. Build and install the firmware

ESPHome Device Builder is the easiest route:

1. Open `lilygo-display.yaml` and run **Validate**.
2. Connect the LILYGO board with a data-capable USB-C cable.
3. Select **Install** and choose the appropriate USB installation method.

With the ESPHome CLI, first create `esphome/secrets.yaml` in the clone, then run
this from the repository root:

```console
esphome run esphome/lilygo-display.yaml
```

Before writing, make sure the selected USB device is the LILYGO display. After
the first boot, Home Assistant should offer to add the new ESPHome device. Add
it and enter the same `api_encryption_key` through the Home Assistant UI. If it
is not discovered automatically, add the **ESPHome** integration manually and
enter the device hostname or IP address.

The device should appear as `hanzi-frame` and expose
`button.hanzi_frame_refresh_chinese_word`.

## 4. Add the automations

`homeassistant/automation.yaml` contains three automations:

- change the word when Home Assistant starts and every ten minutes;
- change the word when the **Next word** helper is pressed;
- add and import words through the helper entities.

Open your existing `/config/automations.yaml` and append the three list items
from the repository file. **Do not replace your whole `automations.yaml`.** Run
Home Assistant's configuration check, then reload the automations.

## 5. Add a dashboard

Four cards are enough for the first working dashboard:

- a Markdown card with the rendered image;
- a Tile card for `input_button.hanziframe_next_word`;
- a Tile card for `button.hanzi_frame_refresh_chinese_word`;
- a To-do List card for `todo.chinese_words`.

Paste this into the Markdown card:

```yaml
type: markdown
content: >-
  <img src="/local/word.png?v={{ state_attr('sensor.current_hanzi_word', 'image_version') | int(0) }}"
       style="width:100%;border-radius:8px;" alt="HanziFrame preview">
entity_id:
  - sensor.current_hanzi_word
```

The `image_version` value prevents the browser from showing an old cached
image. To manage the vocabulary from a phone, you can also add:

- `input_text.hanziframe_new_chinese`,
  `input_text.hanziframe_new_pinyin`,
  `input_text.hanziframe_new_translation`, and
  `input_button.hanziframe_add_word`;
- `input_text.hanziframe_csv_import_words`,
  `input_button.hanziframe_import_words`, and
  `input_button.hanziframe_import_csv_file`.

The quick-paste format is `汉字,hànzì,translation`; separate multiple rows with
`;;`.

## 6. Check the result

The installation is complete when:

- `todo.chinese_words` contains the starter words;
- `/local/word.png` opens and shows a card;
- the `hanzi-frame` device is online in Home Assistant;
- the display refresh button loads the card onto the E-Ink screen;
- **Next word** changes both the dashboard preview and the physical display.

## Troubleshooting

| Problem | What to check |
|---|---|
| Pyscript actions are missing | Confirm the files are in `/config/pyscript/`, `allow_all_imports` is enabled, Home Assistant was restarted, and Pillow installed from `requirements.txt`. |
| `no_active_todo_words` | The Todo list is empty. Import the starter CSV or add a word manually. |
| `/local/word.png` is missing | Run `pyscript.generate_word_image` and confirm `/config/www/` exists and is writable. |
| ESPHome cannot find `t547` | Copy the complete `custom_components/t547/` directory next to the YAML and run a Clean build. |
| The image exists but the display does not refresh | Check the refresh entity and open the image URL from another device on the same network. Replace `homeassistant.local` with the Home Assistant IP address if needed. |
| The dashboard shows an old image | Confirm the Markdown card contains both `image_version` and `entity_id`. |
| USB installation does not start | Check that the cable carries data, select the correct port, and put the board into boot mode if needed. |
| Screen colours are reversed | Do not add another inversion in ESPHome; Pyscript already inverts the image. |

## Official guides

- [Install Pyscript](https://hacs-pyscript.readthedocs.io/en/latest/installation.html)
- [Configure Pyscript and `allow_all_imports`](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html)
- [Home Assistant Local to-do](https://www.home-assistant.io/integrations/local_todo/)
- [Getting started with ESPHome](https://esphome.io/guides/)
