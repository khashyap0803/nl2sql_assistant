import sys
import os
import io
import json
import base64
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd

from src.llm.nl2sql_converter import NL2SQLConverter
from src.voice.speech_to_text import SpeechToText
from src.database.db_controller import DatabaseController
from src.utils.logger import logger

app = Flask(__name__)
CORS(app)

converter = None
stt = None
db = None


def initialize_services():
    global converter, stt, db
    
    logger.section("NL2SQL Server - Initializing Services")
    
    print("Loading NL2SQL Converter (RAG + Ollama LLM)...")
    converter = NL2SQLConverter()
    if converter.enabled:
        print("[OK] NL2SQL Converter ready")
    else:
        print("[WARNING] NL2SQL Converter not fully initialized")
    
    print("Loading Whisper Large-v3 on GPU...")
    try:
        stt = SpeechToText()
        if stt.enabled:
            print("[OK] Speech-to-Text ready (GPU)")
        else:
            print("[WARNING] Speech-to-Text not available")
    except Exception as e:
        print(f"[WARNING] STT initialization failed: {e}")
        stt = None
    
    print("Connecting to database...")
    db = DatabaseController()
    if db.connect():
        print("[OK] Database connected")
        db.close()
    else:
        print("[WARNING] Database connection failed")
    
    logger.section("NL2SQL Server - Ready")
    print("\nServer is ready to accept connections!")


@app.route('/api/health', methods=['GET'])
def health_check():
    status = {
        "status": "online",
        "services": {
            "llm": converter.enabled if converter else False,
            "stt": stt.enabled if stt else False,
            "database": True
        }
    }
    
    if converter and converter.enabled:
        gpu_mem = converter.get_gpu_memory_usage()
        if gpu_mem:
            status["gpu"] = {
                "allocated_gb": round(gpu_mem.get("allocated", 0), 2),
                "total_gb": round(gpu_mem.get("total", 0), 2)
            }
    
    return jsonify(status)


@app.route('/api/query', methods=['POST'])
def process_query():
    if not converter or not converter.enabled:
        return jsonify({"error": "NL2SQL converter not available"}), 503
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' field"}), 400
    
    nl_query = data['query']
    logger.i("SERVER", f"Processing query: '{nl_query}'")
    
    try:
        sql, result, metadata = converter.convert_and_execute(nl_query, execute=True)
        
        response = {
            "success": True,
            "sql": sql,
            "metadata": metadata
        }
        
        if isinstance(result, pd.DataFrame):
            response["result"] = {
                "columns": result.columns.tolist(),
                "data": result.values.tolist(),
                "row_count": len(result)
            }
        else:
            response["result"] = None
            response["error"] = str(result) if result else "No result"
        
        logger.i("SERVER", f"Query completed: {len(result) if isinstance(result, pd.DataFrame) else 0} rows")
        return jsonify(response)
        
    except Exception as e:
        logger.e("SERVER", f"Query error: {e}", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/voice', methods=['POST'])
def process_voice():
    if not stt or not stt.enabled:
        return jsonify({"error": "Speech-to-text not available"}), 503
    
    data = request.get_json()
    
    if not data or 'audio' not in data:
        return jsonify({"error": "Missing 'audio' field (base64 encoded)"}), 400
    
    try:
        audio_bytes = base64.b64decode(data['audio'])
        sample_rate = data.get('sample_rate', 16000)
        
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        logger.i("SERVER", f"Processing audio: {len(audio_array)} samples at {sample_rate}Hz")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            import scipy.io.wavfile as wav
            wav.write(tmp_path, sample_rate, audio_array)
        
        try:
            text = stt.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)
        
        logger.i("SERVER", f"Transcription: '{text}'")
        
        return jsonify({
            "success": True,
            "text": text
        })
        
    except Exception as e:
        logger.e("SERVER", f"Voice processing error: {e}", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/voice_query', methods=['POST'])
def voice_query():
    if not stt or not stt.enabled:
        return jsonify({"error": "Speech-to-text not available"}), 503
    
    if not converter or not converter.enabled:
        return jsonify({"error": "NL2SQL converter not available"}), 503
    
    data = request.get_json()
    
    if not data or 'audio' not in data:
        return jsonify({"error": "Missing 'audio' field (base64 encoded)"}), 400
    
    try:
        audio_bytes = base64.b64decode(data['audio'])
        sample_rate = data.get('sample_rate', 16000)
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            import scipy.io.wavfile as wav
            wav.write(tmp_path, sample_rate, audio_array)
        
        try:
            text = stt.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)
        
        if not text:
            return jsonify({
                "success": False,
                "error": "No speech detected"
            })
        
        logger.i("SERVER", f"Voice query: '{text}'")
        
        sql, result, metadata = converter.convert_and_execute(text, execute=True)
        
        response = {
            "success": True,
            "transcribed_text": text,
            "sql": sql,
            "metadata": metadata
        }
        
        if isinstance(result, pd.DataFrame):
            response["result"] = {
                "columns": result.columns.tolist(),
                "data": result.values.tolist(),
                "row_count": len(result)
            }
        else:
            response["result"] = None
        
        return jsonify(response)
        
    except Exception as e:
        logger.e("SERVER", f"Voice query error: {e}", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/schema', methods=['GET'])
def get_schema():
    try:
        db_local = DatabaseController()
        if not db_local.connect():
            return jsonify({"error": "Database connection failed"}), 503
        
        tables = db_local.get_table_names()
        schema_info = {}
        
        for table in tables:
            schema = db_local.get_table_schema(table)
            if isinstance(schema, pd.DataFrame):
                schema_info[table] = {
                    "columns": schema.to_dict('records')
                }
        
        db_local.close()
        
        return jsonify({
            "success": True,
            "tables": tables,
            "schema": schema_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    print("=" * 70)
    print("  NL2SQL Voice Assistant - Remote Server")
    print("  GPU-Accelerated Backend for Remote Clients")
    print("=" * 70)
    print()
    
    initialize_services()
    
    host = os.environ.get('SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('SERVER_PORT', 5000))
    
    print()
    print("=" * 70)
    print(f"  Server running at: http://{host}:{port}")
    print()
    print("  To expose via Cloudflare Tunnel (CGNAT bypass):")
    print(f"    cloudflared tunnel --url http://localhost:{port}")
    print()
    print("  Or via Pinggy:")
    print(f"    ssh -p 443 -R0:localhost:{port} a.pinggy.io")
    print("=" * 70)
    print()
    
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
