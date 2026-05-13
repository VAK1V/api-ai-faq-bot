"""ML service for loading and running the GGUF model."""
import os
import time
from typing import Optional
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from app.config import get_settings
from app.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# Global model instance
_llm: Optional[Llama] = None


def get_model_path() -> str:
    """Get or download the GGUF model file."""
    cache_dir = "/app/models"
    os.makedirs(cache_dir, exist_ok=True)

    model_path = os.path.join(cache_dir, settings.model_file)

    if not os.path.exists(model_path):
        logger.info(f"Downloading model {settings.model_repo}/{settings.model_file}...")
        model_path = hf_hub_download(
            repo_id=settings.model_repo,
            filename=settings.model_file,
            local_dir=cache_dir,
            local_dir_use_symlinks=False,
        )
        logger.info(f"Model downloaded to {model_path}")
    else:
        logger.info(f"Using cached model at {model_path}")

    return model_path


def download_model() -> None:
    """Download model during build/startup."""
    get_model_path()


def load_model() -> Llama:
    """Load the GGUF model into memory."""
    global _llm

    if _llm is not None:
        return _llm

    model_path = get_model_path()

    logger.info(f"Loading model {settings.model_file} with {settings.n_threads} threads...")
    start_time = time.time()

    try:
        _llm = Llama(
            model_path=model_path,
            n_ctx=settings.n_ctx,
            n_threads=settings.n_threads,
            n_gpu_layers=0,  # CPU only for college computers
            verbose=False,
        )
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")

    return _llm


def generate_answer(question: str) -> tuple[str, float]:
    """Generate an answer to the given question.

    Returns:
        tuple: (generated_text, processing_time_ms)
    """
    llm = load_model()

    # Build chat prompt for T-lite-it-2.1 (Qwen-based format)
    system_prompt = (
        "Ты — полезный AI ассистент. Отвечай кратко, по существу и на русском языке. "
        "Если не знаешь ответ, честно скажи об этом."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    start_time = time.time()

    try:
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            stop=["<|im_end|>", "<|endoftext|>"],
        )

        processing_time = (time.time() - start_time) * 1000

        generated_text = output["choices"][0]["message"]["content"].strip()

        logger.info(
            f"Generated answer in {processing_time:.0f}ms "
            f"(tokens: {output.get('usage', {}).get('completion_tokens', 'N/A')})"
        )

        return generated_text, processing_time

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise RuntimeError(f"Text generation failed: {e}")


def get_model_info() -> dict:
    """Get information about the loaded model."""
    return {
        "model_name": settings.model_file,
        "repo": settings.model_repo,
        "loaded": _llm is not None,
    }
