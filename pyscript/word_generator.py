# `log`, `state`, `task`, `todo`, `@service` and `@pyscript_compile` are provided by Pyscript.
from builtins import open
from PIL import Image, ImageDraw, ImageFont, ImageOps
import csv
import io
import json
import os
import time

# --- PATH CONFIGURATION ---
BASE_APP_PATH = "/config/pyscript/apps/chinese_display"
CSV_FILE = f"{BASE_APP_PATH}/data/chinese_words.csv"
STATE_FILE = f"{BASE_APP_PATH}/chinese_word_state.json"
CHINESE_FONT_PATH = f"{BASE_APP_PATH}/fonts/AR-PL-KaitiM-GB.ttf"
OTHER_FONT_PATH = f"{BASE_APP_PATH}/fonts/Montserrat-SemiBold.ttf"
OUTPUT_PATH = "/config/www/word.png"
TODO_LIST_ENTITY = "todo.chinese_words"
CURRENT_WORD_SENSOR = "sensor.current_hanzi_word"
# -------------------------


@pyscript_compile
def _clean_text(value):
    """Returns a trimmed string while treating None as an empty value."""
    return str(value or "").strip()


@pyscript_compile
def _word_from_values(chinese, pinyin="", translation=""):
    """Normalizes one word and rejects entries without Chinese text."""
    word = {
        "chinese": _clean_text(chinese),
        "pinyin": _clean_text(pinyin),
        "translation": _clean_text(translation),
    }
    if not word["chinese"]:
        return None
    return word


@pyscript_compile
def _todo_summary(word):
    """Converts a word to the stable, human-readable local Todo format."""
    return f"{word['chinese']} | {word['pinyin']} | {word['translation']}"


@pyscript_compile
def _word_key(word):
    """Creates a case-insensitive key used to avoid duplicate Todo entries."""
    return "\x1f".join(
        [word["chinese"].casefold(), word["pinyin"].casefold(), word["translation"].casefold()]
    )


@pyscript_compile
def _parse_todo_summary(summary):
    """Parses `{chinese} | {pinyin} | {translation}` without breaking `|` in translation."""
    parts = _clean_text(summary).split(" | ", 2)
    chinese = parts[0] if parts else ""
    pinyin = parts[1] if len(parts) > 1 else ""
    translation = parts[2] if len(parts) > 2 else ""
    return _word_from_values(chinese, pinyin, translation)


