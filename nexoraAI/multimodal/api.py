from fastapi import APIRouter, FastAPI, HTTPException

from .analysis import GuardrailViolation, analyze_multimodal_input
from .schemas import AnalyzeInputRequest, AnalyzeInputResponse

router = APIRouter()


@router.post("/analyze-input", response_model=AnalyzeInputResponse)
async def analyze_input(payload: AnalyzeInputRequest) -> AnalyzeInputResponse:
    try:
        return analyze_multimodal_input(payload)
    except GuardrailViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


app = FastAPI(title="NexoraAI Multimodal Intelligence")
app.include_router(router)
