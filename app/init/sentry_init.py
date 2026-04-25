import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config.app_config import AppConfig

from app.models.enums.app_environment import AppEnvironment


class SentryInitializer:
    """
    Initializes Sentry error tracking with Flask integration.
    Maps application environment to Sentry environment names.
    """

    @classmethod
    def get_parsed_sentry_env(cls) -> str:
        """
        Maps the application environment setting to a Sentry-compatible environment name.

        Returns:
            str: The Sentry environment string.
        """
        environment_map = {
            AppEnvironment.DEV.value: "development",
            AppEnvironment.STAGING.value: "staging",
            AppEnvironment.PROD.value: "production",
        }

        return environment_map.get(AppConfig.APP_ENVIRONMENT)

    @classmethod
    def initialize(cls) -> None:
        """Initializes the Sentry SDK with the configured DSN and environment."""

        sentry_sdk.init(
            dsn=AppConfig.SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            send_default_pii=True,
            attach_stacktrace=True,
            max_request_body_size="always",
            environment=cls.get_parsed_sentry_env(),
            _experiments={
                "continuous_profiling_auto_start": True,
            },
        )
