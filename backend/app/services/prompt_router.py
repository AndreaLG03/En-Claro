from pathlib import Path
import logging
from typing import Tuple, Optional
from ..models.enums import AnalysisModule

logger = logging.getLogger(__name__)

# Base path for prompts
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts"

def load_prompt(name: str) -> str:
    """Loads a prompt file from the prompts directory."""
    file_path = PROMPT_PATH / name
    if not file_path.exists():
        logger.error(f"Prompt file not found: {file_path}")
        raise FileNotFoundError(f"Prompt file {name} not found.")
    return file_path.read_text(encoding="utf-8")

# Mapping of module to prompt file
PROMPT_MAPPING = {
    AnalysisModule.MESSAGE: "message_interpretation.txt",
    AnalysisModule.AUDIO: "audio_interpretation.txt",
    AnalysisModule.GLOSSARY: "metaphor_glossary.txt",
    AnalysisModule.RESPONSE: "response_helper.txt",
    AnalysisModule.ROUTINE: "routine_planner.txt",
    AnalysisModule.DECODER: "decoder.txt",
    AnalysisModule.ROLEPLAY: "roleplay.txt",
    AnalysisModule.ROLEPLAY_FEEDBACK: "roleplay_feedback.txt",
    AnalysisModule.TRANSLATOR: "translator.txt"
}

# Mapping of module to user prompt formatting
USER_PROMPT_TEMPLATES = {
    AnalysisModule.MESSAGE: "Analiza el siguiente mensaje:\n\n{text}",
    AnalysisModule.AUDIO: "Analiza la siguiente transcripción de audio:\n\n{text}",
    AnalysisModule.GLOSSARY: "Explica la siguiente expresión:\n\n{text}",
    AnalysisModule.RESPONSE: "Ayúdame a responder al siguiente mensaje:\n\n{text}",
    AnalysisModule.ROUTINE: "Ayúdame a crear una rutina con estos datos:\n\n{text}",
    AnalysisModule.DECODER: "Analiza el subtexto y tono de este mensaje:\n\n{text}",
    AnalysisModule.ROLEPLAY: "Historial de conversación:\n\n{text}",
    AnalysisModule.ROLEPLAY_FEEDBACK: "Proporciona feedback sobre esta conversación:\n\n{text}",
    AnalysisModule.TRANSLATOR: "Desglosa literalmente la siguiente expresión:\n\n{text}"
}

def get_prompts(module: str, text: str) -> Tuple[str, str]:
    """
    Returns the system prompt and formatted user prompt for a given module.
    """
    try:
        module_enum = AnalysisModule(module)
    except ValueError:
        raise ValueError(f"Módulo no válido: {module}")

    system_prompt = load_prompt(PROMPT_MAPPING[module_enum])
    user_template = USER_PROMPT_TEMPLATES.get(module_enum, "{text}")
    
    # Use replace to avoid Issues with curly braces in the input text (e.g. JSON)
    formatted_user_prompt = user_template.replace("{text}", text)
    
    return system_prompt, formatted_user_prompt
