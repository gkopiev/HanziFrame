import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import display
from esphome.core import CORE
from esphome.const import (
    CONF_ID,
    CONF_LAMBDA,
    CONF_PAGES,
)
from esphome.const import __version__ as ESPHOME_VERSION

DEPENDENCIES = ["esp32"]

CONF_GREYSCALE = "greyscale"


t547_ns = cg.esphome_ns.namespace("t547")
T547 = t547_ns.class_(
    "T547", cg.PollingComponent, display.DisplayBuffer
)

CONFIG_SCHEMA = cv.All(
    display.FULL_DISPLAY_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(T547),
            cv.Optional(CONF_GREYSCALE, default=False): cv.boolean,
        }
    )
    .extend(cv.polling_component_schema("5s")),
    cv.has_at_most_one_key(CONF_PAGES, CONF_LAMBDA),
    cv.only_with_arduino,
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])

    # ESPHome 2026.2+ disables unused Arduino libraries by default. Keep these
    # declarations here so the vendored component is self-contained and does
    # not depend on matching `esphome.libraries` entries in user YAML.
    if CORE.is_esp32 and CORE.using_arduino:
        cg.add_library("SPI", None)
        cg.add_library("Wire", None)

    # The C sources use the ESP-IDF RMT driver and the legacy driver shim
    # directly. ESPHome 2026.2+ excludes these built-in components unless a
    # consumer enables them. The helper does not exist on older ESPHome
    # versions, where all IDF components were included automatically.
    try:
        from esphome.components.esp32 import include_builtin_idf_component

        include_builtin_idf_component("esp_driver_rmt")
        include_builtin_idf_component("driver")
    except ImportError:
        pass

    if cv.Version.parse(ESPHOME_VERSION) < cv.Version.parse("2023.12.0"):
        await cg.register_component(var, config)
    await display.register_display(var, config)

    if CONF_LAMBDA in config:
        lambda_ = await cg.process_lambda(
            config[CONF_LAMBDA], [(display.DisplayRef, "it")], return_type=cg.void
        )
        cg.add(var.set_writer(lambda_))

    cg.add(var.set_greyscale(config[CONF_GREYSCALE]))

    cg.add_build_flag("-DBOARD_HAS_PSRAM")
