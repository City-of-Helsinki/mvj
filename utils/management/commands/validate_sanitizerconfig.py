import sys
from typing import Any, Optional, Union

import yaml
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "Validates the database sanitizer configuration file against defined Django models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--silent",
            action="store_true",
            help="Only output final result, errors, and return non-zero exit code if issues found",
        )

    def handle(self, *args, **options) -> None:
        config_file = ".sanitizerconfig"
        ignored_apps = ["admin", "contenttypes", "sessions"]
        ignored_models = []
        silent = options["silent"]

        config = self._load_config(config_file)
        if not config:
            sys.exit(1)

        # Extract models from config and Django
        config_models = self._extract_config_models(config)
        django_models = self._extract_django_models(
            ignored_apps, ignored_models, silent
        )

        # Validate config
        exit_code = self._validate_config(config_models, django_models)
        if exit_code != 0:
            sys.exit(exit_code)

    def _load_config(self, config_file: str) -> Optional[dict[str, Any]]:
        """Load sanitizer config from file and validate basic structure."""
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Config file not found: {config_file}"))
            return None
        except yaml.YAMLError as e:
            self.stderr.write(self.style.ERROR(f"Error parsing YAML: {e}"))
            return None

        if not config or "strategy" not in config:
            self.stderr.write(
                self.style.ERROR("Invalid config: 'strategy' section missing")
            )
            return None

        return config

    def _extract_config_models(
        self, config: dict[str, Any]
    ) -> dict[str, Union[str, set[str]]]:
        """Extract models and fields from config file."""
        config_models: dict[str, Union[str, set[str]]] = {}
        for model_name, fields in config["strategy"].items():
            if fields == "skip_rows":
                config_models[model_name] = "skip_rows"
            else:
                config_models[model_name] = set(fields.keys())

        return config_models

    def _extract_django_models(
        self,
        ignored_apps: list[str],
        ignored_models: list[str],
        silent: bool,
    ) -> dict[str, set[str]]:
        """Extract models and fields from Django applications."""
        django_models: dict[str, set[str]] = {}

        # System models to ignore
        system_models = [
            "authtoken_tokenproxy",
            "django_q_failure",
            "django_q_success",
            "gis_postgisgeometrycolumns",
            "gis_postgisspatialrefsys",
        ]

        for app_config in apps.get_app_configs():
            app_name = app_config.label

            # Skip ignored apps
            if app_name in ignored_apps:
                if not silent:
                    self.stdout.write(f"Ignoring app: {app_name}")
                continue

            # Process models for this app
            app_models = self._extract_app_models(
                app_config, app_name, ignored_models, system_models, silent
            )
            django_models.update(app_models)

        return django_models

    def _extract_app_models(
        self,
        app_config,
        app_name: str,
        ignored_models: list[str],
        system_models: list[str],
        silent: bool,
    ) -> dict[str, set[str]]:
        """Extract models and their fields for a single app."""
        app_models = {}

        for model in app_config.get_models():
            model_name = f"{app_name}_{model.__name__.lower()}"
            model_dotted = f"{app_name}.{model.__name__}"

            if self._should_ignore_model(
                model_name, model_dotted, model, ignored_models, system_models, silent
            ):
                continue

            # Extract fields for this model
            fields = self._extract_model_fields(model)
            app_models[model_name] = fields

        return app_models

    def _should_ignore_model(
        self,
        model_name: str,
        model_dotted: str,
        model,
        ignored_models: list[str],
        system_models: list[str],
        silent: bool,
    ) -> bool:
        """Determine if a model should be ignored in validation."""
        # Skip specific models if in ignored list
        if model_dotted in ignored_models:
            if not silent:
                self.stdout.write(f"Ignoring model: {model_name}")
            return True

        # Skip system models
        if model_name in system_models:
            if not silent:
                self.stdout.write(f"Ignoring system model: {model_name}")
            return True

        # Skip models that don't have their own database table
        if getattr(model._meta, "managed", True) is False:
            if not silent:
                self.stdout.write(f"Ignoring unmanaged model: {model_name}")
            return True

        # Skip proxy models
        if getattr(model._meta, "proxy", False):
            if not silent:
                self.stdout.write(f"Ignoring proxy model: {model_name}")
            return True

        return False

    def _extract_model_fields(self, model) -> set[str]:
        """Extract fields from a Django model."""
        fields = set()

        for field in model._meta.get_fields():
            # Skip fields that shouldn't be included
            if self._should_skip_field(field):
                continue

            # Get field name (with _id suffix for foreign keys)
            field_name = self._get_field_name(field)
            fields.add(field_name)

        return fields

    def _should_skip_field(self, field) -> bool:
        """Determine if a field should be skipped in validation."""
        # Skip auto-created fields
        if getattr(field, "auto_created", False):
            return True

        # Skip many-to-many fields
        if isinstance(field, models.ManyToManyField) or isinstance(
            field, models.ManyToManyRel
        ):
            return True

        # Skip generic relation fields
        if hasattr(field, "is_relation") and field.is_relation:
            if hasattr(field, "related_model") and field.related_model is None:
                return True

        # Skip fields without a column (like GenericForeignKey)
        if hasattr(field, "column") and field.column is None:
            return True

        return False

    def _get_field_name(self, field) -> str:
        """Get the appropriate field name, handling foreign keys."""
        field_name = field.name
        if isinstance(field, models.ForeignKey):
            field_name = f"{field.name}_id"
        return field_name

    def _validate_config(
        self,
        config_models: dict[str, Union[str, set[str]]],
        django_models: dict[str, set[str]],
    ) -> int:
        """Validate config against Django models and report issues."""
        # Check for models missing in config
        missing_in_config = set(django_models.keys()) - set(config_models.keys())

        # Check for fields missing in config for each model
        field_issues = self._get_missing_fields(django_models, config_models)

        # Output results
        return self._report_validation_results(missing_in_config, field_issues)

    def _get_missing_fields(
        self,
        django_models: dict[str, set[str]],
        config_models: dict[str, Union[str, set[str]]],
    ) -> list[tuple[str, set[str]]]:
        """Find fields missing in config for each model."""
        field_issues: list[tuple[str, set[str]]] = []

        for model_name, fields in django_models.items():
            missing_fields = self._check_model_missing_fields(
                model_name, fields, config_models
            )
            if missing_fields:
                field_issues.append((model_name, missing_fields))

        return field_issues

    def _check_model_missing_fields(
        self,
        model_name: str,
        fields: set[str],
        config_models: dict[str, Union[str, set[str]]],
    ) -> set[str]:
        """Check for missing fields for a single model."""
        # Skip models not in config or with skip_rows strategy
        if model_name not in config_models or config_models[model_name] == "skip_rows":
            return set()

        # Find fields in Django model but missing in config
        missing_fields = set()
        for field in fields:
            if field not in config_models[model_name]:  # type: ignore
                missing_fields.add(field)

        return missing_fields

    def _report_validation_results(
        self,
        missing_in_config: set[str],
        field_issues: list[tuple[str, set[str]]],
    ) -> int:
        """Report validation results and return exit code."""
        has_issues = False

        if missing_in_config:
            has_issues = True
            self.stdout.write(
                self.style.WARNING(
                    f"Models missing in config: {len(missing_in_config)}"
                )
            )
            for model in sorted(missing_in_config):
                self.stdout.write(f"  - {model}")

        if field_issues:
            has_issues = True
            self.stdout.write(
                self.style.WARNING(
                    f"Models with fields missing in config: {len(field_issues)}"
                )
            )
            for model_name, fields in field_issues:
                self.stdout.write(f"  - {model_name}: {', '.join(sorted(fields))}")

        if not has_issues:
            self.stdout.write(self.style.SUCCESS("Sanitizer config is up to date!"))
            return 0
        else:
            self.stderr.write(self.style.ERROR("Sanitizer config validation failed!"))
            return 1
