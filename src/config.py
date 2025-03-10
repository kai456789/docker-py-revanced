"""Revanced Configurations."""
from pathlib import Path
from typing import List

from environs import Env
from requests import Session

from src.downloader.sources import apk_sources

default_cli = "https://github.com/revanced/revanced-cli/releases/latest"
default_patches = "https://github.com/revanced/revanced-patches/releases/latest"
default_patches_json = default_patches
default_integrations = (
    "https://github.com/revanced/revanced-integrations/releases/latest"
)


class RevancedConfig(object):
    """Revanced Configurations."""

    def __init__(self, env: Env) -> None:
        from src.utils import default_build

        self.env = env
        self.temp_folder = Path("apks")
        self.session = Session()
        self.session.headers["User-Agent"] = "anything"
        self.ci_test = env.bool("CI_TEST", False)
        self.apps = env.list(
            "PATCH_APPS",
            list(apk_sources.keys()) if self.ci_test else default_build,
        )
        self.rip_libs_apps: List[str] = []
        self.existing_downloaded_apks = env.list("EXISTING_DOWNLOADED_APKS", [])
        self.personal_access_token = env.str("PERSONAL_ACCESS_TOKEN", None)
        self.dry_run = env.bool("DRY_RUN", False)
        self.global_cli_dl = env.str("GLOBAL_CLI_DL", default_cli)
        self.global_patches_dl = env.str("GLOBAL_PATCHES_DL", default_patches)
        self.global_patches_json_dl = env.str(
            "GLOBAL_PATCHES_JSON_DL", default_patches_json
        )
        self.global_integrations_dl = env.str(
            "GLOBAL_INTEGRATIONS_DL", default_integrations
        )
        self.global_keystore_name = env.str(
            "GLOBAL_KEYSTORE_FILE_NAME", "revanced.keystore"
        )
        self.global_archs_to_build = env.list("GLOBAL_ARCHS_TO_BUILD", [])
        self.extra_download_files: List[str] = env.list("EXTRA_FILES", [])
