"""
Core game logic for the Bingo application.
"""

import datetime
import logging
import random
import json
from typing import List, Optional, Set, Dict, Any, Tuple, cast

from nicegui import ui, app

from src.config.constants import (
    CLOSED_HEADER_TEXT,
    FREE_SPACE_TEXT,
    FREE_SPACE_TEXT_COLOR,
    HEADER_TEXT,
    TILE_CLICKED_BG_COLOR,
    TILE_CLICKED_TEXT_COLOR,
    TILE_UNCLICKED_BG_COLOR,
    TILE_UNCLICKED_TEXT_COLOR,
)
from src.types.ui_types import (
    BingoPattern,
    BingoPatterns,
    BoardType,
    BoardViews,
    ClickedTiles,
    Coordinate,
    TileButtonsDict,
    TileLabelInfo,
)
from src.utils.text_processing import get_line_style_for_lines, split_phrase_into_lines

# Global variables for game state
board: BoardType = []  # 2D array of phrases
clicked_tiles: ClickedTiles = set()  # Set of (row, col) tuples that are clicked
bingo_patterns: BingoPatterns = set()  # Set of winning patterns found
board_iteration: int = 1
is_game_closed: bool = False
today_seed: Optional[str] = None

# Global variables for UI references (initialized in the UI module)
header_label: Optional[ui.label] = None
controls_row: Optional[ui.row] = None
seed_label: Optional[ui.label] = None
board_views: BoardViews = (
    {}
)  # Dictionary mapping view name to (container, tile_buttons) tuple


def generate_board(seed_val: int, phrases: List[str]) -> BoardType:
    """
    Generate a new board using the provided seed value.
    Also resets the clicked_tiles (ensuring the FREE SPACE is clicked) and sets the global today_seed.

    Args:
        seed_val: Integer used to seed the random generator
        phrases: List of phrases to use in the board

    Returns:
        The generated board as a 2D array of phrases
    """
    global board, today_seed, clicked_tiles

    # Always use a new seed value based on current time and the provided seed value for more randomness
    current_date = datetime.date.today()
    todays_seed_prefix = current_date.strftime("%Y%m%d")
    
    # Create a more unique seed value that combines date and time
    current_time_ms = int((datetime.datetime.now().timestamp() % 1) * 1000)  # milliseconds part of current time
    final_seed = seed_val * 1000 + current_time_ms  # combine with provided seed value
    
    random.seed(final_seed)  # Set the random seed

    shuffled_phrases = random.sample(phrases, 24)
    shuffled_phrases.insert(12, FREE_SPACE_TEXT)

    board = [shuffled_phrases[i : i + 5] for i in range(0, 25, 5)]

    clicked_tiles.clear()
    for r, row in enumerate(board):
        for c, phrase in enumerate(row):
            if phrase.upper() == FREE_SPACE_TEXT:
                clicked_tiles.add((r, c))

    # Format the seed string for display using the provided seed value (board iteration)
    today_seed = f"{todays_seed_prefix}.{seed_val}"

    # Update the seed label if available
    if seed_label is not None:
        seed_label.set_text(f"Seed: {today_seed}")
        seed_label.update()

    return board


