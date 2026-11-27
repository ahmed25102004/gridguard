import importlib
import sys
import types
from pathlib import Path

# Add 'ai-service' directory to sys.path so 'src' can be imported cleanly
AI_SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

# Map 'ai_service' module alias to allow imports like 'from ai_service.src...'
import src
if "ai_service" not in sys.modules:
    ai_mod = types.ModuleType("ai_service")
    ai_mod.src = src
    sys.modules["ai_service"] = ai_mod
    sys.modules["ai_service.src"] = src

    # Also map all direct submodules
    for sub in ["config", "main", "vector_store", "schemas", "embeddings", "prompts"]:
        try:
            m = importlib.import_module(f"src.{sub}")
            setattr(ai_mod, sub, m)
            sys.modules[f"ai_service.src.{sub}"] = m
        except Exception:
            pass
