"""
Configuration constants for the Bingo application.
"""

from typing import Final, Literal

# Type definitions for CSS properties
CssColor = str  # Hex color code like "#123456" or named color like "red"
CssFontFamily = str  # Font family names like "'Font Name', sans-serif"
CssFontWeight = str  # Font weight like "400", "700", etc.
CssFontStyle = Literal["normal", "italic", "oblique"]
CssClass = str  # CSS class name or space-separated class names

# Header text and display settings
HEADER_TEXT: Final[str] = "COMMIT !BINGO"
HEADER_TEXT_COLOR: Final[CssColor] = "#0CB2B3"
CLOSED_HEADER_TEXT: Final[str] = "Bingo Is Closed"
CLOSED_MESSAGE_TEXT: Final[str] = "GAME CLOSED"
CLOSED_MESSAGE_COLOR: Final[CssColor] = "#FF7f33"

# Free space settings
FREE_SPACE_TEXT: Final[str] = "FREE MEAT"
FREE_SPACE_TEXT_COLOR: Final[CssColor] = "#1BEFF5"

# Tile appearance settings
TILE_CLICKED_BG_COLOR: Final[CssColor] = "#100079"
TILE_CLICKED_TEXT_COLOR: Final[CssColor] = "#1BEFF5"
TILE_UNCLICKED_BG_COLOR: Final[CssColor] = "#1BEFF5"
TILE_UNCLICKED_TEXT_COLOR: Final[CssColor] = "#100079"

# Page backgrounds
HOME_BG_COLOR: Final[CssColor] = "#100079"
STREAM_BG_COLOR: Final[CssColor] = "#00FF00"

# Font settings
HEADER_FONT_FAMILY: Final[CssFontFamily] = "'Super Carnival', sans-serif"
BOARD_TILE_FONT: Final[str] = "Inter"
BOARD_TILE_FONT_WEIGHT: Final[CssFontWeight] = "700"
BOARD_TILE_FONT_STYLE: Final[CssFontStyle] = "normal"

# UI Class Constants
BOARD_CONTAINER_CLASS: Final[CssClass] = "flex justify-center items-center w-full"
HEADER_CONTAINER_CLASS: Final[CssClass] = "w-full"
CARD_CLASSES: Final[CssClass] = (
    "relative p-2 rounded-xl shadow-8 w-full h-full flex items-center justify-center"
)
COLUMN_CLASSES: Final[CssClass] = (
    "flex flex-col items-center justify-center gap-0 w-full"
)
GRID_CONTAINER_CLASS: Final[CssClass] = "w-full aspect-square p-4"
GRID_CLASSES: Final[CssClass] = "gap-2 h-full grid-rows-5"
ROW_CLASSES: Final[CssClass] = "w-full"
LABEL_SMALL_CLASSES: Final[CssClass] = "fit-text-small text-center select-none"
LABEL_CLASSES: Final[CssClass] = "fit-text text-center select-none"