@pyscript_compile
def load_chinese_words(csv_file):
    """Loads valid words from the UTF-8 CSV fallback file."""
    words = []
    try:
        with open(csv_file, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                word = _word_from_values(
                    row.get("chinese", ""),
                    row.get("pinyin", ""),
                    row.get("translation", ""),
                )
                if word:
                    words.append(word)
    except (FileNotFoundError, OSError, csv.Error, UnicodeError):
        return []
    return words


def _get_todo_items(status="needs_action"):
    """Returns Todo items for one status, or None when Todo is unavailable."""
    try:
        result = todo.get_items(
            entity_id=TODO_LIST_ENTITY,
            status=status,
            return_response=True,
        )
        entity_result = result.get(TODO_LIST_ENTITY, {}) if isinstance(result, dict) else {}
        items = entity_result.get("items", [])
        if not isinstance(items, list):
            log.warning(f"Unexpected Todo response for {TODO_LIST_ENTITY}: {result}")
            return None
        return items
    except Exception as exc:
        log.warning(f"Todo list {TODO_LIST_ENTITY} is unavailable: {exc}")
        return None


def load_chinese_words_from_todo():
    """Loads valid incomplete Todo entries; None means the Todo service was unavailable."""
    items = _get_todo_items(status="needs_action")
    if items is None:
        return None

    words = []
    for item in items:
        word = _parse_todo_summary(item.get("summary", ""))
        if word:
            words.append(word)
        else:
            log.warning(f"Skipped malformed Todo entry: {item.get('summary', '')}")
    return words


def load_all_chinese_words_from_todo():
    """Loads both active and completed Todo entries for duplicate detection."""
    active_items = _get_todo_items(status="needs_action")
    completed_items = _get_todo_items(status="completed")
    if active_items is None or completed_items is None:
        return None

    words = []
    for item in active_items + completed_items:
        word = _parse_todo_summary(item.get("summary", ""))
        if word:
            words.append(word)
    return words


@pyscript_compile
def _parse_csv_text(csv_text):
    """Parses CSV rows split by newlines or `;;`, keeping commas in translations."""
    if not _clean_text(csv_text):
        return []

    csv_text = str(csv_text).replace(";;", "\n")
    try:
        rows = [
            row
            for row in csv.reader(io.StringIO(csv_text))
            if any(_clean_text(cell) for cell in row)
        ]
    except csv.Error:
        return []

    if not rows:
        return []

    first_row = [_clean_text(cell).lstrip("\ufeff").casefold() for cell in rows[0]]
    has_header = first_row[:3] == ["chinese", "pinyin", "translation"]
    words = []
    for row in rows[1 if has_header else 0 :]:
        if len(row) < 1:
            continue
        chinese = row[0]
        pinyin = row[1] if len(row) > 1 else ""
        translation = ",".join(row[2:]) if len(row) > 2 else ""
        word = _word_from_values(chinese, pinyin, translation)
        if word:
            words.append(word)
        # Rows without Chinese text are ignored.
    return words


def _add_words_to_todo(words):
    """Adds new words to Todo and returns counts without creating duplicates."""
    current_words = load_all_chinese_words_from_todo()
    if current_words is None:
        log.error(f"Cannot add words: Todo list {TODO_LIST_ENTITY} is unavailable")
        return {"added": 0, "skipped": len(words), "error": "todo_unavailable"}

    known_keys = {_word_key(word) for word in current_words}
    added = 0
    skipped = 0
    for word in words:
        key = _word_key(word)
        if key in known_keys:
            skipped += 1
            continue
        try:
            todo.add_item(
                entity_id=TODO_LIST_ENTITY,
                item=_todo_summary(word),
                blocking=True,
            )
            known_keys.add(key)
            added += 1
        except Exception as exc:
            skipped += 1
            log.error(f"Could not add word '{word['chinese']}' to Todo: {exc}")

    return {"added": added, "skipped": skipped}


@pyscript_compile
def get_current_word_index(state_file, total_words):
    """Gets the current rotation index, then persists the next index."""
    if total_words <= 0:
        raise ValueError("total_words must be positive")

    try:
        with open(state_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            current_index = int(data.get("current_index", 0))
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        current_index = 0

    current_index %= total_words
    next_index = (current_index + 1) % total_words

    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as file:
            json.dump({"current_index": next_index}, file)
    except OSError:
        pass

    return current_index


@pyscript_compile
def get_adaptive_font_size(draw, text, font_path, base_size, max_width, min_size=30):
    """Calculates an optimal font size that fits within max_width."""
    current_size = base_size
    font = ImageFont.load_default()

    while current_size >= min_size:
        try:
            font = ImageFont.truetype(font_path, current_size)
        except IOError:
            break

        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return current_size, font
        current_size = int(current_size * 0.9)

    try:
        font = ImageFont.truetype(font_path, min_size)
    except IOError:
        font = ImageFont.load_default()
    return min_size, font


@pyscript_compile
def create_word_image(word_data, output_path, word_number=None, total_words=None):
    """Creates the fixed-size, inverted PNG used by the E-Ink display."""
    width, height = 960, 540
    white, black = (255, 255, 255), (0, 0, 0)
    light_gray, medium_gray = (245, 245, 245), (248, 248, 248)
    border_gray, text_gray = (204, 204, 204), (102, 102, 102)

    img = Image.new("RGB", (width, height), white)
    draw = ImageDraw.Draw(img)

    top_height = int(height * 0.7)
    bottom_height = height - top_height
    left_width = width // 2
    right_width = width - left_width
    chinese_margin = int(left_width * 0.1)
    pinyin_margin = int(right_width * 0.1)
    translation_margin = int(width * 0.05)
    chinese_max_width = left_width - chinese_margin * 2
    pinyin_max_width = right_width - pinyin_margin * 2
    translation_max_width = width - translation_margin * 2

    base_chinese_size, base_pinyin_size, base_translation_size = 210, 90, 90
    chinese_text = word_data.get("chinese", "?")
    pinyin_text = word_data.get("pinyin", "")
    translation_text = word_data.get("translation", "")

    if len(chinese_text) <= 2 and len(pinyin_text) <= 8:
        chinese_size = base_chinese_size
        pinyin_size = base_pinyin_size
        try:
            chinese_font = ImageFont.truetype(CHINESE_FONT_PATH, chinese_size)
        except IOError:
            chinese_font = ImageFont.load_default()
        try:
            pinyin_font = ImageFont.truetype(OTHER_FONT_PATH, pinyin_size)
        except IOError:
            pinyin_font = ImageFont.load_default()
    else:
        chinese_size, chinese_font = get_adaptive_font_size(
            draw, chinese_text, CHINESE_FONT_PATH, base_chinese_size, chinese_max_width
        )
        pinyin_size, pinyin_font = get_adaptive_font_size(
            draw, pinyin_text, OTHER_FONT_PATH, base_pinyin_size, pinyin_max_width
        )

    translation_size, translation_font = get_adaptive_font_size(
        draw,
        translation_text,
        OTHER_FONT_PATH,
        base_translation_size,
        translation_max_width,
        min_size=20,
    )
    try:
        counter_font = ImageFont.truetype(OTHER_FONT_PATH, 40)
    except IOError:
        counter_font = ImageFont.load_default()

    draw.rectangle([left_width, 0, width, top_height], fill=medium_gray)
    draw.rectangle([0, top_height, width, height], fill=light_gray)
    draw.line([0, top_height, width, top_height], fill=border_gray, width=3)
    draw.line([left_width, 0, left_width, top_height], fill=border_gray, width=3)

    if word_number is not None and total_words is not None:
        counter_text = f"{word_number}/{total_words}"
        counter_bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
        draw.text(
            (width - 15 - (counter_bbox[2] - counter_bbox[0]), 15),
            counter_text,
            fill=text_gray,
            font=counter_font,
        )

    chinese_bbox = draw.textbbox((0, 0), chinese_text, font=chinese_font)
    pinyin_bbox = draw.textbbox((0, 0), pinyin_text, font=pinyin_font)
    baseline_y = top_height // 2
    chinese_x = (left_width - (chinese_bbox[2] - chinese_bbox[0])) // 2
    chinese_y = baseline_y - (chinese_bbox[3] - chinese_bbox[1]) // 2 - chinese_bbox[1]
    pinyin_x = left_width + (right_width - (pinyin_bbox[2] - pinyin_bbox[0])) // 2
    pinyin_y = baseline_y - (pinyin_bbox[3] - pinyin_bbox[1]) // 2 - pinyin_bbox[1]
    draw.text((chinese_x, chinese_y), chinese_text, fill=black, font=chinese_font)
    draw.text((pinyin_x, pinyin_y), pinyin_text, fill=black, font=pinyin_font)

    translation_bbox = draw.textbbox((0, 0), translation_text, font=translation_font)
    translation_x = (width - (translation_bbox[2] - translation_bbox[0])) // 2
    translation_baseline_y = top_height + bottom_height // 2
    translation_y = translation_baseline_y - (translation_bbox[3] - translation_bbox[1]) // 2 - translation_bbox[1]
    draw.text((translation_x, translation_y), translation_text, fill=black, font=translation_font)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ImageOps.invert(img).save(output_path, "PNG")
    return output_path


def _publish_current_word(word, word_number=None, total_words=None, source="custom"):
    """Publishes status for the dashboard and a unique preview cache-busting version."""
    attributes = {
        "chinese": word["chinese"],
        "pinyin": word["pinyin"],
        "translation": word["translation"],
        "word_number": word_number,
        "total_words": total_words,
        "image_version": time.time_ns(),
        "source": source,
        "friendly_name": "Текущее китайское слово",
        "icon": "mdi:translate",
    }
    state.set(CURRENT_WORD_SENSOR, word["chinese"], new_attributes=attributes)


def _generate_word_image_impl(chinese=None, pinyin=None, translation=None):
    """Generates the next Todo/CSV word, or an explicitly supplied custom word."""
    is_custom_request = (
        chinese is not None or pinyin is not None or translation is not None
    )
    if is_custom_request:
        word = _word_from_values(chinese, pinyin, translation)
        if not word:
            log.error("Custom image generation requires a Chinese word")
            return {"generated": False, "reason": "missing_chinese"}
        task.executor(create_word_image, word, OUTPUT_PATH)
        _publish_current_word(word, source="custom")
        return {"generated": True, "source": "custom"}

    words = load_chinese_words_from_todo()
    if words is None:
        words = task.executor(load_chinese_words, CSV_FILE)
        source = "csv"
    elif not words:
        log.info(f"Todo list {TODO_LIST_ENTITY} has no active words; CSV fallback skipped")
        return {
            "generated": False,
            "reason": "no_active_todo_words",
            "source": "todo",
        }
    else:
        source = "todo"
    if not words:
        log.error("No words to display. Add Todo entries or check the CSV fallback.")
        return {"generated": False, "reason": "no_words"}

    total_words = len(words)
    current_index = task.executor(get_current_word_index, STATE_FILE, total_words)
    word = words[current_index]
    word_number = current_index + 1
    log.info(f"Generating {source} word {word_number}/{total_words}: {word['chinese']}")
    task.executor(
        create_word_image,
        word,
        OUTPUT_PATH,
        word_number=word_number,
        total_words=total_words,
    )
    _publish_current_word(word, word_number, total_words, source)
    return {
        "generated": True,
        "source": source,
        "word_number": word_number,
        "total_words": total_words,
    }


@service(supports_response="optional")
def generate_word_image(chinese=None, pinyin=None, translation=None):
    """Runs image generation and reports a structured failure instead of a service 500."""
    try:
        return _generate_word_image_impl(chinese, pinyin, translation)
    except Exception as exc:
        error = str(exc)
        log.error(f"Word generation failed before completion: {error}")
        return {
            "generated": False,
            "reason": "generation_failed",
            "error": error[:240],
        }


@service(supports_response="optional")
def add_chinese_word(chinese=None, pinyin=None, translation=None):
    """Adds one word to the Todo dictionary without creating a duplicate."""
    word = _word_from_values(chinese, pinyin, translation)
    if not word:
        log.error("Cannot add a word without Chinese text")
        return {"added": 0, "skipped": 1, "reason": "missing_chinese"}

    result = _add_words_to_todo([word])
    log.info(f"Todo add-word result: {result}")
    return result


@service(supports_response="optional")
def bulk_import_words(csv_text=None):
    """Imports CSV rows separated by newlines or `;;`; a header is optional."""
    words = _parse_csv_text(csv_text)
    if not words:
        log.warning("No valid words found in pasted CSV text")
        return {"added": 0, "skipped": 0, "reason": "no_valid_words"}

    result = _add_words_to_todo(words)
    log.info(f"Todo bulk-import result: {result}")
    return result


@service(supports_response="optional")
def import_words_from_csv():
    """Imports all valid CSV fallback words into Todo without creating duplicates."""
    words = task.executor(load_chinese_words, CSV_FILE)
    if not words:
        log.warning("No valid words found in the CSV fallback file")
        return {"added": 0, "skipped": 0, "reason": "no_valid_words"}

    result = _add_words_to_todo(words)
    log.info(f"Todo CSV-import result: {result}")
    return result
