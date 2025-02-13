from nicegui import ui
import random
import datetime
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- New: Color constants and font ---
TILE_CLICKED_BG_COLOR = "#3b82f6"        # Blue background for clicked tiles
TILE_CLICKED_TEXT_COLOR = "white"
TILE_UNCLICKED_BG_COLOR = "#facc15"       # Yellow background for unclicked tiles
TILE_UNCLICKED_TEXT_COLOR = "black"
FREE_MEAT_TEXT_COLOR = "#FF7f33"          # Color for the FREE MEAT tile

HOME_BG_COLOR = "#100079"                 # Background for home page
STREAM_BG_COLOR = "#00FF00"               # Background for stream page
HEADER_TEXT_COLOR = "#0CB2B3"             # Color for header text

FONT_FAMILY = "'Super Carnival', sans-serif"

# New constants for line-height adjustments
LINE_HEIGHT_SHORT = "1.5em"
LINE_HEIGHT_DEFAULT = "1em"

def get_line_style_for_lines(line_count: int, default_text_color: str) -> str:
    """
    Return a complete style string with an adjusted line-height based on the number of lines
    that resulted from splitting the phrase.
    Fewer lines (i.e. unsplit phrases) get a higher line-height, while more lines get a lower one.
    """
    if line_count == 1:
        lh = "1.5em"  # More spacing for a single line.
    elif line_count == 2:
        lh = "1.2em"  # Slightly reduced spacing for two lines.
    elif line_count == 3:
        lh = "0.9em"    # Even tighter spacing for three lines.
    else:
        lh = "0.9em"  # For four or more lines.
    return f"font-family: {FONT_FAMILY}; padding: 0; margin: 0; color: {default_text_color}; line-height: {lh};"

# Read phrases from a text file and convert them to uppercase.
with open("phrases.txt", "r") as f:
    phrases = [line.strip().upper() for line in f if line.strip()]

# Use today's date as the seed for deterministic shuffling
today_seed = datetime.date.today().strftime("%Y%m%d")
random.seed(int(today_seed))  # Everyone gets the same shuffle per day

# Shuffle and create the 5x5 board:
shuffled_phrases = random.sample(phrases, 24)  # Random but fixed order per day
shuffled_phrases.insert(12, "FREE MEAT")         # Center slot
board = [shuffled_phrases[i:i+5] for i in range(0, 25, 5)]

# Track clicked tiles and store chip references
clicked_tiles = set()
tile_buttons = {}  # {(row, col): chip}
tile_icons = {}  # {(row, col): icon reference}
admin_checkboxes = {}  # {(row, col): admin checkbox element}

def split_phrase_into_lines(phrase: str) -> list:
    """
    Splits the phrase into balanced lines.
    If the phrase has two or fewer words, return it as a single line.
    Otherwise, split into two lines at the midpoint.
    """
    words = phrase.split()
    if len(words) == 1:
        return [words[0]]
    elif len(words) == 2:
        return [words[0], words[1]]
    elif len(words) == 3:
        return [words[0], words[1], words[2]]
    else:
        mid = round(len(words) / 2)
        return [" ".join(words[:mid]), " ".join(words[mid:])]

# Function to create the Bingo board UI
def create_bingo_board():
    # The header and seed label are handled outside this function.
    logging.info("Creating Bingo board")

    with ui.element("div").classes("flex justify-center items-center w-full"):
         with ui.element("div").classes("w-full max-w-3xl aspect-square"):
              with ui.grid(columns=5).classes("gap-2 h-full grid-rows-5"):
                for row_idx, row in enumerate(board):
                    for col_idx, phrase in enumerate(row):
                        # Create a clickable card for this cell with reduced padding and centered content. Added 'relative' class for icon overlay.
                        card = ui.card().classes("relative p-2 bg-yellow-500 rounded-lg w-full h-full flex items-center justify-center").style("cursor: pointer;")
                        with card:
                            with ui.column().classes("flex flex-col items-center justify-center gap-0 w-full"):
                                # Set text color: free meat gets #FF7f33, others black
                                default_text_color = FREE_MEAT_TEXT_COLOR if phrase.upper() == "FREE MEAT" else TILE_UNCLICKED_TEXT_COLOR
                                lines = split_phrase_into_lines(phrase)
                                line_count = len(lines)
                                for line in lines:
                                    with ui.row().classes("w-full"):
                                        ui.label(line).classes("fit-text text-center select-none").style(get_line_style_for_lines(line_count, default_text_color))
                        
                        tile_buttons[(row_idx, col_idx)] = card
                        
                        if phrase.upper() == "FREE MEAT":
                            clicked_tiles.add((row_idx, col_idx))
                            card.style("color: #FF7f33; border: none;")
                        else:
                            card.on("click", lambda e, r=row_idx, c=col_idx: toggle_tile(r, c))

