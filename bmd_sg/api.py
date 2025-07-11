from typing import Any, List, Optional

import yaml
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

import bmd_sg.decklink_control as decklink_control
from bmd_sg.decklink_control import create_api_args, generate_and_display_image
from bmd_sg.patterns import PatternType
from bmd_sg.decklink.bmd_decklink import HDRMetadata

router = APIRouter()


class Color(BaseModel):
    r: int = Field(..., ge=0, description="Red component")
    g: int = Field(..., ge=0, description="Green component")
    b: int = Field(..., ge=0, description="Blue component")


class HDRMetadataRequest(BaseModel):
    """Complete HDR metadata request model."""
    eotf: int = Field(3, ge=1, le=3, description="EOTF type (0-7 as per CEA 861.3)")
    max_cll: int = Field(1000, ge=0, description="Maximum Content Light Level in cd/m²")
    max_fall: int = Field(50, ge=0, description="Maximum Frame Average Light Level in cd/m²")
    
    # Display primaries (Rec2020 default values)
    red_x: float = Field(0.708, ge=0.0, le=1.0, description="Red primary X coordinate")
    red_y: float = Field(0.292, ge=0.0, le=1.0, description="Red primary Y coordinate")
    green_x: float = Field(0.170, ge=0.0, le=1.0, description="Green primary X coordinate")
    green_y: float = Field(0.797, ge=0.0, le=1.0, description="Green primary Y coordinate")
    blue_x: float = Field(0.131, ge=0.0, le=1.0, description="Blue primary X coordinate")
    blue_y: float = Field(0.046, ge=0.0, le=1.0, description="Blue primary Y coordinate")
    white_x: float = Field(0.3127, ge=0.0, le=1.0, description="White point X coordinate")
    white_y: float = Field(0.3290, ge=0.0, le=1.0, description="White point Y coordinate")
    
    # Mastering display luminance
    max_display_mastering_luminance: float = Field(1000.0, ge=0.0, description="Max display mastering luminance in cd/m²")
    min_display_mastering_luminance: float = Field(0.0001, ge=0.0, description="Min display mastering luminance in cd/m²")


class FourColorPatternRequest(BaseModel):
    width: int = 1920
    height: int = 1080
    bit_depth: int = 12
    roi_x: int = 0
    roi_y: int = 0
    roi_width: Optional[int] = None
    roi_height: Optional[int] = None
    colors: List[Color] = Field(..., description="List of 4 RGB colors")
    hdr_metadata: Optional[HDRMetadataRequest] = Field(None, description="Complete HDR metadata")

    @validator("colors")
    def check_colors_length(cls, v):
        if len(v) != 4:
            raise ValueError("Exactly 4 colors must be provided")
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


@router.post("/bmd-signal-gen/4color")
async def four_color_pattern(request: Request, body: Any = Body(...)):
    pattern, error = await parse_and_validate_request(request, FourColorPatternRequest)
    if error:
        return error
    if pattern is None:
        return JSONResponse(
            status_code=400, content={"error": "Pattern validation failed"}
        )

    # Check if DeckLink is initialized
    if decklink_control.decklink_instance is None:
        return JSONResponse(
            status_code=503, content={"error": "DeckLink not initialized"}
        )

    # Prepare colors as tuples
    color_tuples = [(c.r, c.g, c.b) for c in pattern.colors]

    # Create API args and call generate function
    try:
        api_args = create_api_args(
            width=pattern.width,
            height=pattern.height,
            pattern=PatternType.FOUR_COLOR,
            colors=color_tuples,
            roi_x=pattern.roi_x,
            roi_y=pattern.roi_y,
            roi_width=pattern.roi_width,
            roi_height=pattern.roi_height,
        )

        # Set complete HDR metadata if provided
        if pattern.hdr_metadata:
            hdr_metadata = HDRMetadata()
            hdr_metadata.EOTF = pattern.hdr_metadata.eotf
            hdr_metadata.maxCLL = float(pattern.hdr_metadata.max_cll)
            hdr_metadata.maxFALL = float(pattern.hdr_metadata.max_fall)
            hdr_metadata.referencePrimaries.RedX = pattern.hdr_metadata.red_x
            hdr_metadata.referencePrimaries.RedY = pattern.hdr_metadata.red_y
            hdr_metadata.referencePrimaries.GreenX = pattern.hdr_metadata.green_x
            hdr_metadata.referencePrimaries.GreenY = pattern.hdr_metadata.green_y
            hdr_metadata.referencePrimaries.BlueX = pattern.hdr_metadata.blue_x
            hdr_metadata.referencePrimaries.BlueY = pattern.hdr_metadata.blue_y
            hdr_metadata.referencePrimaries.WhiteX = pattern.hdr_metadata.white_x
            hdr_metadata.referencePrimaries.WhiteY = pattern.hdr_metadata.white_y
            hdr_metadata.maxDisplayMasteringLuminance = pattern.hdr_metadata.max_display_mastering_luminance
            hdr_metadata.minDisplayMasteringLuminance = pattern.hdr_metadata.min_display_mastering_luminance
            
            decklink_control.decklink_instance.set_hdr_metadata(hdr_metadata)

        success = generate_and_display_image(
            api_args,
            decklink_control.decklink_instance,
            decklink_control.decklink_bit_depth,
        )

        if success:
            return {
                "message": "4-color pattern generated and displayed",
                "shape": f"{pattern.width}x{pattern.height}",
                "colors": color_tuples,
                "hdr_metadata": pattern.hdr_metadata.dict() if pattern.hdr_metadata else None,
            }
        else:
            return JSONResponse(
                status_code=500, content={"error": "Pattern generation failed"}
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Pattern generation failed", "details": str(e)},
        )