def toggle_tile(row: int, col: int) -> None:
    """
    Toggle the state of a tile (clicked/unclicked).
    Updates the UI and checks for winner.

    Args:
        row: Row index of the tile to toggle
        col: Column index of the tile to toggle
    """
    global clicked_tiles

    # Don't allow toggling the free space
    if (row, col) == (2, 2):
        return

    key: Coordinate = (row, col)
    if key in clicked_tiles:
        clicked_tiles.remove(key)
    else:
        clicked_tiles.add(key)

    check_winner()
    
    # Save state to storage after each tile toggle for persistence
    save_state_to_storage()

    for view_key, (container, tile_buttons_local) in board_views.items():
        for (r, c), tile in tile_buttons_local.items():
            phrase = board[r][c]
            if (r, c) in clicked_tiles:
                new_card_style = f"background-color: {TILE_CLICKED_BG_COLOR}; color: {TILE_CLICKED_TEXT_COLOR}; border: none; outline: 3px solid {TILE_CLICKED_TEXT_COLOR};"
                new_label_color = TILE_CLICKED_TEXT_COLOR
            else:
                new_card_style = f"background-color: {TILE_UNCLICKED_BG_COLOR}; color: {TILE_UNCLICKED_TEXT_COLOR}; border: none;"
                new_label_color = TILE_UNCLICKED_TEXT_COLOR

            card = cast(ui.card, tile["card"])
            card.style(new_card_style)

            lines = split_phrase_into_lines(phrase)
            line_count = len(lines)
            new_label_style = get_line_style_for_lines(line_count, new_label_color)

            label_list = cast(List[TileLabelInfo], tile["labels"])
            for label_info in label_list:
                lbl = cast(ui.label, label_info["ref"])
                base_classes = cast(str, label_info["base_classes"])
                lbl.classes(base_classes)
                lbl.style(new_label_style)
                lbl.update()

            card.update()

        container.update()

    try:
        js_code = """
            setTimeout(function() {
                if (typeof fitty !== 'undefined') {
                    fitty('.fit-text', { multiLine: true, minSize: 10, maxSize: 1000 });
                    fitty('.fit-text-small', { multiLine: true, minSize: 10, maxSize: 72 });
                }
            }, 50);
        """
        ui.run_javascript(js_code)
        
        # In NiceGUI 2.11+, updates are automatically synchronized between clients
        # via the timer-based sync_board_state function running frequently
        logging.debug("UI updates will be synchronized by timers")
    except Exception as e:
        logging.debug(f"JavaScript execution failed: {e}")


def check_winner() -> None:
    """
    Check for Bingo win condition and update the UI accordingly.
    """
    global bingo_patterns
    new_patterns: List[BingoPattern] = []

    # Check rows and columns.
    for i in range(5):
        if all((i, j) in clicked_tiles for j in range(5)):
            if f"row{i}" not in bingo_patterns:
                new_patterns.append(f"row{i}")
        if all((j, i) in clicked_tiles for j in range(5)):
            if f"col{i}" not in bingo_patterns:
                new_patterns.append(f"col{i}")

    # Check main diagonal.
    if all((i, i) in clicked_tiles for i in range(5)):
        if "diag_main" not in bingo_patterns:
            new_patterns.append("diag_main")

    # Check anti-diagonal.
    if all((i, 4 - i) in clicked_tiles for i in range(5)):
        if "diag_anti" not in bingo_patterns:
            new_patterns.append("diag_anti")

    # Additional winning variations:

    # Blackout: every cell is clicked.
    if all((r, c) in clicked_tiles for r in range(5) for c in range(5)):
        if "blackout" not in bingo_patterns:
            new_patterns.append("blackout")

    # 4 Corners: top-left, top-right, bottom-left, bottom-right.
    if all(pos in clicked_tiles for pos in [(0, 0), (0, 4), (4, 0), (4, 4)]):
        if "four_corners" not in bingo_patterns:
            new_patterns.append("four_corners")

    # Plus shape: complete center row and center column.
    plus_cells: Set[Coordinate] = {(2, c) for c in range(5)} | {
        (r, 2) for r in range(5)
    }
    if all(cell in clicked_tiles for cell in plus_cells):
        if "plus" not in bingo_patterns:
            new_patterns.append("plus")

    # X shape: both diagonals complete.
    if all((i, i) in clicked_tiles for i in range(5)) and all(
        (i, 4 - i) in clicked_tiles for i in range(5)
    ):
        if "x_shape" not in bingo_patterns:
            new_patterns.append("x_shape")

    # Outside edges (perimeter): all border cells clicked.
    perimeter_cells: Set[Coordinate] = (
        {(0, c) for c in range(5)}
        | {(4, c) for c in range(5)}
        | {(r, 0) for r in range(5)}
        | {(r, 4) for r in range(5)}
    )
    if all(cell in clicked_tiles for cell in perimeter_cells):
        if "perimeter" not in bingo_patterns:
            new_patterns.append("perimeter")

    if new_patterns:
        # Separate new win patterns into standard and special ones.
        special_set: Set[str] = {
            "blackout",
            "four_corners",
            "plus",
            "x_shape",
            "perimeter",
        }
        standard_new: List[BingoPattern] = [
            p for p in new_patterns if p not in special_set
        ]
        special_new: List[BingoPattern] = [p for p in new_patterns if p in special_set]

        # Process standard win conditions (rows, columns, diagonals).
        if standard_new:
            for pattern in standard_new:
                bingo_patterns.add(pattern)
            standard_total: int = sum(1 for p in bingo_patterns if p not in special_set)
            message: str
            if standard_total == 1:
                message = "BINGO!"
            elif standard_total == 2:
                message = "DOUBLE BINGO!"
            elif standard_total == 3:
                message = "TRIPLE BINGO!"
            elif standard_total == 4:
                message = "QUADRUPLE BINGO!"
            elif standard_total == 5:
                message = "QUINTUPLE BINGO!"
            else:
                message = f"{standard_total}-WAY BINGO!"
            ui.notify(message, color="green", duration=5)

        # Process special win conditions individually.
        for sp in special_new:
            bingo_patterns.add(sp)
            # Format the name to title-case and append "Bingo!"
            sp_message: str = sp.replace("_", " ").title() + " Bingo!"
            ui.notify(sp_message, color="blue", duration=5)


