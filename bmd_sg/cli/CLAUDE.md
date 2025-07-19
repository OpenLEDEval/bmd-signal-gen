# CLI Module Development Guide

## Architecture Patterns

**Global callback**: Typer context (`ctx.obj`) with `setup_tools_from_context(ctx)`  
**Rich help panels**: `"Device / Pixel Format"`, `"ROI"`, `"HDR Metadata"`, `"Pattern Options"`

## Standard Command Structure

```python
def pattern_command(ctx: typer.Context, duration: float = 5.0) -> None:
    """Brief description with NumPy docstring format."""
    tools = setup_tools_from_context(ctx)
    pattern_data = tools.pattern_generator.create_pattern(...)
    tools.decklink.display_frame_with_duration(pattern_data, duration)
```

## Key Patterns

**Parameter validation**: `validate_color(color_value, tools.decklink.get_bit_depth())`  
**Error handling**: `typer.echo(f"Error: {e}", err=True)` and `typer.Exit(1)`  
**Mock support**: Automatic via `setup_tools_from_context()`  
**Registration**: Add to `main.py` with `app.command("name")(function)`

## Testing

**Hardware**: `uv run python -m bmd_sg.cli.main command --duration 2.0`  
**Mock device**: `uv run python -m bmd_sg.cli.main --mock-device command --duration 2.0`
