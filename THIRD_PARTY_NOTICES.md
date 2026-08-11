# Third-party and asset notices

Original HanziFrame code and documentation are licensed under the root
[MIT License](LICENSE). The materials below retain separate terms. This file
maps those terms; it does not replace any full license text kept beside the
corresponding material.

## Vendored `t547` component

- Imported source: [`hbast/lilygo_t5_47_plus`, commit `f6997e3`](https://github.com/hbast/lilygo_t5_47_plus/tree/f6997e3250e7a1bbd97dc5e2fd3044ac883bf490/components/t547)
- Adapter lineage: `tiaanv` → `nickolay` → `LouisMT` → `dabalroman` → `hbast`
- Bundled driver lineage: [Xinyuan-LilyGO/LilyGo-EPD47](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47) and [vroland/epdiy](https://github.com/vroland/epdiy)
- License: Python and other non-runtime files are MIT; C/C++ runtime files are GPLv3 under the ESPHome License

Copyright remains with the respective upstream authors and contributors. See
the component's complete [provenance and local-change record](esphome/custom_components/t547/ATTRIBUTION.md)
and [full license text](esphome/custom_components/t547/LICENSE).

HanziFrame distributes the component as source. Firmware binaries are not part
of this repository. Any future binary release needs a separate GPLv3
corresponding-source, reproducibility, dependency-notice and credential review.

## Fonts

### AR PL KaitiM GB, Version 2.11

- Copyright © 1994–1999 Arphic Technology Co., Ltd.
- License: Arphic Public License
- Files: `AR-PL-KaitiM-GB.ttf` and
  [`ARPHICPL.TXT`](pyscript/apps/chinese_display/fonts/ARPHICPL.TXT)

### Montserrat SemiBold, Version 9.000

- Copyright 2011 The Montserrat Project Authors
- Upstream named in the font: [JulietaUla/Montserrat](https://github.com/JulietaUla/Montserrat)
- License: SIL Open Font License 1.1
- Files: `Montserrat-SemiBold.ttf` and
  [`MONTSERRAT_LICENSE.txt`](pyscript/apps/chinese_display/fonts/MONTSERRAT_LICENSE.txt)

Both font binaries are redistributed unmodified. Documents and images rendered
with them do not inherit the font licenses.

## Project media and enclosure

The **HanziFrame device photo** (`assets/Display_Photo.png`) is © 2025
[`gkopiev`](https://github.com/gkopiev) and licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See the adjacent
[media notice](assets/LICENSE.md).

The **HanziFrame Home Assistant dashboard screenshot**
(`assets/Home_Assistant_Dashboard.png`) is a user-created capture of a locally
configured HanziFrame dashboard. Copyright in `gkopiev`'s original selection,
arrangement, local configuration and capture is © 2026 gkopiev and licensed
under CC BY 4.0; see the [media notice](assets/LICENSE.md).

The screenshot depicts
[Home Assistant Frontend](https://github.com/home-assistant/frontend), which
remains under the
[Apache License 2.0](assets/HOME_ASSISTANT_FRONTEND_LICENSE.md). The CC license
does not cover Home Assistant names, logos, trademarks, interface elements or
other third-party material shown. These are used only to identify the depicted
software; no affiliation or endorsement is implied.

The optional [Lilygo T5 4.7 Inch Case](https://www.printables.com/model/741304-lilygo-t5-47-inch-case)
is an external model by Vladimir Varzaru, licensed under CC BY 4.0 on its source
page. The model files are not included in this repository.

## Runtime dependencies installed separately

HanziFrame does not vendor these projects; users install them separately and
their upstream terms continue to apply:

- [Home Assistant Core](https://github.com/home-assistant/core) — Apache License 2.0;
- [Pyscript](https://github.com/custom-components/pyscript) — Apache License 2.0;
- [ESPHome](https://github.com/esphome/esphome) — ESPHome License (MIT for Python/non-runtime code and GPLv3 for C/C++ runtime code);
- [Pillow](https://github.com/python-pillow/Pillow) — MIT-CMU License.

Hardware and product names are used only to identify compatibility; their
respective trademarks remain with their owners.
