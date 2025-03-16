"""
Head setup module for the Bingo application.
"""

import logging

from nicegui import ui

from src.config.constants import (
    BOARD_TILE_FONT,
    BOARD_TILE_FONT_STYLE,
    BOARD_TILE_FONT_WEIGHT,
    HEADER_FONT_FAMILY,
    HEADER_TEXT,
    HEADER_TEXT_COLOR,
)
from src.utils.text_processing import get_google_font_css


def setup_head(background_color: str):
    """
    Set up common head elements: fonts, fitty JS, and background color.
    """
    # Set the header label in the game_logic module
    from src.core.game_logic import header_label

    ui.add_css(
        """
        
            @font-face {
                font-family: 'Super Carnival';
                font-style: normal;
                font-weight: 400;
                /* Load the local .woff file from the static folder (URL-encoded for Safari) */
                src: url('/static/Super%20Carnival.woff') format('woff');
            }
        
    """
    )

    ui.add_head_html(
        f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family={BOARD_TILE_FONT.replace(" ", "+")}&display=swap" rel="stylesheet">
    """
    )

    # Add CSS class for board tile fonts
    ui.add_head_html(
        get_google_font_css(
            BOARD_TILE_FONT, BOARD_TILE_FONT_WEIGHT, BOARD_TILE_FONT_STYLE, "board_tile"
        )
    )

    # Add fitty.js for text resizing
    ui.add_head_html(
        '<script src="https://cdn.jsdelivr.net/npm/fitty@2.3.6/dist/fitty.min.js"></script>'
    )

    # Add html2canvas library and capture function.
    ui.add_head_html(
        """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function captureBoardAndDownload(seed) {
        var boardElem = document.getElementById('board-container');
        if (!boardElem) {
            alert("Board container not found!");
            return;
        }
        // Run fitty to ensure text is resized and centered
        if (typeof fitty !== 'undefined') {
            fitty('.fit-text', { multiLine: true, minSize: 10, maxSize: 1000 });
            fitty('.fit-text-small', { multiLine: true, minSize: 10, maxSize: 72 });
        }
    
        // Wait a short period to ensure that the board is fully rendered and styles have settled.
        setTimeout(function() {
            html2canvas(boardElem, {
                useCORS: true,
                scale: 10,  // Increase scale for higher resolution
                logging: true,
                backgroundColor: null
            }).then(function(canvas) {
                var link = document.createElement('a');
                link.download = `bingo_board_${seed}.png`;  // Include seed in filename
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        }, 500);  // Adjust delay if necessary
    }
    
    // Function to safely apply fitty
    function applyFitty() {
        if (typeof fitty !== 'undefined') {
            fitty('.fit-text', { multiLine: true, minSize: 10, maxSize: 1000 });
            fitty('.fit-text-small', { multiLine: true, minSize: 10, maxSize: 72 });
            fitty('.fit-header', { multiLine: true, minSize: 10, maxSize: 2000 });
        }
    }
    </script>
    """
    )

    # Set background color
    ui.add_head_html(f"<style>body {{ background-color: {background_color}; }}</style>")

    # Add event listeners for fitty with caching and efficient reapplication
    ui.add_head_html(
        """<script>
        // Cache for storing computed font sizes
        window.fittySizeCache = {};
        
        // Track window dimensions to know when recalculation is needed
        let lastWindowWidth = window.innerWidth;
        let lastWindowHeight = window.innerHeight;
        
        // Track when the last fitty application was performed to avoid rapid changes
        let lastFittyApplication = 0;
        let fittyTimer;
        
        // Allow external code to reset/trigger the fitty timer
        window.resetFittyTimer = function() {
            clearTimeout(fittyTimer);
            // Wait a bit longer to ensure fewer, better-timed fitty calls
            fittyTimer = setTimeout(applyFitty, 150);
        };
        
        // Store computed size in cache
        function cacheFittySize(element, size) {
            const id = element.getAttribute('id') || 
                       element.getAttribute('data-fitty-id') || 
                       Math.random().toString(36).substring(2, 10);
                       
            // Ensure the element has an ID for cache lookup
            if (!element.getAttribute('data-fitty-id')) {
                element.setAttribute('data-fitty-id', id);
            }
            
            // Store the size
            window.fittySizeCache[id] = {
                size: size,
                windowWidth: lastWindowWidth,
                windowHeight: lastWindowHeight,
                content: element.textContent,
                className: element.className
            };
        }
        
        // Try to retrieve cached size
        function getCachedSize(element) {
            const id = element.getAttribute('id') || element.getAttribute('data-fitty-id');
            if (!id || !window.fittySizeCache[id]) return null;
            
            const cache = window.fittySizeCache[id];
            
            // Only use cache if window size and content haven't changed
            if (cache.windowWidth === lastWindowWidth && 
                cache.windowHeight === lastWindowHeight &&
                cache.content === element.textContent &&
                cache.className === element.className) {
                return cache.size;
            }
            
            return null;
        }
        
        // Apply cached sizes if available, otherwise use fitty
        function applyCachedSizes() {
            const elements = document.querySelectorAll('.fit-text, .fit-text-small, .fit-header');
            let needsFitty = false;
            
            elements.forEach(function(el) {
                const cachedSize = getCachedSize(el);
                if (cachedSize !== null) {
                    // Apply cached size directly
                    el.style.fontSize = cachedSize + 'px';
                    el.setAttribute('data-fitty-applied', 'cached');
                } else {
                    // Mark for fitty processing
                    el.setAttribute('data-fitty-applied', 'pending');
                    needsFitty = true;
                }
            });
            
            return needsFitty;
        }
        
        // Run fitty when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Update window dimensions
            lastWindowWidth = window.innerWidth;
            lastWindowHeight = window.innerHeight;
            
            // First try cached sizes
            const needsFitty = applyCachedSizes();
            
            // Only run fitty if necessary
            if (needsFitty) {
                setTimeout(applyFitty, 150);
            }
        });
        
        // Run fitty when window is resized
        let resizeTimer;
        window.addEventListener('resize', function() {
            // Update window dimensions
            lastWindowWidth = window.innerWidth;
            lastWindowHeight = window.innerHeight;
            
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(applyFitty, 150);  // Debounce resize events
        });
        
        // Intercept fitty to capture sizes
        const originalFitty = window.fitty;
        window.fitty = function(selector, options) {
            if (typeof originalFitty !== 'function') return null;
            
            // Call the original fitty
            const fittyInstances = originalFitty(selector, options);
            
            // Capture the computed sizes after fitty completes
            if (Array.isArray(fittyInstances)) {
                fittyInstances.forEach(function(instance) {
                    instance.element.addEventListener('fit', function(e) {
                        // Store the computed font size in our cache
                        cacheFittySize(instance.element, e.detail.newValue);
                    });
                });
            }
            
            return fittyInstances;
        };
        
        // Improved applyFitty function with caching
        window.applyFitty = function(force = false) {
            // Update window dimensions
            lastWindowWidth = window.innerWidth;
            lastWindowHeight = window.innerHeight;
            
            // Don't run fitty more often than every 300ms to avoid flickering
            const now = Date.now();
            if (!force && now - lastFittyApplication < 300) {
                // Schedule for later instead
                window.resetFittyTimer();
                return;
            }
            
            // First try to apply cached sizes
            const needsFitty = applyCachedSizes();
            
            // Only run fitty if we have elements that couldn't use cached values
            if (needsFitty && typeof originalFitty === 'function') {
                // Apply fitty only to elements that need it
                fitty('.fit-text[data-fitty-applied="pending"]', { multiLine: true, minSize: 10, maxSize: 1000 });
                fitty('.fit-text-small[data-fitty-applied="pending"]', { multiLine: true, minSize: 10, maxSize: 72 });
                fitty('.fit-header[data-fitty-applied="pending"]', { multiLine: true, minSize: 10, maxSize: 2000 });
                
                lastFittyApplication = now;
            }
        };
        
        // Periodically check for new elements that need fitty, but less frequently
        setInterval(function() {
            // First try cached sizes for any new elements
            const needsFitty = applyCachedSizes();
            
            // Only run fitty if we found elements that need it
            if (needsFitty) {
                applyFitty();
            }
        }, 2000);
    </script>"""
    )

    # Create header with full width
    with ui.element("div").classes("w-full"):
        ui_header_label = (
            ui.label(f"{HEADER_TEXT}")
            .classes("fit-header text-center")
            .style(f"font-family: {HEADER_FONT_FAMILY}; color: {HEADER_TEXT_COLOR};")
        )

    # Make the header label available in game_logic module
    from src.core.game_logic import header_label

    header_label = ui_header_label
