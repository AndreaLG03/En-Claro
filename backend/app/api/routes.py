import logging
from fastapi import APIRouter, HTTPException
from ..models.schemas import TextRequest, AIResponse
from ..services.prompt_router import get_prompts
from ..services.claude_client import call_claude

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=AIResponse)
async def analyze_text(request: TextRequest):
    """
    Analyzes text using the specified module.
    Delegates prompt formatting to the prompt_router and calls Claude API.
    """
    MAX_INPUT_LENGTH = 15000 # Increased for roleplay history
    if len(request.text) > MAX_INPUT_LENGTH:
        raise HTTPException(status_code=400, detail=f"El texto es demasiado largo (máx {MAX_INPUT_LENGTH} caracteres).")

    try:
        # Get appropriate prompts based on module, injecting profile/context
        system_prompt, user_prompt = get_prompts(
            request.module, 
            request.text,
            user_profile=request.user_profile,
            scenario_context=request.scenario_context
        )
        
        # Call AI service
        result_text = await call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        return AIResponse(result=result_text)

    except ValueError as ve:
        logger.warning(f"Validation error in analyze_text: {str(ve)}")
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        error_msg = str(e)
        logger.exception("Unexpected error during text analysis")
        
        # Friendly translation for common API errors
        friendly_error = "No se pudo analizar el contenido. Por favor, comprueba tu conexión o intenta más tarde."
        if "401" in error_msg or "authentication" in error_msg.lower():
            friendly_error = "Error de autenticación: Verifica tu CLAUDE_API_KEY."
            raise HTTPException(status_code=401, detail=friendly_error)
        elif "429" in error_msg:
            friendly_error = "Límite de mensajes alcanzado. Por favor, espera un momento."
            raise HTTPException(status_code=429, detail=friendly_error)
            
        raise HTTPException(
            status_code=500,
            detail=f"Error técnico: {str(e)}"
        )