# Toggle tile click state (for example usage)
def toggle_tile(row, col):
    # Do not allow toggling for the FREE MEAT cell (center cell)
    if (row, col) == (2, 2):
        return
    key = (row, col)
    if key in clicked_tiles:
        logging.debug(f"Tile at {key} unclicked")
        clicked_tiles.remove(key)
    else:
        logging.debug(f"Tile at {key} clicked")
        clicked_tiles.add(key)
    check_winner()
    sync_board_state()

# Check for Bingo win condition
def check_winner():
    for i in range(5):
        if all((i, j) in clicked_tiles for j in range(5)) or all((j, i) in clicked_tiles for j in range(5)):
            ui.notify("BINGO!", color="green", duration=5)
            return
    if all((i, i) in clicked_tiles for i in range(5)) or all((i, 4 - i) in clicked_tiles for i in range(5)):
        ui.notify("BINGO!", color="green", duration=5)

def sync_board_state():
    update_tile_styles(tile_buttons)
    sync_admin_checkboxes()
    update_admin_visibility()

def sync_admin_checkboxes():
    """
    Sync the value in each admin panel checkbox with the global clicked_tiles.
    """
    for key, chks in admin_checkboxes.items():
        new_value = key in clicked_tiles
        if "single" in chks and chks["single"].value != new_value:
            chks["single"].value = new_value
            chks["single"].update()

def update_admin_visibility():
    """
    Bind the visibility of the admin checkboxes:
       - left copy is visible only when unchecked (value False)
       - right copy is visible only when checked (value True)
    """
    for key, chks in admin_checkboxes.items():
        val = chks["single"].value  # both copies hold the same value
        chks["single"].set_visibility(not val)  # show left box only when unchecked
        chks["single"].update()

def admin_checkbox_change(e, key):
    # When a checkbox in the admin page is toggled, update the global clicked_tiles
    if e.value:
        clicked_tiles.add(key)
    else:
        clicked_tiles.discard(key)
    sync_board_state()

@ui.page("/")
def home_page():
    # Set up NiceGUI page and head elements    
    setup_head(HOME_BG_COLOR)

    global tile_buttons
    tile_buttons = build_board(ui.element("div").classes("flex justify-center items-center w-full"), tile_buttons, toggle_tile)

    # Add a timer that calls sync_board_state every 1 second to push state updates to all clients
    ui.timer(0.1, sync_board_state)

    with ui.element("div").classes("w-full mt-4"):
        ui.label(f"Seed: {today_seed}").classes("text-md text-gray-300 text-center")

@ui.page("/admin")
def admin_page():
    def reset_board():
        clicked_tiles.clear()
        # Re-add FREE MEAT at the center (position (2,2))
        clicked_tiles.add((2, 2))
        sync_board_state()
        build_admin_panel()  # rebuild panel to reflect state changes

    with ui.row().classes("zd max-w-xl mx-auto p-4") as container:
        ui.label("Admin Panel").classes("text-h4 text-center")
        ui.button("Reset Board", on_click=reset_board)

        def build_admin_panel():
            panel.clear()  # clear previous panel content
            with panel:
                with ui.column():
                    # Single column design: list each tile with a toggle checkbox.
                    for r in range(5):
                        for c in range(5):
                            key = (r, c)
                            phrase = board[r][c]
                            with ui.row().classes("items-center"):
                                ui.label(f"{phrase} ({r},{c})").classes("w-3/4")
                                def on_checkbox_change(e, key=key):
                                    if e.value:
                                        clicked_tiles.add(key)
                                    else:
                                        clicked_tiles.discard(key)
                                    sync_board_state()
                                cb = ui.checkbox("", value=(key in clicked_tiles), on_change=on_checkbox_change)
                                # Save a single reference to this admin checkbox
                                admin_checkboxes[key] = {"single": cb}

        panel = ui.column()  # container for the admin panel
        build_admin_panel()
        ui.timer(0.1, sync_admin_checkboxes)

