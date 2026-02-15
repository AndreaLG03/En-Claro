import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.schemas import TextRequest, AIResponse
from ..models.db import get_db, User, AnalysisHistory
from ..services.prompt_router import get_prompts
from ..services.claude_client import call_claude

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=AIResponse)
async def analyze_text(request: TextRequest, db: Session = Depends(get_db)):
    """
    Analyzes text using the specified module.
    Delegates prompt formatting to the prompt_router and calls Claude API.
    """
    MAX_INPUT_LENGTH = 15000 # Increased for roleplay history
    
    # --- PREMIUM LOGIC START ---
    # Hardcoded list for MVP. In production, this would be a DB check.
    PREMIUM_USERS = [
        "andrealan2003@gmail.com"
    ]
    
    # Check for Premium Scenarios
    is_premium_scenario = False
    if request.module == 'roleplay' and request.scenario_context:
        # Check for explicit flag in context (sent from frontend)
        if request.scenario_context.get('is_premium', False):
            is_premium_scenario = True
            
    if is_premium_scenario:
        user_email = request.user_email
        if not user_email or user_email not in PREMIUM_USERS:
            # Rejection
            raise HTTPException(
                status_code=403, 
                detail="Esta función es exclusiva para usuarios Premium ⭐. Actualiza tu cuenta para acceder."
            )
    # --- PREMIUM LOGIC END ---

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

        # --- HISTORY SAVING START ---
        if request.user_email:
            try:
                # Find or create user
                user = db.query(User).filter(User.email == request.user_email).first()
                if not user:
                    # Check if they should be premium based on hardcoded list
                    is_premium = request.user_email in PREMIUM_USERS
                    user = User(email=request.user_email, is_premium=is_premium)
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                
                # Save history
                history_item = AnalysisHistory(
                    user_email=user.email,
                    module=request.module,
                    input_text=request.text,
                    result_text=result_text,
                    meta_data=request.scenario_context or {}
                )
                db.add(history_item)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to save history: {e}")
                # Don't fail the request if history saving fails
        # --- HISTORY SAVING END ---

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

@router.get("/history")
def get_history(email: str, db: Session = Depends(get_db)):
    """Fetch analysis history for a specific user email."""
    if not email:
        return []
        
    history = db.query(AnalysisHistory).filter(AnalysisHistory.user_email == email).order_by(AnalysisHistory.timestamp.desc()).limit(50).all()
    return [{
        "id": h.id,
        "module": h.module,
        "input_text": h.input_text,
        "result_text": h.result_text,
        "timestamp": h.timestamp.isoformat(),
        "meta_data": h.meta_data
    } for h in history]
