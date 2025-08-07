from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Manages application configuration using environment variables.
    """
    # OpenAI Compatible API Settings
    AI_PROVIDER: str = Field(default="openai", description="The AI provider to use ('openai' or 'vertexai').")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(..., env="OPENAI_BASE_URL")

    # Model & Generation Parameters
    MODEL_NAME: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.03
    TOP_P: float = 0.97
    REASONING_EFFORT: str = "disable"
    MAX_COMPLETION_TOKENS: int = 32768

    # Document Preprocessing Settings
    TARGET_DPI: int = 200
    DEFAULT_DPI: int = 72
    SMALL_ANGLE_THRESHOLD: float = 2.0
    DEFAULT_IMAGE_FORMAT: str = "png"
    SHARPEN_CONTRAST_ALPHA: float = 1.25
    SHARPEN_CONTRAST_BETA: float = 0.0

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR).")
    LOG_FILE_PATH: str = Field(default="logs/document_processor.log", description="Path to the log file.")
    LOG_ROTATION_MAX_BYTES: int = Field(default=10485760, description="Max log file size in bytes before rotation (10MB).")
    LOG_ROTATION_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files to keep.")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a single, importable instance of the settings
settings = Settings()