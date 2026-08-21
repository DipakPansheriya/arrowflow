"""
Firebase Firestore REST Client for ArrowFlow 2FA
Directly communicates with Google Cloud Firestore REST API without requiring heavy native SDKs.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class FirebaseClient:
    PROJECT_ID = "arrowflow-f6b65"
    API_KEY = "AIzaSyAmhc0w2nJkKIx01oIKW3OrEnrh3AmGtCI"
    COLLECTION_ID = "auth_config"
    DOC_ID = "admin_totp"
    TIMEOUT_SECONDS = 8

    def __init__(self, project_id: Optional[str] = None, api_key: Optional[str] = None):
        self.project_id = project_id or self.PROJECT_ID
        self.api_key = api_key or self.API_KEY
        self.base_url = (
            f"https://firestore.googleapis.com/v1/projects/{self.project_id}"
            f"/databases/(default)/documents/{self.COLLECTION_ID}/{self.DOC_ID}?key={self.api_key}"
        )

    def get_authenticator_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the administrator's authenticator configuration from Firebase Firestore.
        Returns:
            dict containing 'secret_key', 'created_at', etc. if document exists,
            or None if the document does not exist (HTTP 404).
        """
        try:
            req = urllib.request.Request(self.base_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    fields = raw_data.get("fields", {})
                    
                    config = {}
                    for k, v in fields.items():
                        if "stringValue" in v:
                            config[k] = v["stringValue"]
                        elif "booleanValue" in v:
                            config[k] = v["booleanValue"]
                        elif "integerValue" in v:
                            config[k] = int(v["integerValue"])
                        elif "timestampValue" in v:
                            config[k] = v["timestampValue"]
                    return config
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Document does not exist yet -> First-time setup required
                return None
            raise RuntimeError(f"Firebase HTTP error ({e.code}): {e.reason}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Unable to connect to Firebase: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Firebase request failed: {str(e)}")
        
        return None

    def save_authenticator_config(self, secret_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Securely save the newly generated authenticator secret key and metadata in Firebase Firestore.
        """
        if not secret_key:
            raise ValueError("Secret key cannot be empty.")

        now_iso = datetime.now(timezone.utc).isoformat()
        
        fields = {
            "secret_key": {"stringValue": str(secret_key)},
            "app_name": {"stringValue": "ArrowFlow"},
            "admin_user": {"stringValue": "admin"},
            "issuer": {"stringValue": "ArrowFlow"},
            "created_at": {"stringValue": now_iso},
            "status": {"stringValue": "active"}
        }

        if metadata:
            for k, v in metadata.items():
                if isinstance(v, bool):
                    fields[k] = {"booleanValue": v}
                elif isinstance(v, int):
                    fields[k] = {"integerValue": str(v)}
                else:
                    fields[k] = {"stringValue": str(v)}

        payload = {"fields": fields}
        data = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="PATCH"
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Failed to save authenticator key to Firebase ({e.code}): {e.reason}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Unable to connect to Firebase: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Firebase save failed: {str(e)}")

    def check_connection(self) -> bool:
        """Quick ping test to determine Firebase connectivity."""
        try:
            req = urllib.request.Request(self.base_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status in (200, 404)
        except urllib.error.HTTPError as e:
            # 404 means server is connected and answering
            return e.code == 404
        except Exception:
            return False
