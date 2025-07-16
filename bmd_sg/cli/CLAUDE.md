# CLI Module Development Guide

## Architecture Patterns

- Global callback pattern with Typer context (`ctx.obj`)
- Commands inherit configuration via `setup_tools_from_context(ctx)`
- Use rich help panels: `"Device / Pixel Format"`, `"ROI"`, `"HDR Metadata"`,
  `"Pattern Options"`

## Standard Command Structure

```python
def pattern_command(ctx: typer.Context, duration: float = 5.0) -> None:
    """Brief description with NumPy docstring format."""
    tools = setup_tools_from_context(ctx)
    pattern_data = tools.pattern_generator.create_pattern(...)
    tools.decklink.display_frame_with_duration(pattern_data, duration)
```

## Key Patterns

- **Parameter validation**:
  `validate_color(color_value, tools.decklink.get_bit_depth())`
- **Error handling**: Use `typer.echo(f"Error: {e}", err=True)` and
  `typer.Exit(1)`
- **Mock support**: Handled automatically by `setup_tools_from_context()`
- **Registration**: Add to `main.py` with `app.command("name")(function)`

## Option Groups

Use when 3+ options and 2+ logical groups exist. Standard panels above cover
most cases.

## Testing

Check if there are any physical devices connect for real and test using them.

```bash
uv run python -m bmd_sg.cli.main command --duration 2.0
```

If no hardware devices are available, you may test with the mock-device:

```bash
uv run python -m bmd_sg.cli.main --mock-device command --duration 2.0
```
