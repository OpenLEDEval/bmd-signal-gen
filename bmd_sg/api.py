from typing import Any

import yaml
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

import bmd_sg.decklink_control as decklink_control
from bmd_sg.pattern_generator import PatternType
from bmd_sg.signal_generator import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    DeckLinkSettings,
    PatternSettings,
)

router = APIRouter()


class Color(BaseModel):
    r: int = Field(..., ge=0, description="Red component")
    g: int = Field(..., ge=0, description="Green component")
    b: int = Field(..., ge=0, description="Blue component")


class PatternRequest(BaseModel):
    pattern: PatternType = PatternType.SOLID
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None
    colors: list[Color] = Field(..., description="List of 1 to 4 RGB colors")

    @validator("colors")
    def check_colors_length(cls, v, values):
        pattern = values.get("pattern")
        if pattern == PatternType.SOLID and len(v) != 1:
            raise ValueError("Exactly 1 color must be provided for solid pattern")
        if pattern == PatternType.TWO_COLOR and len(v) != 2:
            raise ValueError("Exactly 2 colors must be provided for 2color pattern")
        if pattern == PatternType.FOUR_COLOR and len(v) != 4:
            raise ValueError("Exactly 4 colors must be provided for 4color pattern")
        if len(v) > 4:
            raise ValueError("Maximum of 4 colors are supported")
        return v


async def parse_and_validate_request(request: Request, model):
    try:
        data = await request.json()
    except Exception:
        try:
            raw = await request.body()
            data = yaml.safe_load(raw)
        except Exception as e:
            return None, JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON or YAML", "details": str(e)},
            )
    try:
        return model(**data), None
    except Exception as e:
        return None, JSONResponse(
            status_code=422,
            content={"error": "Invalid pattern parameters", "details": str(e)},
        )


@router.post("/bmd-signal-gen/setup")
async def setup_decklink(request: Request, body: Any = Body(...)):
    decklink_settings, error = await parse_and_validate_request(
        request, DeckLinkSettings
    )
    if error:
        return error
    if decklink_settings is None:
        return JSONResponse(
            status_code=400, content={"error": "DeckLink settings validation failed"}
        )

    success, error = decklink_control.initialize_decklink_for_api()
    if not success:
        return JSONResponse(
            status_code=503,
            content={"error": "DeckLink not initialized", "details": error},
        )

    decklink_control.setup_decklink_device(decklink_settings, 0, None)

    # Store width and height globally for pattern generation
    decklink_control.decklink_width = decklink_settings.width
    decklink_control.decklink_height = decklink_settings.height

    return {"message": "DeckLink device setup complete"}


@router.post("/bmd-signal-gen/pattern")
@router.post("/bmd-signal-gen/display")
async def display_pattern(request: Request, body: Any = Body(...)):
    pattern_request, error = await parse_and_validate_request(request, PatternRequest)
    if error:
        return error
    if pattern_request is None:
        return JSONResponse(
            status_code=400, content={"error": "Pattern settings validation failed"}
        )

    # Check if DeckLink is initialized
    if decklink_control.decklink_instance is None:
        return JSONResponse(
            status_code=503, content={"error": "DeckLink not initialized"}
        )

    # Prepare colors as tuples
    color_tuples = [(c.r, c.g, c.b) for c in pattern_request.colors]

    # Create PatternSettings object
    pattern_settings = PatternSettings(
        pattern=pattern_request.pattern,
        colors=color_tuples,
        roi_x=pattern_request.roi_x,
        roi_y=pattern_request.roi_y,
        roi_width=pattern_request.roi_width,
        roi_height=pattern_request.roi_height,
        bit_depth=decklink_control.decklink_bit_depth,
        width=decklink_control.decklink_width or DEFAULT_WIDTH,
        height=decklink_control.decklink_height or DEFAULT_HEIGHT,
    )

    # Display the pattern
    try:
        success = decklink_control.display_pattern(
            pattern_settings,
            decklink_control.decklink_instance,
        )

        if success:
            return {
                "message": f"{pattern_settings.pattern.value} pattern displayed",
                "shape": f"{pattern_settings.width}x{pattern_settings.height}",
                "colors": pattern_settings.colors,
            }
        else:
            return JSONResponse(
                status_code=500, content={"error": "Pattern display failed"}
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Pattern display failed", "details": str(e)},
        )
