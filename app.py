from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import io
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
MODEL = os.getenv('MODEL', 'flux:latest')
PORT = int(os.getenv('PORT', 5000))

# Verificar conexão com Ollama ao iniciar
def check_ollama_connection():
    try:
        response = requests.get(f'{OLLAMA_API_URL}/api/tags', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Conectado ao Ollama com sucesso")
            return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Ollama: {e}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Verificar saúde da API"""
    ollama_ok = check_ollama_connection()
    return jsonify({
        'status': 'ok' if ollama_ok else 'warning',
        'ollama_connected': ollama_ok,
        'model': MODEL,
        'timestamp': datetime.now().isoformat()
    }), 200 if ollama_ok else 503

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """
    Gerar imagem com base no prompt
    
    Body JSON:
    {
        "prompt": "descrição da imagem",
        "width": 1024,
        "height": 1024,
        "model": "flux:latest" (opcional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Campo "prompt" é obrigatório'}), 400
        
        prompt = data.get('prompt')
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        model = data.get('model', MODEL)
        
        # Validações
        if len(prompt) < 3:
            return jsonify({'error': 'Prompt deve ter pelo menos 3 caracteres'}), 400
        
        if len(prompt) > 2000:
            return jsonify({'error': 'Prompt não pode ter mais de 2000 caracteres'}), 400
        
        if width < 256 or width > 2048:
            return jsonify({'error': 'Width deve estar entre 256 e 2048'}), 400
        
        if height < 256 or height > 2048:
            return jsonify({'error': 'Height deve estar entre 256 e 2048'}), 400
        
        logger.info(f"🎨 Gerando imagem: {prompt[:50]}...")
        
        # Fazer requisição ao Ollama
        ollama_request = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'images': {
                'width': width,
                'height': height
            }
        }
        
        response = requests.post(
            f'{OLLAMA_API_URL}/api/generate',
            json=ollama_request,
            timeout=300  # 5 minutos de timeout para geração
        )
        
        if response.status_code != 200:
            logger.error(f"Erro Ollama: {response.text}")
            return jsonify({'error': 'Erro ao gerar imagem no Ollama'}), 500
        
        result = response.json()
        
        # Extrair a imagem (Ollama retorna em base64 no campo 'images')
        if 'images' not in result or not result['images']:
            return jsonify({'error': 'Ollama não retornou imagem'}), 500
        
        image_base64 = result['images'][0]
        
        # Converter base64 para bytes
        import base64
        image_bytes = base64.b64decode(image_base64)
        
        logger.info(f"✅ Imagem gerada com sucesso ({len(image_bytes)} bytes)")
        
        # Retornar como arquivo PNG
        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'generated_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        
    except requests.exceptions.Timeout:
        logger.error("Timeout ao conectar ao Ollama")
        return jsonify({'error': 'Timeout: Geração de imagem levou muito tempo'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Erro de conexão com Ollama")
        return jsonify({'error': 'Não foi possível conectar ao Ollama'}), 503
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    """Listar modelos disponíveis"""
    try:
        response = requests.get(f'{OLLAMA_API_URL}/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                'models': [m['name'] for m in models],
                'count': len(models)
            }), 200
        return jsonify({'error': 'Erro ao listar modelos'}), 500
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {str(e)}")
        return jsonify({'error': 'Não foi possível conectar ao Ollama'}), 503

@app.route('/', methods=['GET'])
def index():
    """Rota raiz com documentação"""
    return jsonify({
        'name': 'Ollama Image Generation API',
        'version': '1.0',
        'endpoints': {
            'POST /api/generate': {
                'description': 'Gerar imagem a partir de um prompt',
                'body': {
                    'prompt': 'string (obrigatório)',
                    'width': 'integer (default: 1024)',
                    'height': 'integer (default: 1024)',
                    'model': 'string (default: ' + MODEL + ')'
                },
                'returns': 'PNG image'
            },
            'GET /api/models': {
                'description': 'Listar modelos disponíveis',
                'returns': 'JSON com lista de modelos'
            },
            'GET /health': {
                'description': 'Verificar saúde da API',
                'returns': 'JSON com status'
            }
        },
        'example': {
            'curl': 'curl -X POST http://localhost:5000/api/generate -H "Content-Type: application/json" -d \'{"prompt": "um gato colorido"}\''
        }
    }), 200

if __name__ == '__main__':
    logger.info(f"🚀 Iniciando Ollama Image API")
    logger.info(f"Ollama URL: {OLLAMA_API_URL}")
    logger.info(f"Modelo padrão: {MODEL}")
    check_ollama_connection()
    app.run(host='0.0.0.0', port=PORT, debug=False)
