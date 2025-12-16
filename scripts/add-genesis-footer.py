#!/usr/bin/env python3
"""
Add Bitcoin Genesis Block hex dump footer to Platane/snk SVG output.

Usage:
    python3 add-genesis-footer.py <svg_file> <light|dark>

The script modifies the SVG in-place, adding a centered hex dump footer
showing the famous "The Times 03/Jan/2009" message from the genesis block.
"""

import sys
import re
from pathlib import Path

# Genesis block hex dump - the section containing Satoshi's message
GENESIS_HEX_DUMP = [
    ("00000080", "01 04 45 54 68 65 20 54 69 6D 65 73 20 30 33 2F", "..EThe Times 03/"),
    ("00000090", "4A 61 6E 2F 32 30 30 39 20 43 68 61 6E 63 65 6C", "Jan/2009 Chancel"),
    ("000000A0", "6C 6F 72 20 6F 6E 20 62 72 69 6E 6B 20 6F 66 20", "lor on brink of "),
    ("000000B0", "73 65 63 6F 6E 64 20 62 61 69 6C 6F 75 74 20 66", "second bailout f"),
    ("000000C0", "6F 72 20 62 61 6E 6B 73 FF FF FF FF 01 00 F2 05", "or banksÿÿÿÿ..ò."),
]

# Colors - same for both light and dark modes
COLORS = {
    "addr": "#565f89",   # Muted Tokyo Night gray
    "hex": "#a9b1d6",    # Tokyo Night text
    "ascii": "#F7931A",  # Bitcoin orange
}

# Layout constants
FONT_SIZE = 9
LINE_HEIGHT = 11
TOP_PADDING = 10
BOTTOM_PADDING = 5


def parse_viewbox(svg_content: str) -> tuple:
    """Extract viewBox dimensions from SVG (min_x, min_y, width, height)."""
    match = re.search(r'viewBox="([^"]+)"', svg_content)
    if not match:
        raise ValueError("No viewBox found in SVG")
    
    parts = match.group(1).split()
    return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))


def find_grid_center(svg_content: str) -> float:
    """Find the center of the contribution grid by looking at rect elements."""
    # Find all x positions of rect elements (contribution cells)
    x_matches = re.findall(r'<rect[^>]*\sx="(\d+)"', svg_content)
    if not x_matches:
        return 424.0  # Default fallback
    
    x_values = [int(x) for x in x_matches]
    min_x = min(x_values)
    max_x = max(x_values) + 12  # Add cell width (12px)
    
    return (min_x + max_x) / 2


def find_grid_bounds(svg_content: str) -> tuple:
    """Find the actual contribution grid bounds by looking at rect elements."""
    # Find all x positions of rect elements (contribution cells)
    x_matches = re.findall(r'<rect[^>]*\sx="(\d+)"', svg_content)
    if not x_matches:
        return None
    
    x_values = [int(x) for x in x_matches]
    min_x = min(x_values)
    max_x = max(x_values) + 12  # Add cell width (12px)
    
    return (min_x, max_x)


def extract_animation_duration(svg_content: str) -> int:
    """
    Extract animation duration from snake SVG CSS.
    
    Platane/snk uses format: animation: none <duration>ms linear infinite
    Example: animation: none 82100ms linear infinite
    
    Returns duration in milliseconds, or 82100 as fallback.
    """
    match = re.search(r'animation:\s*none\s+(\d+)ms', svg_content)
    if match:
        return int(match.group(1))
    return 82100  # Default fallback


def update_viewbox(svg_content: str, new_height: float) -> str:
    """Update the viewBox height in the SVG."""
    def replace_viewbox(match):
        parts = match.group(1).split()
        parts[3] = str(int(new_height))
        return f'viewBox="{" ".join(parts)}"'
    
    return re.sub(r'viewBox="([^"]+)"', replace_viewbox, svg_content)


def update_height_attr(svg_content: str, new_height: float) -> str:
    """Update the height attribute in the SVG root tag only."""
    # Match <svg ... height="X" ...> - only in the opening svg tag
    def replace_in_svg_tag(match):
        svg_tag = match.group(0)
        return re.sub(r'height="[^"]+"', f'height="{int(new_height)}"', svg_tag)
    
    return re.sub(r'<svg[^>]+>', replace_in_svg_tag, svg_content, count=1)


