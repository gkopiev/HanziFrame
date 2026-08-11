# T547 component attribution

HanziFrame vendors the ESPHome component for the LILYGO T5 4.7-inch
ESP32-S3 e-paper display from:

- Upstream: [hbast/lilygo_t5_47_plus](https://github.com/hbast/lilygo_t5_47_plus)
- Imported commit: [`f6997e3250e7a1bbd97dc5e2fd3044ac883bf490`](https://github.com/hbast/lilygo_t5_47_plus/tree/f6997e3250e7a1bbd97dc5e2fd3044ac883bf490/components/t547)
- Commit date: 2025-12-05

Copyright remains with the respective upstream authors and contributors.

## Provenance and acknowledgements

The ESPHome adapter originated in
[`tiaanv/esphome-components`](https://github.com/tiaanv/esphome-components)
at commit `821d142`. Tiaan Viljoen confirmed in
[issue #4](https://github.com/tiaanv/esphome-components/issues/4#issuecomment-1330058461)
that it may use the ESPHome license.

The component then developed through these repositories:

1. [nickolay/esphome-lilygo-t547plus](https://github.com/nickolay/esphome-lilygo-t547plus), including the documented import in [`e364d3e`](https://github.com/nickolay/esphome-lilygo-t547plus/commit/e364d3efb1e7d91021065619652caad9f325cd4c);
2. [LouisMT/esphome-lilygo-t547plus](https://github.com/LouisMT/esphome-lilygo-t547plus), including the display runtime import in [`d27cc08`](https://github.com/LouisMT/esphome-lilygo-t547plus/commit/d27cc08cd905723a7673b1fbf1d21fc45f10efa8);
3. [dabalroman/esphome-lilygo-t547plus_esphome-2025.11](https://github.com/dabalroman/esphome-lilygo-t547plus_esphome-2025.11);
4. [hbast/lilygo_t5_47_plus](https://github.com/hbast/lilygo_t5_47_plus).

The bundled display runtime derives from
[Xinyuan-LilyGO/LilyGo-EPD47](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47/tree/68a99369c61c6d789208016b279c9cd2454f3daa/src),
whose driver work in turn credits
[vroland/epdiy](https://github.com/vroland/epdiy).

Thanks to Tiaan Viljoen, Nickolay Ponomarev, Darrell Chan, `bvarick`, Louis
Matthijssen, Roman Dąbal, Holger Bast, the LILYGO/Lewis He contributors,
Valentin Roland and every contributor recorded in the upstream histories.

## HanziFrame modifications

Changes prepared on 2026-07-11 relative to the imported commit:

- `display.py` declares the bundled Arduino `SPI` and `Wire` libraries for
  selective compilation in ESPHome 2026.2+ and enables the built-in ESP-IDF
  `esp_driver_rmt` component plus the legacy `driver` shim, with a compatibility
  fallback for ESPHome versions that predate the helper API;
- `ed047tc1.c`, `ed047tc1.h`, `epd_driver.h`, `i2s_data_bus.c`,
  `i2s_data_bus.h`, `rmt_pulse.c`, `rmt_pulse.h` and `t547.cpp` have only a
  newline-at-EOF normalization. This makes no functional runtime change.

No other local implementation changes are intended. The pinned tree and these
notices should be reviewed together whenever the component is refreshed.

## License

The component retains the ESPHome License: Python and other non-runtime files
are licensed under MIT; C/C++ runtime files are licensed under GPLv3. The full
upstream license text is preserved in [LICENSE](LICENSE).

The imported LILYGO runtime is distributed under GPLv3. Its `epdiy` ancestry
is credited above; see the upstream projects for their original notices and
history.
