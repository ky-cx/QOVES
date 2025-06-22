from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import base64

class LandmarkPoint(BaseModel):
    x: float
    y: float

class CropSubmitRequest(BaseModel):
    image: str  # base64 encoded
    landmarks: List[LandmarkPoint]
    segmentation_map: str  # base64 encoded
    
    class Config:
        # This is an older syntax for Pydantic v1, for v2 it's handled by default
        # but leaving it here won't cause harm.
        orm_mode = True

class JobResponse(BaseModel):
    id: str
    status: str

class CropResult(BaseModel):
    svg: str  # base64 encoded SVG
    mask_contours: Dict[str, List[List[Dict[str, float]]]]

class ErrorResponse(BaseModel):
    detail: str
    error_code: str