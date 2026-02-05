#!/usr/bin/env python3
"""
Script para testar a API de geração de imagens
Certifique-se que Ollama está rodando antes de executar
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import sys

# Configurações
API_URL = "http://localhost:5000"

def test_health():
    """Teste do health check"""
    print("\n🔍 Testando /health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_models():
    """Teste de listagem de modelos"""
    print("\n🔍 Testando /api/models...")
    try:
        response = requests.get(f"{API_URL}/api/models", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_generate_image(prompt="um gato colorido", width=512, height=512):
    """Teste de geração de imagem"""
    print(f"\n🔍 Testando /api/generate com prompt: '{prompt}'...")
    try:
        response = requests.post(
            f"{API_URL}/api/generate",
            json={
                "prompt": prompt,
                "width": width,
                "height": height
            },
            timeout=300  # 5 minutos
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Salvar imagem
            filename = f"test_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Imagem salva: {filename}")
            print(f"Tamanho: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - geração levou muito tempo")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("🎨 Testando Ollama Image Generation API")
    print("=" * 60)
    
    # Verificar se a API está rodando
    print(f"\n📡 Conectando a {API_URL}...")
    try:
        requests.get(f"{API_URL}/", timeout=5)
        print("✅ API está respondendo")
    except:
        print("❌ API não está respondendo!")
        print("   Execute em outro terminal: python app.py")
        sys.exit(1)
    
    # Executar testes
    results = {
        "health": test_health(),
        "models": test_models(),
        "generate": test_generate_image("um robô futurista em Tóquio"),
    }
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 Resultado dos Testes")
    print("=" * 60)
    for test, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test.upper()}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! API está funcionando corretamente.")
        sys.exit(0)
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
