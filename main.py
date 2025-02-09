from nicegui import ui
import random
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    else:
        mid = round(len(words) / 2)
        return [" ".join(words[:mid]), " ".join(words[mid:])]

# Function to create the Bingo board UI
def create_bingo_board():
    # The header and seed label are handled outside this function.
    logging.info("Creating Bingo board")

    with ui.element("div").classes("flex justify-center items-center w-full"):
        with ui.grid(columns=5).classes("gap-2 mt-4"):
            for row_idx, row in enumerate(board):
                for col_idx, phrase in enumerate(row):
                    # Create a clickable card for this cell with reduced padding and centered content.
                    card = ui.card().classes("p-2 bg-yellow-500 hover:bg-yellow-400 rounded-lg w-full flex items-center justify-center").style("cursor: pointer; aspect-ratio: 1;")
                    with card:
                        with ui.column().classes("flex flex-col items-center justify-center gap-0 w-full"):
                            # Set text color: free meat gets #FF7f33, others black
                            default_text_color = "#FF7f33" if phrase.upper() == "FREE MEAT" else "black"
                            # Split the phrase into balanced lines.
                            for line in split_phrase_into_lines(phrase):
                                tile = ui.label(line).classes("fit-text text-center")
                                tile.style(f"font-family: 'Super Carnival', sans-serif; padding: 0; margin: 0; color: {default_text_color};")
                    # Save the card reference.
                    tile_buttons[(row_idx, col_idx)] = card
                    if phrase.upper() == "FREE MEAT":
                        clicked_tiles.add((row_idx, col_idx))
                        # Set the free meat cell's style: text color, background, etc.
                        card.style("color: #FF7f33; background: #facc15; border: none;")
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
        tile_buttons[key].style("background: #facc15; border: none; color: black;")
    else:
        logging.debug(f"Tile at {key} clicked")
        clicked_tiles.add(key)
        tile_buttons[key].style("color: #22c55e; border: 15px solid #15803d;")

    check_winner()

# Check for Bingo win condition
def check_winner():
    for i in range(5):
        if all((i, j) in clicked_tiles for j in range(5)) or all((j, i) in clicked_tiles for j in range(5)):
            ui.notify("BINGO!", color="green", duration=5)
            return
    if all((i, i) in clicked_tiles for i in range(5)) or all((i, 4 - i) in clicked_tiles for i in range(5)):
        ui.notify("BINGO!", color="green", duration=5)

# Set up NiceGUI page and head elements
ui.page("/")
ui.add_head_html('<link href="https://fonts.cdnfonts.com/css/super-carnival" rel="stylesheet">')
ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/fitty@2.3.6/dist/fitty.min.js"></script>')

with ui.element("div").classes("w-full max-w-3xl mx-auto"):
    ui.label("COMMIT BINGO!").classes("fit-header text-center").style("font-family: 'Super Carnival', sans-serif;")

create_bingo_board()

with ui.element("div").classes("w-full mt-4"):
    ui.label(f"Seed: {today_seed}").classes("text-md text-gray-300 text-center")

ui.timer(0.5, lambda: ui.run_javascript("fitty('.fit-text', { multiLine: true, maxSize: 100 }); fitty('.fit-header', { multiLine: true, maxSize: 200 });"), once=True)
ui.run(port=8080, title="Commit Bingo", dark=True)
