"""
UI synchronization module for the Bingo application.
"""

import logging

from nicegui import ui

from src.config.constants import CLOSED_HEADER_TEXT, HEADER_TEXT
from src.core.game_logic import board_views, header_label, is_game_closed
from src.utils.text_processing import get_line_style_for_lines, split_phrase_into_lines


def sync_board_state():
    """
    Update tile styles in every board view (e.g., home and stream).
    Also handles the game closed state to ensure consistency across views.
    """
    try:
        # Import these directly to ensure we're using the most current reference
        from src.core.game_logic import header_label as current_header_label
        from src.core.game_logic import is_game_closed as current_is_closed
        
        # If game is closed, make sure all views reflect that
        if current_is_closed:
            # Update header if available
            if current_header_label:
                current_header_label.set_text(CLOSED_HEADER_TEXT)
                current_header_label.update()

            # Show closed message in all board views
            from src.ui.board_builder import build_closed_message

            for view_key, (container, _) in board_views.items():
                container.clear()
                build_closed_message(container)
                container.update()

            # Make sure controls row is showing only the Start New Game button
            from src.core.game_logic import controls_row as current_controls_row, reopen_game

            if current_controls_row:
                # Only update controls if it's not already showing just the New Game button
                if (not hasattr(current_controls_row, 'default_slot') or 
                    not current_controls_row.default_slot or 
                    len(current_controls_row.default_slot.children) != 1):
                    
                    current_controls_row.clear()
                    with current_controls_row:
                        with ui.button(
                            "Start New Game", icon="autorenew", on_click=reopen_game
                        ).classes("px-4 py-2") as new_game_btn:
                            ui.tooltip("Start a new game with a fresh board")

            return
        else:
            # Ensure header text is correct when game is open
            if current_header_label and current_header_label.text != HEADER_TEXT:
                current_header_label.set_text(HEADER_TEXT)
                current_header_label.update()

        # Normal update if game is not closed
        # Update tile styles in every board view (e.g., home and stream)
        for view_key, (container, tile_buttons_local) in board_views.items():
            update_tile_styles(tile_buttons_local)

        # Apply cached sizes whenever possible, or trigger fitty for new elements
        # This helps reduce flickering from too many fitty calculations
        try:
            js_code = """
                // Try to use cached sizes first
                if (typeof applyCachedSizes === 'function') {
                    const needsFitty = applyCachedSizes();
                    
                    // Only trigger fitty if we have elements that need calculation
                    if (needsFitty && typeof resetFittyTimer === 'function') {
                        resetFittyTimer();
                    }
                }
            """
            ui.run_javascript(js_code)
        except Exception as e:
            logging.debug(
                f"JavaScript execution failed (likely disconnected client): {e}"
            )
    except Exception as e:
        logging.debug(f"Error in sync_board_state: {e}")


def update_tile_styles(tile_buttons_dict: dict):
    """
    Update styles for each tile and its text labels based on the clicked_tiles set.
    """
    from src.config.constants import (
        FREE_SPACE_TEXT,
        TILE_CLICKED_BG_COLOR,
        TILE_CLICKED_TEXT_COLOR,
        TILE_UNCLICKED_BG_COLOR,
        TILE_UNCLICKED_TEXT_COLOR,
    )
    from src.core.game_logic import board, clicked_tiles

    for (r, c), tile in tile_buttons_dict.items():
        # tile is a dict with keys "card" and "labels"
        phrase = board[r][c]

        if (r, c) in clicked_tiles:
            new_card_style = f"background-color: {TILE_CLICKED_BG_COLOR}; color: {TILE_CLICKED_TEXT_COLOR}; border: none; outline: 3px solid {TILE_CLICKED_TEXT_COLOR};"
            new_label_color = TILE_CLICKED_TEXT_COLOR
        else:
            new_card_style = f"background-color: {TILE_UNCLICKED_BG_COLOR}; color: {TILE_UNCLICKED_TEXT_COLOR}; border: none;"
            new_label_color = TILE_UNCLICKED_TEXT_COLOR

        # Update the card style.
        tile["card"].style(new_card_style)
        tile["card"].update()

        # Recalculate the line count for the current phrase.
        lines = split_phrase_into_lines(phrase)
        line_count = len(lines)
        # Recalculate label style based on the new color.
        new_label_style = get_line_style_for_lines(line_count, new_label_color)

        # Update all label elements for this tile.
        for label_info in tile["labels"]:
            lbl = label_info["ref"]
            # Reapply the stored base classes.
            lbl.classes(label_info["base_classes"])
            # Update inline style (which may now use a new color due to tile click state).
            lbl.style(new_label_style)
            lbl.update()
