"""
Manifest data model for ArrowFlow auto-update system.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class UpdateManifest:
    version: str
    url: str
    sha256: str
    release_date: str = ""
    updater_url: Optional[str] = None
    updater_sha256: Optional[str] = None
    changelog: str = "No release notes available."
    min_supported_version: str = "1.0.0"
    mandatory: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UpdateManifest":
        if not isinstance(data, dict):
            raise ValueError("Manifest payload must be a JSON dictionary.")

        version = str(data.get("version", "")).strip()
        url = str(data.get("url", "")).strip()
        sha256_hash = str(data.get("sha256", "")).strip().lower()

        if not version:
            raise ValueError("Manifest missing required 'version' field.")
        if not url:
            raise ValueError("Manifest missing required 'url' field.")
        if not sha256_hash or len(sha256_hash) != 64:
            raise ValueError("Manifest missing or invalid 64-character hex 'sha256' field.")

        return cls(
            version=version,
            url=url,
            sha256=sha256_hash,
            release_date=str(data.get("release_date", "")),
            updater_url=data.get("updater_url"),
            updater_sha256=data.get("updater_sha256"),
            changelog=str(data.get("changelog", "No release notes available.")),
            min_supported_version=str(data.get("min_supported_version", "1.0.0")),
            mandatory=bool(data.get("mandatory", False)),
            raw_data=data
        )

    @classmethod
    def from_json(cls, json_str: str) -> "UpdateManifest":
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "release_date": self.release_date,
            "url": self.url,
            "sha256": self.sha256,
            "updater_url": self.updater_url,
            "updater_sha256": self.updater_sha256,
            "changelog": self.changelog,
            "min_supported_version": self.min_supported_version,
            "mandatory": self.mandatory,
        }