def generate_hex_dump_svg(grid_left_x: float, start_y: float, duration_ms: int) -> str:
    """Generate SVG elements for the animated hex dump footer."""
    lines = []
    
    # Add style for the hex dump with reveal animation
    style = f'''
  <style type="text/css">
    @keyframes genesis-reveal {{
      0%, 5% {{ clip-path: inset(0 100% 0 0); }}
      95%, 100% {{ clip-path: inset(0 0% 0 0); }}
    }}
    .genesis-block {{
      animation: genesis-reveal {duration_ms}ms linear infinite;
    }}
    .genesis-line {{
      font-family: 'Courier New', Courier, monospace;
      font-size: {FONT_SIZE}px;
      white-space: pre;
    }}
    .genesis-addr {{ fill: {COLORS["addr"]}; }}
    .genesis-hex {{ fill: {COLORS["hex"]}; }}
    .genesis-ascii {{ fill: {COLORS["ascii"]}; }}
  </style>'''
    lines.append(style)
    
    # Create a group for the hex dump, left-aligned with grid
    lines.append('  <g class="genesis-block">')
    
    # Calculate positions for each column (left-aligned with grid)
    char_width = 5.4  # approximate width of monospace char at 9px
    start_x = int(grid_left_x)
    
    addr_x = start_x
    hex_x = start_x + int(10 * char_width)  # after "00000080  "
    ascii_x = start_x + int(59 * char_width)  # after hex bytes + spacing
    
    for i, (addr, hex_bytes, ascii_text) in enumerate(GENESIS_HEX_DUMP):
        y = int(start_y + (i * LINE_HEIGHT))
        
        # Use separate text elements for each column with fixed positions
        lines.append(f'    <text class="genesis-line genesis-addr" x="{addr_x}" y="{y}">{addr}</text>')
        lines.append(f'    <text class="genesis-line genesis-hex" x="{hex_x}" y="{y}">{hex_bytes}</text>')
        lines.append(f'    <text class="genesis-line genesis-ascii" x="{ascii_x}" y="{y}">{ascii_text}</text>')
    
    lines.append('  </g>')
    
    return '\n'.join(lines)


def add_genesis_footer(svg_path: Path, mode: str) -> None:
    """Add animated genesis block hex dump footer to SVG file."""
    # Read the SVG content
    svg_content = svg_path.read_text(encoding='utf-8')
    
    # Check if genesis block already exists (prevent duplicates)
    if 'class="genesis-block"' in svg_content:
        print(f"Genesis block already exists in {svg_path}, skipping")
        return
    
    # Parse current viewBox
    min_x, min_y, width, height = parse_viewbox(svg_content)
    
    # Extract animation duration from existing snake CSS
    duration_ms = extract_animation_duration(svg_content)
    
    # Calculate new dimensions
    footer_height = TOP_PADDING + (len(GENESIS_HEX_DUMP) * LINE_HEIGHT) + BOTTOM_PADDING
    new_height = height + footer_height
    
    # Find grid bounds for left-alignment
    grid_bounds = find_grid_bounds(svg_content)
    if grid_bounds is None:
        grid_left_x = 0  # Fallback
    else:
        grid_left_x = grid_bounds[0]  # Left edge of grid
    
    start_y = min_y + height + TOP_PADDING + FONT_SIZE  # +FONT_SIZE because text y is baseline
    
    # Generate the hex dump SVG elements
    hex_dump_svg = generate_hex_dump_svg(grid_left_x, start_y, duration_ms)
    
    # Update viewBox and height attribute
    svg_content = update_viewbox(svg_content, new_height)
    svg_content = update_height_attr(svg_content, new_height)
    
    # Insert the hex dump before the closing </svg> tag
    svg_content = svg_content.replace('</svg>', f'{hex_dump_svg}\n</svg>')
    
    # Write the modified SVG
    svg_path.write_text(svg_content, encoding='utf-8')
    
    print(f"Added genesis block footer to {svg_path} ({mode} mode)")
    print(f"  Original height: {height}, New height: {new_height}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <svg_file> <light|dark>")
        sys.exit(1)
    
    svg_path = Path(sys.argv[1])
    mode = sys.argv[2].lower()
    
    if mode not in ('light', 'dark'):
        print(f"Error: mode must be 'light' or 'dark', got '{mode}'")
        sys.exit(1)
    
    if not svg_path.exists():
        print(f"Error: SVG file not found: {svg_path}")
        sys.exit(1)
    
    try:
        add_genesis_footer(svg_path, mode)
    except Exception as e:
        print(f"Error processing SVG: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
