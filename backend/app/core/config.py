from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurazione applicativa, sovrascrivibile da .env o variabili d'ambiente."""

    model_config = SettingsConfigDict(env_prefix="PRESIDIO_", env_file=".env", extra="ignore")

    app_name: str = "Presidio Lazio"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    data_dir: Path = BACKEND_ROOT.parent / "data"
    database_url: str = "sqlite:///./presidio.db"
    auto_seed: bool = True

    # Catena LLM: si prova prima il modello locale, poi Groq, poi le regole deterministiche.
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_model: str = "google/gemma-4-e4b"
    llm_timeout_seconds: float = 60.0
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_api_key: str = ""

    # Servizi OpenStreetMap: geocodifica dell'indirizzo e calcolo del tragitto.
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    osrm_url: str = "https://router.project-osrm.org/route/v1/driving"
    geo_timeout_seconds: float = 8.0
    # Nominatim richiede uno user agent identificabile.
    user_agent: str = "PresidioLazio/0.1 (hackathon project)"

    @property
    def facilities_dir(self) -> Path:
        return self.resolved_data_dir / "facilities"

    @property
    def resolved_data_dir(self) -> Path:
        # I path relativi in .env sono relativi a backend/, non alla cwd di chi lancia il processo.
        if self.data_dir.is_absolute():
            return self.data_dir
        return (BACKEND_ROOT / self.data_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
