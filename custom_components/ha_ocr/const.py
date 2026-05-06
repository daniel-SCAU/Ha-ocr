"""Constants for the Ha OCR integration."""

DOMAIN = "ha_ocr"
PLATFORMS = ["sensor", "button"]

# Configuration keys
CONF_DEVICE = "device"
CONF_ROI_X = "roi_x"
CONF_ROI_Y = "roi_y"
CONF_ROI_WIDTH = "roi_width"
CONF_ROI_HEIGHT = "roi_height"
CONF_EXPECTED_TEXTS = "expected_texts"
CONF_OCR_LANG = "ocr_lang"

# Defaults
DEFAULT_DEVICE = "/dev/video0"
DEFAULT_ROI_X = 0
DEFAULT_ROI_Y = 0
DEFAULT_ROI_WIDTH = 0   # 0 means use full frame width
DEFAULT_ROI_HEIGHT = 0  # 0 means use full frame height
DEFAULT_OCR_LANG = "eng"
DEFAULT_EXPECTED_TEXTS = ""

# Entity attribute names
ATTR_OCR_TEXT = "ocr_text"
ATTR_MATCH = "match"
ATTR_MATCHED_TEXTS = "matched_texts"

# Service names
SERVICE_CAPTURE = "capture"