def reset_board() -> None:
    """
    Reset the board by clearing all clicked states, clearing winning patterns,
    and re-adding the FREE SPACE.
    """
    global bingo_patterns
    bingo_patterns.clear()  # Clear previously recorded wins.
    clicked_tiles.clear()
    for r, row in enumerate(board):
        for c, phrase in enumerate(row):
            if phrase.upper() == FREE_SPACE_TEXT:
                clicked_tiles.add((r, c))
    
    # Save state after reset for persistence
    save_state_to_storage()


def generate_new_board(phrases: List[str]) -> None:
    """
    Generate a new board with an incremented iteration seed and update all board views.

    Args:
        phrases: List of phrases to use for the board
    """
    global board_iteration
    global is_game_closed, header_label
    is_game_closed = False
    board_iteration += 1
    generate_board(board_iteration, phrases)

    # Update all board views (both home and stream)
    from src.ui.board_builder import build_board

    for view_key, (container, tile_buttons_local) in board_views.items():
        container.clear()
        tile_buttons_local.clear()
        build_board(container, tile_buttons_local, toggle_tile, board, clicked_tiles)
        container.update()

    # Reset any clicked tiles except for the FREE SPACE
    reset_board()


def close_game() -> None:
    """
    Close the game - show closed message instead of the board and update the header text.
    This function is called when the close button is clicked.
    """
    global is_game_closed, header_label
    is_game_closed = True

    # Update header text on the current view
    if header_label is not None:
        header_label.set_text(CLOSED_HEADER_TEXT)
        header_label.update()

    # Show closed message in board containers
    from src.config.constants import CLOSED_MESSAGE_COLOR, CLOSED_MESSAGE_TEXT
    from src.ui.board_builder import build_closed_message

    # Replace board with closed message in all views
    for view_key, (container, tile_buttons_local) in board_views.items():
        container.clear()
        build_closed_message(container)
        container.update()

    # Modify the controls row to only show the New Board button
    if controls_row is not None:
        controls_row.clear()
        with controls_row:
            with ui.button("Start New Game", icon="autorenew", on_click=reopen_game).classes(
                "px-4 py-2"
            ) as new_game_btn:
                ui.tooltip("Start a new game with a fresh board")

    # Save game state with is_game_closed=True for persistence
    save_state_to_storage()

    # In NiceGUI 2.11+, updates are automatically synchronized between clients
    # via the timer-based sync_board_state function
    logging.info("Game closed - changes will be synchronized by timers")

    # Notify that game has been closed
    ui.notify("Game has been closed", color="red", duration=3)


