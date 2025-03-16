"""
Routes module for the Bingo application.
"""

import json
import logging
import uuid
from typing import Dict, Set

from nicegui import app, ui

from src.config.constants import HOME_BG_COLOR, STREAM_BG_COLOR
from src.ui.board_builder import create_board_view
from src.ui.sync import sync_board_state

# Track connected clients by path
# Key is path, value is set of client IDs
connected_clients: Dict[str, Set[str]] = {
    "/": set(),
    "/stream": set()
}

# Counter for active home clients 
active_home_users = 0


@ui.page("/")
def home_page():
    """
    Main page with the interactive bingo board and controls.
    """
    global active_home_users
    
    # Track this client connection
    client_id = app.storage.user.get('client_id', str(uuid.uuid4()))
    app.storage.user['client_id'] = client_id
    
    if client_id not in connected_clients["/"]:
        active_home_users += 1
        connected_clients["/"].add(client_id)
        logging.info(f"Home user connected. Active users: {active_home_users}")
    
    create_board_view(HOME_BG_COLOR, True)

    # Display active user count
    with ui.card():
        active_users_label = ui.label(f"Connections: {active_home_users}")
        ui.timer(5, lambda: active_users_label.set_text(f"Connections: {active_home_users}"))
    
    try:
        # Create a timer that deactivates when the client disconnects
        # Using 0.1 seconds gives good responsiveness while avoiding UI flicker
        timer = ui.timer(0.1, sync_board_state)
        
        # Handle disconnection
        def on_disconnect():
            global active_home_users
            if client_id in connected_clients["/"]:
                connected_clients["/"].remove(client_id)
                active_home_users -= 1
                logging.info(f"Home user disconnected. Active users: {active_home_users}")
            timer.cancel()
        
        app.on_disconnect(on_disconnect)
    except Exception as e:
        logging.warning(f"Error creating timer: {e}")


@ui.page("/stream")
def stream_page():
    """
    Stream view of the bingo board (without controls, for display purposes).
    """
    # Track this client connection
    client_id = app.storage.user.get('client_id', str(uuid.uuid4()))
    app.storage.user['client_id'] = client_id
    
    if client_id not in connected_clients["/stream"]:
        connected_clients["/stream"].add(client_id)
        logging.info(f"Stream user connected. Total stream users: {len(connected_clients['/stream'])}")
    
    create_board_view(STREAM_BG_COLOR, False)
    
    try:
        # Create a timer that deactivates when the client disconnects
        # Using 0.1 seconds gives good responsiveness while avoiding UI flicker
        timer = ui.timer(0.1, sync_board_state)
        
        # Handle disconnection
        def on_disconnect():
            if client_id in connected_clients["/stream"]:
                connected_clients["/stream"].remove(client_id)
                logging.info(f"Stream user disconnected. Total stream users: {len(connected_clients['/stream'])}")
            timer.cancel()
        
        app.on_disconnect(on_disconnect)
    except Exception as e:
        logging.warning(f"Error creating timer: {e}")


@app.get("/health")
def health():
    return json.dumps({
        "health": "ok",
        "active_players": active_home_users,
        "stream_viewers": len(connected_clients["/stream"])
    }, indent=4, sort_keys=True)


def init_routes():
    """
    Initialize routes and return any necessary objects.
    This is mainly a placeholder to ensure routes are imported
    and decorated properly.
    """
    return None
