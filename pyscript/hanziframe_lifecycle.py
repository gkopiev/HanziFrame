"""Gate scheduled refreshes while the renderer is unavailable or HA is stopping.

Requires Pyscript's allow_all_imports and hass_is_global options. The watcher is
native Python so HA event callbacks publish state without an interpreter task.
"""


@pyscript_compile
def _watch_hanziframe_readiness(hass):
    from homeassistant.const import (
        EVENT_HOMEASSISTANT_STOP,
        EVENT_SERVICE_REGISTERED,
        EVENT_SERVICE_REMOVED,
    )
    from homeassistant.core import callback

    entity_id = "binary_sensor.hanziframe_ready"
    attributes = {"friendly_name": "Готовность HanziFrame", "icon": "mdi:translate"}
    # Replace a previous instance without leaving duplicate listeners on reload.
    owner = hass.data.setdefault("hanziframe_readiness", {})
    previous = owner.get("close")
    if previous is not None:
        previous()

    @callback
    def publish(event=None):
        if event is not None and event.event_type != EVENT_HOMEASSISTANT_STOP:
            if (
                event.data.get("domain") != "pyscript"
                or event.data.get("service") != "generate_word_image"
            ):
                return
        ready = (
            (event is None or event.event_type != EVENT_HOMEASSISTANT_STOP)
            and not hass.is_stopping
            and hass.services.has_service("pyscript", "generate_word_image")
        )
        hass.states.async_set(entity_id, "on" if ready else "off", attributes)

    unsubscribe = [
        hass.bus.async_listen(event_type, publish)
        for event_type in (
            EVENT_HOMEASSISTANT_STOP,
            EVENT_SERVICE_REGISTERED,
            EVENT_SERVICE_REMOVED,
        )
    ]
    publish()

    @callback
    def close():
        for remove_listener in unsubscribe:
            remove_listener()
        unsubscribe.clear()
        # A delayed shutdown callback from the old instance must not own state.
        if owner.get("close") is close:
            owner.pop("close")
            hass.states.async_set(entity_id, "off", attributes)

    owner["close"] = close
    return close


# Install only once the shutdown hook is active. A context can be unloaded
# before startup, when Pyscript does not call its shutdown decorators.
_close_readiness = None
_readiness_stopped = False


@time_trigger("startup", "shutdown")
def hanziframe_readiness_lifecycle(trigger_time=None):
    global _close_readiness, _readiness_stopped
    if trigger_time == "shutdown":
        # A startup action already queued before unload must not reopen listeners.
        _readiness_stopped = True
        if _close_readiness is not None:
            _close_readiness()
    elif not _readiness_stopped:
        _close_readiness = _watch_hanziframe_readiness(hass)
