"""Isolated lifecycle regression tests using real HA and Pyscript classes.

Verified with HA Core 2026.10.1 and Pyscript 2.0.1 (baseline) / 2.1.0.
Run in a Python environment where HA and custom_components.pyscript are importable:
    python -m unittest discover -s tests -v

No connection to a running HA is made. All states/events belong to a fresh,
local HomeAssistant object with a temporary configuration directory.
"""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
    EVENT_SERVICE_REMOVED,
)
import yaml

from homeassistant.core import Context, CoreState, HomeAssistant, callback
from homeassistant.helpers.script import Script
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.helpers import config_validation as cv
from homeassistant.components.homeassistant.triggers.state import (
    async_attach_trigger,
    async_validate_trigger_config,
)

from custom_components.pyscript import DecoratorRegistry
from custom_components.pyscript.const import CONFIG_ENTRY, DOMAIN
from custom_components.pyscript.eval import AstEval
from custom_components.pyscript.function import Function
from custom_components.pyscript.global_ctx import GlobalContext, GlobalContextMgr
from custom_components.pyscript.state import State
from custom_components.pyscript.trigger import TrigTime


SOURCE = Path(__file__).resolve().parents[1] / "pyscript/hanziframe_lifecycle.py"
ENTITY = "binary_sensor.hanziframe_ready"


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.directory.name)
        self.hass.data[DOMAIN] = {
            CONFIG_ENTRY: SimpleNamespace(
                data={"allow_all_imports": True, "hass_is_global": True}
            )
        }
        Function.init(self.hass)
        State.init(self.hass)
        State.register_functions()
        TrigTime.init(self.hass)
        GlobalContextMgr.init()
        DecoratorRegistry.init(self.hass)
        self.contexts = []
        self.removes = []

    async def asyncTearDown(self):
        for context in self.contexts:
            context.stop()
        await Function.waiter_sync()
        for remove in self.removes:
            remove()
        # Tests with explicit close() or replacement must also tolerate cleanup.
        close = self.hass.data.get("hanziframe_readiness", {}).get("close")
        if close:
            close()
        await Function.waiter_stop()
        await Function.reaper_stop()
        await self.hass.async_block_till_done()
        self.directory.cleanup()

    async def load(
        self, *, auto_start=True, name="file.hanziframe_lifecycle", source=None, symbols=None
    ):
        context = GlobalContext(name, global_sym_table=symbols or {}, manager=GlobalContextMgr)
        context.set_auto_start(auto_start)
        self.contexts.append(context)
        evaluator = AstEval(context.get_name(), global_ctx=context)
        Function.install_ast_funcs(evaluator)
        evaluator.parse(SOURCE.read_text(encoding="utf-8") if source is None else source)
        await evaluator.eval()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        return context

    def ready(self):
        return self.hass.states.get(ENTITY).state

    def register(self):
        self.hass.services.async_register("pyscript", "generate_word_image", lambda call: None)

    async def test_registration_removal_and_unrelated_events(self):
        await self.load()
        self.assertEqual(self.ready(), "off")
        self.hass.services.async_register("other", "generate_word_image", lambda call: None)
        self.assertEqual(self.ready(), "off")
        self.register()
        self.assertEqual(self.ready(), "on")
        self.hass.bus.async_fire(
            EVENT_SERVICE_REMOVED, {"domain": "pyscript", "service": "other"}
        )
        self.assertEqual(self.ready(), "on")
        self.hass.services.async_remove("pyscript", "generate_word_image")
        self.assertEqual(self.ready(), "off")
        self.register()
        self.assertEqual(self.ready(), "on")

    async def test_service_present_before_watcher_load(self):
        self.register()
        await self.load()
        self.assertEqual(self.ready(), "on")

    async def test_stop_before_service_removal(self):
        self.register()
        await self.load()
        self.hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        self.assertTrue(self.hass.services.has_service("pyscript", "generate_word_image"))
        self.assertEqual(self.ready(), "off")
        self.hass.set_state(CoreState.stopping)
        self.hass.services.async_remove("pyscript", "generate_word_image")
        self.register()
        self.assertEqual(self.ready(), "off")

    async def test_load_while_stopping(self):
        self.register()
        self.hass.set_state(CoreState.stopping)
        await self.load()
        self.assertEqual(self.ready(), "off")

    async def test_reload_and_delayed_old_cleanup(self):
        self.register()
        old = await self.load()
        old_close = self.hass.data["hanziframe_readiness"]["close"]
        await self.load()
        old.stop()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        old_close()
        self.assertEqual(self.ready(), "on")
        self.hass.services.async_remove("pyscript", "generate_word_image")
        self.assertEqual(self.ready(), "off")
        self.register()
        self.assertEqual(self.ready(), "on")

    async def test_unload_removes_listeners(self):
        self.register()
        context = await self.load()
        context.stop()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        self.assertEqual(self.ready(), "off")
        self.assertNotIn("close", self.hass.data["hanziframe_readiness"])
        self.hass.services.async_remove("pyscript", "generate_word_image")
        self.register()
        self.assertEqual(self.ready(), "off")
        # A leaked STOP listener would overwrite this sentinel state.
        self.hass.states.async_set(ENTITY, "unavailable")
        self.hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        self.assertEqual(self.ready(), "unavailable")

    async def test_refresh_actions_fail_closed_and_preserve_call_order(self):
        # Run the actual public actions, as a manual automation.trigger does
        # after bypassing the automation's outer conditions.
        config = yaml.safe_load(
            (SOURCE.parents[1] / "homeassistant/automation.yaml").read_text(encoding="utf-8")
        )[0]
        calls = []

        @callback
        def generate(call):
            calls.append("generate")

        @callback
        def press(call):
            calls.append("button")

        self.hass.services.async_register("pyscript", "generate_word_image", generate)
        self.hass.services.async_register("button", "press", press)
        async_set_service_schema(self.hass, "button", "press", {"fields": {}})
        script = Script(
            self.hass, cv.SCRIPT_SCHEMA(config["actions"]), "HanziFrame refresh", "automation"
        )
        # An unknown sensor, off, and unavailable must all stop before generation
        # AND before button.press, which would otherwise display a stale image.
        for state in ("unknown", "off", "unavailable"):
            self.hass.states.async_set(ENTITY, state)
            await script.async_run(context=Context())
            self.assertEqual(calls, [])
        self.hass.states.async_set(ENTITY, "on")
        await script.async_run(context=Context())
        self.assertEqual(calls, ["generate", "button"])

    async def test_unload_before_start_installs_no_listeners(self):
        listeners = self.hass.bus.async_listeners()
        context = await self.load(auto_start=False)
        self.assertIsNone(self.hass.states.get(ENTITY))
        self.assertEqual(self.hass.bus.async_listeners(), listeners)
        context.stop()
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.bus.async_listeners(), listeners)
        self.assertNotIn("close", self.hass.data.get("hanziframe_readiness", {}))
        self.register()
        self.hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        self.assertIsNone(self.hass.states.get(ENTITY))

    async def test_unload_with_startup_queued_does_not_reopen_listeners(self):
        listeners = self.hass.bus.async_listeners()
        context = await self.load(auto_start=False)
        context.set_auto_start(True)
        context.start()
        context.stop()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.bus.async_listeners(), listeners)
        self.assertNotIn("close", self.hass.data.get("hanziframe_readiness", {}))
        self.register()
        readiness = self.hass.states.get(ENTITY)
        self.assertTrue(readiness is None or readiness.state == "off")

    async def attach_refresh(self, calls):
        config = yaml.safe_load(
            (SOURCE.parents[1] / "homeassistant/automation.yaml").read_text(encoding="utf-8")
        )[0]

        @callback
        def press(call):
            calls.append("button")

        self.hass.services.async_register("button", "press", press)
        async_set_service_schema(self.hass, "button", "press", {"fields": {}})
        script = Script(
            self.hass, cv.SCRIPT_SCHEMA(config["actions"]), "HanziFrame refresh", "automation"
        )

        async def action(variables, context):
            await script.async_run(context=context)

        trigger_config = await async_validate_trigger_config(
            self.hass, cv.TRIGGER_SCHEMA(config["triggers"])[1]
        )
        self.removes.append(
            await async_attach_trigger(
                self.hass, trigger_config, action, {"trigger_data": {}, "variables": {}}
            )
        )

    async def load_pair(self, calls):
        # Real Pyscript service decorators remain dormant until context.start(),
        # just as they do during HA's cold load and integration reload.
        watcher = await self.load(auto_start=False)
        renderer = await self.load(
            auto_start=False,
            name="file.word_generator",
            source="@service\ndef generate_word_image():\n    calls.append('generate')\n",
            symbols={"calls": calls},
        )
        return watcher, renderer

    async def start_pair(self, contexts, renderer_first):
        order = reversed(contexts) if renderer_first else contexts
        for context in order:
            context.set_auto_start(True)
            context.start()
        await self.hass.async_block_till_done()

    async def check_cold_start_and_full_reload(self, renderer_first):
        calls = []
        await self.attach_refresh(calls)
        contexts = await self.load_pair(calls)
        self.assertIsNone(self.hass.states.get(ENTITY))
        await self.start_pair(contexts, renderer_first)
        self.assertEqual(self.ready(), "on")
        self.assertEqual(calls, ["generate", "button"])

        for context in contexts:
            context.stop()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        self.assertEqual(self.ready(), "off")
        self.assertNotIn("close", self.hass.data["hanziframe_readiness"])
        self.assertFalse(self.hass.services.has_service("pyscript", "generate_word_image"))
        contexts = await self.load_pair(calls)
        await self.start_pair(contexts, renderer_first)
        self.assertEqual(self.ready(), "on")
        self.assertEqual(calls, ["generate", "button", "generate", "button"])

    async def test_cold_start_and_full_reload_watcher_first(self):
        await self.check_cold_start_and_full_reload(renderer_first=False)

    async def test_cold_start_and_full_reload_renderer_first(self):
        await self.check_cold_start_and_full_reload(renderer_first=True)

    async def test_lifecycle_only_reload_refreshes_once(self):
        calls = []
        await self.attach_refresh(calls)
        watcher, renderer = await self.load_pair(calls)
        await self.start_pair((watcher, renderer), renderer_first=False)
        watcher.stop()
        await Function.waiter_sync()
        await self.hass.async_block_till_done()
        self.assertEqual(self.ready(), "off")
        await self.load()
        self.assertEqual(self.ready(), "on")
        self.assertEqual(calls, ["generate", "button", "generate", "button"])


if __name__ == "__main__":
    unittest.main()
