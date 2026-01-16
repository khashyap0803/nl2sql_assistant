import requests
import base64
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class RemoteNL2SQLClient:
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.enabled = False
        self.timeout = 120
        
        if self._check_connection():
            self.enabled = True
            print(f"[OK] Connected to remote server: {self.server_url}")
        else:
            print(f"[ERROR] Cannot connect to server: {self.server_url}")
    
    def _check_connection(self) -> bool:
        try:
            response = requests.get(
                f"{self.server_url}/api/health",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"[SERVER] LLM: {'OK' if data['services']['llm'] else 'OFFLINE'}")
                print(f"[SERVER] STT: {'OK' if data['services']['stt'] else 'OFFLINE'}")
                if 'gpu' in data:
                    print(f"[SERVER] GPU: {data['gpu']['allocated_gb']:.1f} / {data['gpu']['total_gb']:.1f} GB")
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False
        except Exception as e:
            print(f"[ERROR] Health check failed: {e}")
            return False
    
    def get_gpu_memory_usage(self) -> Optional[Dict[str, float]]:
        try:
            response = requests.get(
                f"{self.server_url}/api/health",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'gpu' in data:
                    return {
                        "allocated": data['gpu']['allocated_gb'],
                        "total": data['gpu']['total_gb']
                    }
        except:
            pass
        return None
    
    def convert_and_execute(
        self, 
        nl_query: str,
        execute: bool = True
    ) -> Tuple[str, Optional[pd.DataFrame], Dict[str, Any]]:
        if not self.enabled:
            return "", None, {"error": "Client not connected"}
        
        try:
            response = requests.post(
                f"{self.server_url}/api/query",
                json={"query": nl_query},
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_data = response.json()
                return "", None, {"error": error_data.get("error", "Unknown error")}
            
            data = response.json()
            
            sql = data.get("sql", "")
            metadata = data.get("metadata", {})
            
            result = None
            if data.get("result"):
                columns = data["result"]["columns"]
                rows = data["result"]["data"]
                result = pd.DataFrame(rows, columns=columns)
            
            return sql, result, metadata
            
        except requests.exceptions.Timeout:
            return "", None, {"error": "Server timeout"}
        except requests.exceptions.ConnectionError:
            return "", None, {"error": "Cannot connect to server"}
        except Exception as e:
            return "", None, {"error": str(e)}
    
    def convert(self, nl_query: str) -> str:
        sql, _, _ = self.convert_and_execute(nl_query, execute=False)
        return sql
    
    def get_suggestions(self, partial_query: str = "") -> List[str]:
        return [
            "Show all data",
            "Total sales by region",
            "Top 10 products by revenue",
            "Sales for January 2025",
            "Average amount by customer type"
        ]


class RemoteSpeechToText:
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.enabled = False
        self.sample_rate = 16000
        self.timeout = 60
        
        if self._check_stt_available():
            self.enabled = True
    
    def _check_stt_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.server_url}/api/health",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data['services'].get('stt', False)
            return False
        except:
            return False
    
    def listen(self, duration: int = 5) -> str:
        if not self.enabled:
            return ""
        
        try:
            import sounddevice as sd
            
            print(f"Recording for {duration} seconds...")
            
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            audio_data = audio_data.flatten()
            
            print("Sending audio to server for transcription...")
            
            audio_bytes = audio_data.tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            response = requests.post(
                f"{self.server_url}/api/voice",
                json={
                    "audio": audio_b64,
                    "sample_rate": self.sample_rate
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Server returned: {response.status_code}")
                return ""
            
            data = response.json()
            text = data.get("text", "")
            
            if text:
                print(f"Transcribed: '{text}'")
            else:
                print("No speech detected")
            
            return text
            
        except ImportError:
            print("[ERROR] sounddevice not installed")
            return ""
        except Exception as e:
            print(f"[ERROR] Voice recording/transcription failed: {e}")
            return ""
    
    def get_device(self) -> str:
        return "Remote (GPU)" if self.enabled else "disabled"


def test_remote_client():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python client.py <server_url>")
        print("Example: python client.py https://abc123.trycloudflare.com")
        return
    
    server_url = sys.argv[1]
    print(f"Testing connection to: {server_url}")
    print()
    
    client = RemoteNL2SQLClient(server_url)
    
    if client.enabled:
        print("\nTesting query...")
        sql, result, metadata = client.convert_and_execute("show all data")
        print(f"SQL: {sql}")
        if result is not None:
            print(f"Rows: {len(result)}")
            print(result.head())
        else:
            print(f"Error: {metadata.get('error')}")
    else:
        print("Client not connected")


if __name__ == "__main__":
    test_remote_client()
