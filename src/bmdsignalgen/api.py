from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
import yaml

from .patterns import PatternType
from .decklink_control import decklink_instance, decklink_bit_depth, create_api_args, generate_and_display_image
import src.bmdsignalgen.decklink_control as decklink_control

router = APIRouter()

class Color(BaseModel):
    r: int = Field(..., ge=0, description="Red component")
    g: int = Field(..., ge=0, description="Green component")
    b: int = Field(..., ge=0, description="Blue component")

class FourColorPatternRequest(BaseModel):
    width: int = 1920
    height: int = 1080
    bit_depth: int = 12
    roi_x: int = 0
    roi_y: int = 0
    roi_width: Optional[int] = None
    roi_height: Optional[int] = None
    colors: List[Color] = Field(..., description="List of 4 RGB colors")

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
            return None, JSONResponse(status_code=400, content={"error": "Invalid JSON or YAML", "details": str(e)})
    try:
        return model(**data), None
    except Exception as e:
        return None, JSONResponse(status_code=422, content={"error": "Invalid pattern parameters", "details": str(e)})

@router.post("/bmd-signal-gen/4color")
async def four_color_pattern(request: Request, body: Any = Body(...)):
    pattern, error = await parse_and_validate_request(request, FourColorPatternRequest)
    if error:
        return error
    if pattern is None:
        return JSONResponse(status_code=400, content={"error": "Pattern validation failed"})
    
    # Check if DeckLink is initialized - use the module reference to ensure we get the current state
    if decklink_control.decklink_instance is None:
        return JSONResponse(status_code=503, content={"error": "DeckLink not initialized"})
    
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
            roi_height=pattern.roi_height
        )
        
        success = generate_and_display_image(api_args, decklink_control.decklink_instance, decklink_control.decklink_bit_depth)
        
        if success:
            return {
                "message": "4-color pattern generated and displayed",
                "shape": f"{pattern.width}x{pattern.height}",
                "colors": color_tuples
            }
        else:
            return JSONResponse(status_code=500, content={"error": "Pattern generation failed"})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Pattern generation failed", "details": str(e)}) 