@ui.page("/stream")
def stream_page():
    # Set up NiceGUI page and head elements    
    setup_head(STREAM_BG_COLOR)

    

    # Build the board using the common function (use a local dictionary here)
    local_tile_buttons = build_board(ui.element("div").classes("flex justify-center items-center w-full"), {}, toggle_tile)

    # Timer to update ONLY the stream view's board (using its local_tile_buttons)
    ui.timer(0.1, lambda: update_tile_styles(local_tile_buttons))

    with ui.element("div").classes("w-full mt-4"):
        ui.label(f"Seed: {today_seed}").classes("text-md text-gray-300 text-center")

def setup_head(background_color: str):
    """
    Set up common head elements: fonts, fitty JS, and background color.
    """
    ui.add_head_html(f'<link href="https://fonts.cdnfonts.com/css/super-carnival" rel="stylesheet">')
    ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/fitty@2.3.6/dist/fitty.min.js"></script>')
    ui.add_head_html(f'<style>body {{ background-color: {background_color}; }}</style>')
    ui.add_head_html("""<script>
        document.addEventListener('DOMContentLoaded', () => {
            fitty('.fit-text', { multiLine: true, minSize: 10, maxSize: 1000 });
            fitty('.fit-header', { multiLine: true, minSize: 10, maxSize: 2000 });
        });
        window.addEventListener('resize', () => {
            fitty('.fit-text', { multiLine: true, minSize: 10, maxSize: 1000 });
            fitty('.fit-header', { multiLine: true, minSize: 10, maxSize: 2000 });
        });
    </script>""")

    # Use full width with padding so the header spans edge-to-edge
    with ui.element("div").classes("w-full"):
        ui.label("COMMIT !BINGO").classes("fit-header text-center").style(f"font-family: {FONT_FAMILY}; color: {HEADER_TEXT_COLOR};")

def build_board(parent, tile_buttons_dict: dict, on_tile_click):
    """
    Build the common Bingo board in the given parent element.
    The resulting tile UI elements are added to tile_buttons_dict.
    """
    with parent:
        # Use full width and add padding so the board touches the edges with a gap
        with ui.element("div").classes("w-full aspect-square p-4"):
            with ui.grid(columns=5).classes("gap-2 h-full grid-rows-5"):
                for row_idx, row in enumerate(board):
                    for col_idx, phrase in enumerate(row):
                        card = ui.card().classes(
                            "relative p-2 bg-yellow-500 rounded-lg w-full h-full flex items-center justify-center"
                        ).style("cursor: pointer;")
                        with card:
                            with ui.column().classes("flex flex-col items-center justify-center gap-0 w-full"):
                                default_text_color = FREE_MEAT_TEXT_COLOR if phrase.upper() == "FREE MEAT" else TILE_UNCLICKED_TEXT_COLOR
                                lines = split_phrase_into_lines(phrase)
                                line_count = len(lines)
                                for line in lines:
                                    with ui.row().classes("w-full"):
                                        ui.label(line).classes("fit-text text-center select-none").style(get_line_style_for_lines(line_count, default_text_color))
                        tile_buttons_dict[(row_idx, col_idx)] = card
                        if phrase.upper() == "FREE MEAT":
                            clicked_tiles.add((row_idx, col_idx))
                            card.style(f"color: {FREE_MEAT_TEXT_COLOR}; border: none;")
                        else:
                            card.on("click", lambda e, r=row_idx, c=col_idx: on_tile_click(r, c))
    return tile_buttons_dict

def update_tile_styles(tile_buttons_dict: dict):
    """
    Update styles for each tile in the given dictionary based on the global clicked_tiles.
    """
    for (r, c), card in tile_buttons_dict.items():
        if board[r][c].upper() == "FREE MEAT":
            continue
        if (r, c) in clicked_tiles:
            new_style = f"background-color: {TILE_CLICKED_BG_COLOR}; color: {TILE_CLICKED_TEXT_COLOR}; border: none;"
        else:
            new_style = f"background-color: {TILE_UNCLICKED_BG_COLOR}; color: {TILE_UNCLICKED_TEXT_COLOR}; border: none;"
        card.style(new_style)
        card.update()

# Run the NiceGUI app
ui.run(port=8080, title="Commit Bingo", dark=False)
