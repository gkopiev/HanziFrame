# HanziFrame

**English** · [Русский](README.ru.md)

**Chinese words, always in sight.**

HanziFrame is a smart display that helps you learn Chinese words. It shows and
regularly cycles through vocabulary cards with Chinese characters, pinyin, and
translations. Cards can also be changed on demand, while the vocabulary can be
managed from a phone through a Home Assistant dashboard.

**[What you need](#what-you-need) ·
[Full installation guide](docs/INSTALL.md) ·
[AI-assisted installation](#ai-assisted-installation)**

<p align="center">
  <img src="assets/Display_Photo.png" alt="HanziFrame showing a Chinese word, pinyin, and Russian translation on a 4.7-inch LILYGO T5 E-Ink display" width="900">
</p>

## How it works

Home Assistant chooses the next word and renders a complete frame for it. The
display fetches that image over the local network and keeps it on screen until
the next refresh. No cloud API is required for everyday use: the vocabulary,
logic, and images stay on your home network.

## How to use it

1. Add a word from your phone: Chinese characters, pinyin, and a translation.
   You can also paste several rows or import a CSV file.
2. Wait for the scheduled update or press **Next word** on the Home Assistant
   dashboard.
3. Mark a learned word as completed in Todo. It leaves the display rotation but
   remains in your vocabulary.

Words can be edited or removed directly in Home Assistant. Translation text can
use any characters available in the bundled font; the starter vocabulary uses
Russian translations. The refresh interval is configurable too.

<p align="center">
  <img src="assets/Home_Assistant_Dashboard.png" alt="HanziFrame dashboard in Home Assistant showing the current card with a Chinese word, pinyin and translation, display controls, word entry and import, and the Todo list" width="900">
  <br>
  <sub>Home Assistant dashboard: the current card, display controls, word entry and import, and the Todo vocabulary.</sub>
</p>

## What you need

Core components:

- [LILYGO T5 4.7″ E-Paper](https://lilygo.cc/products/t5-4-7-inch-e-paper-v2-3)
  with an ESP32-S3;
- a running Home Assistant server and Wi-Fi;
- a data-capable USB-C cable for the first firmware installation;
- stable USB power for everyday operation.

The board works without an enclosure. For a tidy desktop build, the device in
the photo uses an [external enclosure by Vladimir Varzaru](https://www.printables.com/model/741304-lilygo-t5-47-inch-case),
licensed under CC BY 4.0. Its model files are not part of this repository. The
pictured build uses **M2×3.2×4** heat-set inserts and **M2×5** screws.

Test-fit the board and plug in the USB-C cable before installing the inserts.
Different LILYGO revisions may fit slightly differently: the board can be
tight, the USB-C opening suits a slim connector, and the enclosure button may
not align perfectly with the board button. Make any small adjustments before
the final assembly.

## Under the hood

HanziFrame keeps the display itself as a simple thin client:

- **Home Assistant + Pyscript** manage the vocabulary, choose a word, and
  render the complete 960×540 image;
- **ESPHome** downloads that image and sends it to the E-Ink panel;
- **Local Todo** is the main vocabulary, while CSV provides convenient bulk
  import;
- the **t547** display driver is already included, so there is no separate
  download or manual patch.

The project is tested with **Home Assistant Core 2026.8.1**, **Pyscript 2.0.1**,
and **ESPHome 2026.7.4** on a LILYGO T5 4.7″ ESP32-S3. Recheck display-driver
compatibility before moving to other versions.

## Installation

HanziFrame is a DIY project, not a one-click Home Assistant add-on. You install
the Home Assistant side, flash the display once over USB, and connect the two
over the local network. All source files, fonts, reference automations, and the
vendored display driver used by the tested stack are included in the repository.

**[Open the complete installation guide →](docs/INSTALL.md)**

It covers the complete route from downloading the project to the first frame on
the display. If Home Assistant and ESPHome are already configured, the same
guide explains how to add HanziFrame without replacing your existing
configuration wholesale.

## AI-assisted installation

To install with Codex, Claude Code, or another coding agent, start a new task
with one prompt:

> Help me install and configure the project
> `https://github.com/gkopiev/HanziFrame` in my environment.

The agent will find the remaining steps and safe-installation rules in the
repository itself.

## Licenses and credits

Original HanziFrame code and documentation are licensed under the
[MIT License](LICENSE). Third-party components, fonts, and media retain their
respective terms; see
[Third-party and asset notices](THIRD_PARTY_NOTICES.md).

Device photo and creator-owned content in the dashboard screenshot: © 2025–2026
gkopiev, CC BY 4.0. Depicted third-party UI retains its own terms; see the
[media notice](assets/LICENSE.md). The process for reporting vulnerabilities is
described in the [security policy](SECURITY.md).
