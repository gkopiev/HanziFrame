# Import necessary libraries from pyscript
# log will be available automatically
from builtins import open
from PIL import Image, ImageDraw, ImageFont
import csv
import os
import json

# --- PATH CONFIGURATION ---
BASE_APP_PATH = "/config/pyscript/apps/chinese_display"
CSV_FILE = f"{BASE_APP_PATH}/data/chinese_words.csv"
STATE_FILE = f"{BASE_APP_PATH}/chinese_word_state.json"
CHINESE_FONT_PATH = f"{BASE_APP_PATH}/fonts/AR-PL-KaitiM-GB.ttf"
OTHER_FONT_PATH = f"{BASE_APP_PATH}/fonts/Montserrat-SemiBold.ttf"
OUTPUT_PATH = "/config/www/word.png"
# -------------------------

def load_chinese_words(csv_file):
    """Loads words from CSV file"""
    words = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                words.append({
                    'chinese': row.get('chinese', ''),
                    'pinyin': row.get('pinyin', ''),
                    'translation': row.get('translation', '')
                })
    except FileNotFoundError:
        log.error(f"Words file not found: {csv_file}")
        return []
    return words

def get_current_word_index(state_file, total_words):
    """Gets current word index and increments it"""
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
            current_index = data.get('current_index', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        current_index = 0
    
    next_index = (current_index + 1) % total_words
    
    try:
        # Make sure the directory for the state file exists
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({'current_index': next_index}, f)
    except Exception as e:
        log.error(f"Error saving state: {e}")
    
    return current_index

def get_adaptive_font_size(draw, text, font_path, base_size, max_width, min_size=30):
    """Calculates optimal font size for given width"""
    current_size = base_size
    font = ImageFont.load_default() # Default font in case of error
    
    while current_size >= min_size:
        try:
            font = ImageFont.truetype(font_path, current_size)
        except IOError:
            log.warning(f"Could not load font {font_path}. Using default font.")
            break # Exit loop if font not found
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            return current_size, font
        
        current_size = int(current_size * 0.9)
    
    try:
        font = ImageFont.truetype(font_path, min_size)
    except IOError:
        font = ImageFont.load_default()
        
    return min_size, font

def create_word_image(word_data, output_path, word_number=None, total_words=None):
    """
    Creates an image with Chinese word.
    Counter 'word_number/total_words' is optional.
    """
    WIDTH, HEIGHT = 960, 540
    WHITE, BLACK, LIGHT_GRAY, MEDIUM_GRAY, BORDER_GRAY, TEXT_GRAY = (255, 255, 255), (0, 0, 0), (245, 245, 245), (248, 248, 248), (204, 204, 204), (102, 102, 102)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)
    
    top_height = int(HEIGHT * 0.7)
    bottom_height = HEIGHT - top_height
    left_width = WIDTH // 2
    right_width = WIDTH - left_width
    
    chinese_margin = int(left_width * 0.1)
    pinyin_margin = int(right_width * 0.1)
    # Add margins for translation text
    translation_margin = int(WIDTH * 0.05)  # 5% margin on each side
    
    chinese_max_width = left_width - (chinese_margin * 2)
    pinyin_max_width = right_width - (pinyin_margin * 2)
    translation_max_width = WIDTH - (translation_margin * 2)  # Maximum width for translation text
    
    base_chinese_size, base_pinyin_size, base_translation_size = 210, 90, 90
    
    chinese_text = word_data.get('chinese', '?')
    pinyin_text = word_data.get('pinyin', '')
    translation_text = word_data.get('translation', '')
    
    # Adaptive sizes for Chinese and pinyin (as before)
    if len(chinese_text) <= 2:
        chinese_size = base_chinese_size
        try:
            chinese_font = ImageFont.truetype(CHINESE_FONT_PATH, chinese_size)
        except IOError:
            chinese_font = ImageFont.load_default()
        
        pinyin_size = base_pinyin_size
        try:
            pinyin_font = ImageFont.truetype(OTHER_FONT_PATH, pinyin_size)
        except IOError:
            pinyin_font = ImageFont.load_default()
    else:
        chinese_size, chinese_font = get_adaptive_font_size(draw, chinese_text, CHINESE_FONT_PATH, base_chinese_size, chinese_max_width)
        pinyin_size_ratio = chinese_size / base_chinese_size
        adaptive_pinyin_size = int(base_pinyin_size * pinyin_size_ratio)
        pinyin_size, pinyin_font = get_adaptive_font_size(draw, pinyin_text, OTHER_FONT_PATH, adaptive_pinyin_size, pinyin_max_width)
    
    # Adaptive size for translation text
    translation_size, translation_font = get_adaptive_font_size(draw, translation_text, OTHER_FONT_PATH, base_translation_size, translation_max_width, min_size=20)
    
    try:
        counter_font = ImageFont.truetype(OTHER_FONT_PATH, 40)
    except IOError:
        counter_font = ImageFont.load_default()

    log.info(f"Word: {chinese_text} ({len(chinese_text)} characters). Font sizes - Chinese: {chinese_size}px, Pinyin: {pinyin_size}px, Translation: {translation_size}px")

    # --- Drawing ---
    draw.rectangle([left_width, 0, WIDTH, top_height], fill=MEDIUM_GRAY)
    draw.rectangle([0, top_height, WIDTH, HEIGHT], fill=LIGHT_GRAY)
    draw.line([0, top_height, WIDTH, top_height], fill=BORDER_GRAY, width=3)
    draw.line([left_width, 0, left_width, top_height], fill=BORDER_GRAY, width=3)
    
    # Draw counter only if corresponding data is provided
    if word_number is not None and total_words is not None:
        counter_text = f"{word_number}/{total_words}"
        counter_bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
        draw.text((WIDTH - 15 - (counter_bbox[2] - counter_bbox[0]), 15), counter_text, fill=TEXT_GRAY, font=counter_font)
    
    chinese_bbox = draw.textbbox((0, 0), chinese_text, font=chinese_font)
    pinyin_bbox = draw.textbbox((0, 0), pinyin_text, font=pinyin_font)
    
    baseline_y = top_height // 2
    
    chinese_x = (left_width - (chinese_bbox[2] - chinese_bbox[0])) // 2
    chinese_y = baseline_y - (chinese_bbox[3] - chinese_bbox[1]) // 2 - chinese_bbox[1]
    draw.text((chinese_x, chinese_y), chinese_text, fill=BLACK, font=chinese_font)
    
    pinyin_x = left_width + (right_width - (pinyin_bbox[2] - pinyin_bbox[0])) // 2
    pinyin_y = baseline_y - (pinyin_bbox[3] - pinyin_bbox[1]) // 2 - pinyin_bbox[1]
    draw.text((pinyin_x, pinyin_y), pinyin_text, fill=BLACK, font=pinyin_font)
    
    # Draw translation text with adaptive font
    translation_bbox = draw.textbbox((0, 0), translation_text, font=translation_font)
    translation_x = (WIDTH - (translation_bbox[2] - translation_bbox[0])) // 2
    translation_baseline_y = top_height + bottom_height // 2
    translation_y = translation_baseline_y - (translation_bbox[3] - translation_bbox[1]) // 2 - translation_bbox[1]
    draw.text((translation_x, translation_y), translation_text, fill=BLACK, font=translation_font)
    
    # Make sure /config/www directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Invert image
    from PIL import ImageOps
    img_inverted = ImageOps.invert(img)
    
    # Save inverted image
    img_inverted.save(output_path, 'PNG')
    log.info(f"Inverted image saved: {output_path}")

# This function will be available as a service in Home Assistant
# Service name will be: pyscript.generate_word_image
@service
def generate_word_image(chinese=None, pinyin=None, translation=None):
    """
    Main function called by automation.
    If parameters (chinese, pinyin, translation) are provided, generates image for them.
    Otherwise, takes next word from CSV file.
    """
    # MODE 1: Generate specific word (e.g., for night mode)
    if chinese and pinyin and translation:
        log.info(f"Generating image for specified word: {chinese}")
        word_data = {
            'chinese': chinese,
            'pinyin': pinyin,
            'translation': translation
        }
        # Call create_word_image without counter
        create_word_image(word_data, OUTPUT_PATH)
    
    # MODE 2: Standard operation by list
    else:
        log.info("Generating next word from list.")
        words = load_chinese_words(CSV_FILE)
        
        if not words:
            log.error("No words to display. Check CSV file.")
            return
        
        total_words = len(words)
        current_index = get_current_word_index(STATE_FILE, total_words)
        word = words[current_index]
        word_number = current_index + 1
        
        log.info(f"Generating image for word {word_number}/{total_words}: {word['chinese']}")
        # Call create_word_image with counter
        create_word_image(word, OUTPUT_PATH, word_number=word_number, total_words=total_words)
