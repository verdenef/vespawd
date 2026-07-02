"""Default configuration values."""

from vedaws.config.schema import (
    LoggingConfig,
    PluginsConfig,
    RuntimeConfig,
    SecurityConfig,
    VedawsConfig,
    WorkersConfig,
)


def default_config() -> VedawsConfig:
    return VedawsConfig(
        logging=LoggingConfig(level="INFO", file=None),
        plugins=PluginsConfig(enabled=True, search_paths=[]),
        workers=WorkersConfig(enabled=True, search_paths=[]),
        runtime=RuntimeConfig(name="vedaws"),
        security=SecurityConfig(allow_env_secrets=True, allow_file_secrets=False),
    )
