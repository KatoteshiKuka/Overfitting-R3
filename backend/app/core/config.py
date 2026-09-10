from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurazione applicativa, sovrascrivibile da .env o variabili d'ambiente."""

    model_config = SettingsConfigDict(env_prefix="HEALTHPULSE_", env_file=".env", extra="ignore")

    app_name: str = "HealthPulse"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    data_dir: Path = BACKEND_ROOT.parent / "data"
    # Percorso assoluto: con `sqlite:///./…` il database finisce nella cartella da cui si
    # lancia il comando, quindi avviare il server da un punto diverso creava un secondo
    # database vuoto senza dire niente, oppure ne apriva uno non scrivibile.
    database_url: str = f"sqlite:///{BACKEND_ROOT / 'healthpulse.db'}"
    auto_seed: bool = True

    # Durata della sessione di accesso: coprire una giornata di demo senza rifare login.
    session_hours: int = 8

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
    user_agent: str = "HealthPulse/0.1 (hackathon project)"

    @property
    def facilities_dir(self) -> Path:
        return self.resolved_data_dir / "facilities"

    @property
    def congestion_dir(self) -> Path:
        return self.resolved_data_dir / "congestion"

    @property
    def resolved_data_dir(self) -> Path:
        # I path relativi in .env sono relativi a backend/, non alla cwd di chi lancia il processo.
        if self.data_dir.is_absolute():
            return self.data_dir
        return (BACKEND_ROOT / self.data_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
