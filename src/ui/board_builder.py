"""
Board builder UI component for the Bingo application.
"""

from nicegui import ui

from src.config.constants import (
    BOARD_TILE_FONT,
    BOARD_TILE_FONT_STYLE,
    BOARD_TILE_FONT_WEIGHT,
    CARD_CLASSES,
    FREE_SPACE_TEXT,
    FREE_SPACE_TEXT_COLOR,
    GRID_CLASSES,
    GRID_CONTAINER_CLASS,
    LABEL_CLASSES,
    LABEL_SMALL_CLASSES,
    TILE_CLICKED_BG_COLOR,
    TILE_CLICKED_TEXT_COLOR,
    TILE_UNCLICKED_BG_COLOR,
    TILE_UNCLICKED_TEXT_COLOR,
)
from src.utils.text_processing import (
    split_phrase_into_lines,
    get_line_style_for_lines,
)


def build_board(parent, tile_buttons_dict: dict, on_tile_click, board, clicked_tiles):
    """
    Build the common Bingo board in the given parent element.
    The resulting tile UI elements are added to tile_buttons_dict.
    
    Args:
        parent: The parent UI element to build the board in
        tile_buttons_dict: Dictionary to store the created UI elements
        on_tile_click: Callback function when a tile is clicked
        board: 2D array of phrases
        clicked_tiles: Set of (row, col) tuples that are clicked
    """
    with parent:
        with ui.element("div").classes(GRID_CONTAINER_CLASS):
            with ui.grid(columns=5).classes(GRID_CLASSES):
                for row_idx, row in enumerate(board):
                    for col_idx, phrase in enumerate(row):
                        card = ui.card().classes(CARD_CLASSES).style("cursor: pointer;")
                        labels_list = []  # initialize list for storing label metadata
                        with card:
                            with ui.column().classes("flex flex-col items-center justify-center gap-0 w-full"):
                                default_text_color = FREE_SPACE_TEXT_COLOR if phrase.upper() == FREE_SPACE_TEXT else TILE_UNCLICKED_TEXT_COLOR
                                lines = split_phrase_into_lines(phrase)
                                line_count = len(lines)
                                for line in lines:
                                    with ui.row().classes("w-full items-center justify-center"):
                                        base_class = LABEL_SMALL_CLASSES if len(line) <= 3 else LABEL_CLASSES
                                        lbl = ui.label(line).classes(base_class).style(get_line_style_for_lines(line_count, default_text_color))
                                        labels_list.append({
                                            "ref": lbl,
                                            "base_classes": base_class,
                                            "base_style": get_line_style_for_lines(line_count, default_text_color)
                                        })
                        tile_buttons_dict[(row_idx, col_idx)] = {"card": card, "labels": labels_list}
                        
                        # Apply appropriate styling based on clicked state
                        if (row_idx, col_idx) in clicked_tiles:
                            card.style(f"background-color: {TILE_CLICKED_BG_COLOR}; color: {TILE_CLICKED_TEXT_COLOR}; border: none; outline: 3px solid {TILE_CLICKED_TEXT_COLOR};")
                        
                        # Don't allow clicking the free space 
                        if phrase.upper() == FREE_SPACE_TEXT:
                            card.style(f"color: {FREE_SPACE_TEXT_COLOR}; border: none; outline: 3px solid {TILE_CLICKED_TEXT_COLOR};")
                        else:
                            card.on("click", lambda e, r=row_idx, c=col_idx: on_tile_click(r, c))
    return tile_buttons_dict


def create_board_view(background_color: str, is_global: bool):
    """
    Creates a board page view based on the background color and a flag.
    If is_global is True, the board uses global variables (home page)
    otherwise it uses a local board (stream page).
    """
    import logging
    from src.core.game_logic import board, clicked_tiles, toggle_tile, board_views
    from src.ui.head import setup_head
    from src.utils.file_monitor import check_phrases_file_change
    
    # Set up common head elements
    setup_head(background_color)
    
    # Create the board container. For the home view, assign an ID to capture it.
    if is_global:
        container = ui.element("div").classes("home-board-container flex justify-center items-center w-full")
        try:
            ui.run_javascript("document.querySelector('.home-board-container').id = 'board-container'")
        except Exception as e:
            logging.debug(f"Setting board container ID failed: {e}")
    else:
        container = ui.element("div").classes("stream-board-container flex justify-center items-center w-full")
        try:
            ui.run_javascript("document.querySelector('.stream-board-container').id = 'board-container-stream'")
        except Exception as e:
            logging.debug(f"Setting stream container ID failed: {e}")
    
    if is_global:
        from src.core.game_logic import reset_board, generate_new_board
        from src.ui.controls import create_controls_row
        from src.utils.file_operations import read_phrases_file
        
        # Define the callback for phrases file changes
        def on_phrases_change(phrases):
            generate_new_board(phrases)
        
        # Build the home view with controls
        tile_buttons = {}  # Start with an empty dictionary.
        build_board(container, tile_buttons, toggle_tile, board, clicked_tiles)
        board_views["home"] = (container, tile_buttons)
        
        # Add timers for synchronizing the global board
        try:
            check_timer = ui.timer(1, lambda: check_phrases_file_change(on_phrases_change))
        except Exception as e:
            logging.warning(f"Error setting up timer: {e}")
        
        # Add control buttons (reset, new board, etc.)
        controls_row = create_controls_row()
        
    else:
        # Build the stream view (no controls)
        local_tile_buttons = {}
        build_board(container, local_tile_buttons, toggle_tile, board, clicked_tiles)
        board_views["stream"] = (container, local_tile_buttons)