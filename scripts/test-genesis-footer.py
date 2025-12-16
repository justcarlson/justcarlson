#!/usr/bin/env python3
"""
Test script for add-genesis-footer.py

Validates:
1. Animation duration extraction
2. CSS keyframes injection
3. Text left-alignment with grid
4. SVG structure integrity
5. Duplicate prevention
"""

import sys
import tempfile
from pathlib import Path

# Import the module under test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "add_genesis_footer",
    Path(__file__).parent / "add-genesis-footer.py"
)
add_genesis_footer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_genesis_footer_module)

extract_animation_duration = add_genesis_footer_module.extract_animation_duration
find_grid_bounds = add_genesis_footer_module.find_grid_bounds
parse_viewbox = add_genesis_footer_module.parse_viewbox
add_genesis_footer = add_genesis_footer_module.add_genesis_footer


def create_mock_snake_svg(duration_ms: int = 82100) -> str:
    """Create a minimal snake SVG for testing."""
    return f'''<svg viewBox="0 0 880 180" width="880" height="180" xmlns="http://www.w3.org/2000/svg">
  <style>.c{{animation:none {duration_ms}ms linear infinite}}</style>
  <rect class="c" x="16" y="26" width="12" height="12"/>
  <rect class="c" x="832" y="110" width="12" height="12"/>
</svg>'''


def test_extract_animation_duration():
    """Test animation duration extraction."""
    # Test with explicit duration
    svg = create_mock_snake_svg(75000)
    duration = extract_animation_duration(svg)
    assert duration == 75000, f"Expected 75000, got {duration}"
    
    # Test with default fallback (no animation)
    svg_no_animation = '<svg><rect/></svg>'
    duration = extract_animation_duration(svg_no_animation)
    assert duration == 82100, f"Expected fallback 82100, got {duration}"
    
    print("  Animation duration extraction works")


def test_find_grid_bounds():
    """Test grid bounds detection."""
    svg = create_mock_snake_svg()
    bounds = find_grid_bounds(svg)
    assert bounds == (16, 844), f"Expected (16, 844), got {bounds}"
    
    # Test with no rects
    svg_no_rects = '<svg></svg>'
    bounds = find_grid_bounds(svg_no_rects)
    assert bounds is None, f"Expected None, got {bounds}"
    
    print("  Grid bounds detection works")


def test_parse_viewbox():
    """Test viewBox parsing."""
    svg = create_mock_snake_svg()
    viewbox = parse_viewbox(svg)
    assert viewbox == (0, 0, 880, 180), f"Expected (0, 0, 880, 180), got {viewbox}"
    
    print("  ViewBox parsing works")


def test_full_integration():
    """Test full footer addition."""
    svg_content = create_mock_snake_svg(82100)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = Path(f.name)
    
    try:
        add_genesis_footer(temp_path, 'dark')
        result = temp_path.read_text()
        
        # Validate output
        assert '@keyframes genesis-reveal' in result, "Missing keyframes"
        assert 'animation: genesis-reveal 82100ms' in result, "Wrong animation duration"
        assert 'class="genesis-block"' in result, "Missing genesis-block class"
        assert 'clip-path: inset(0 100% 0 0)' in result, "Missing clip-path start"
        assert 'clip-path: inset(0 0% 0 0)' in result, "Missing clip-path end"
        
        # Validate left-alignment (x should be 16, the grid left edge)
        assert 'x="16"' in result, "Footer not left-aligned with grid"
        
        print("  Full integration test passed")
    finally:
        temp_path.unlink()


def test_duplicate_prevention():
    """Test that running script twice doesn't add duplicate footer."""
    svg_content = create_mock_snake_svg(82100)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = Path(f.name)
    
    try:
        # Run once
        add_genesis_footer(temp_path, 'dark')
        first_result = temp_path.read_text()
        first_count = first_result.count('class="genesis-block"')
        
        # Run again
        add_genesis_footer(temp_path, 'dark')
        second_result = temp_path.read_text()
        second_count = second_result.count('class="genesis-block"')
        
        assert first_count == 1, f"Expected 1 genesis-block after first run, got {first_count}"
        assert second_count == 1, f"Expected 1 genesis-block after second run, got {second_count}"
        
        print("  Duplicate prevention works")
    finally:
        temp_path.unlink()


def main():
    """Run all tests."""
    print("Running genesis footer tests...\n")
    
    test_extract_animation_duration()
    test_find_grid_bounds()
    test_parse_viewbox()
    test_full_integration()
    test_duplicate_prevention()
    
    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