def reopen_game() -> None:
    """
    Reopen the game after it has been closed.
    This regenerates a new board and resets the UI.
    """
    global is_game_closed, header_label, board_iteration

    # Reset game state
    is_game_closed = False

    # Update header text back to original for the current view
    if header_label is not None:
        header_label.set_text(HEADER_TEXT)
        header_label.update()

    # Generate a new board with increased board_iteration for different seed
    from src.utils.file_operations import read_phrases_file

    phrases: List[str] = read_phrases_file()

    board_iteration += 1
    generate_board(board_iteration, phrases)

    # Rebuild the controls row with all buttons
    from src.ui.controls import rebuild_controls_row

    if controls_row is not None:
        rebuild_controls_row(controls_row)

    # Recreate and show all board views
    from src.ui.board_builder import build_board

    for view_key, (container, tile_buttons_local) in board_views.items():
        container.style("display: block;")
        container.clear()
        tile_buttons_local.clear()
        build_board(container, tile_buttons_local, toggle_tile, board, clicked_tiles)
        container.update()

    # Reset clicked tiles except for FREE SPACE
    reset_board()

    # Notify that a new game has started
    ui.notify("New game started", color="green", duration=3)

    # In NiceGUI 2.11+, updates are automatically synchronized between clients
    # via the timer-based sync_board_state function
    logging.info("Game reopened - changes will be synchronized by timers")
        
    # Save state to storage for persistence across app restarts
    save_state_to_storage()


def save_state_to_storage() -> bool:
    """
    Save the current game state to app.storage.general for persistence
    across application restarts.
    
    Returns:
        bool: True if state was saved successfully, False otherwise
    """
    try:
        if not hasattr(app, 'storage') or not hasattr(app.storage, 'general'):
            logging.warning("app.storage.general not available")
            return False
        
        # Convert non-JSON-serializable types to serializable equivalents
        clicked_tiles_list = list(tuple(coord) for coord in clicked_tiles)
        bingo_patterns_list = list(bingo_patterns)
        
        # Prepare state dictionary
        state = {
            'board': board,
            'clicked_tiles': clicked_tiles_list,
            'bingo_patterns': bingo_patterns_list,
            'board_iteration': board_iteration,
            'is_game_closed': is_game_closed,
            'today_seed': today_seed
        }
        
        # Save to storage
        app.storage.general['game_state'] = state
        logging.debug("Game state saved to persistent storage")
        return True
    except Exception as e:
        logging.error(f"Error saving state to storage: {e}")
        return False


def load_state_from_storage() -> bool:
    """
    Load game state from app.storage.general if available.
    
    Returns:
        bool: True if state was loaded successfully, False otherwise
    """
    global board, clicked_tiles, bingo_patterns, board_iteration, is_game_closed, today_seed
    
    try:
        if not hasattr(app, 'storage') or not hasattr(app.storage, 'general'):
            logging.warning("app.storage.general not available")
            return False
        
        if 'game_state' not in app.storage.general:
            logging.debug("No saved game state found in storage")
            return False
        
        state = app.storage.general['game_state']
        
        # Load board
        board = state['board']
        
        # Convert clicked_tiles from list back to set
        clicked_tiles = set(tuple(coord) for coord in state['clicked_tiles'])
        
        # Convert bingo_patterns from list back to set
        bingo_patterns = set(state['bingo_patterns'])
        
        # Load other state variables
        board_iteration = state['board_iteration']
        is_game_closed = state['is_game_closed']
        today_seed = state['today_seed']
        
        logging.debug("Game state loaded from persistent storage")
        return True
    except Exception as e:
        logging.error(f"Error loading state from storage: {e}")
        return False
