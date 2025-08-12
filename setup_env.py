#!/usr/bin/env python3
"""
Script para configurar automáticamente las variables de entorno
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Configura el archivo .env con las variables necesarias"""
    
    print("🚀 Configurando variables de entorno...")
    
    # Verificar si ya existe .env
    if Path('.env').exists():
        print("⚠️  El archivo .env ya existe. ¿Quieres sobrescribirlo? (y/N): ", end="")
        response = input().lower()
        if response != 'y':
            print("❌ Configuración cancelada")
            return
    
    # Copiar archivo de ejemplo
    if Path('env.example').exists():
        shutil.copy('env.example', '.env')
        print("✅ Archivo .env creado desde env.example")
    else:
        print("❌ No se encontró env.example")
        return
    
    # Generar SECRET_KEY
    import secrets
    secret_key = secrets.token_hex(32)
    
    # Leer el archivo .env
    with open('.env', 'r') as f:
        content = f.read()
    
    # Reemplazar SECRET_KEY
    content = content.replace(
        'SECRET_KEY=your_super_secret_key_here_minimum_32_characters',
        f'SECRET_KEY={secret_key}'
    )
    
    # Escribir el archivo actualizado
    with open('.env', 'w') as f:
        f.write(content)
    
    print(f"✅ SECRET_KEY generada: {secret_key[:16]}...")
    print("✅ Archivo .env configurado correctamente")
    
    # Mostrar variables que necesitan configuración manual
    print("\n📋 Variables que necesitas configurar manualmente:")
    print("   - WHATSAPP_API_KEY (si usas WhatsApp)")
    print("   - MERCADOPAGO_ACCESS_TOKEN (si usas MercadoPago)")
    print("   - STRIPE_SECRET_KEY (si usas Stripe)")
    
    print("\n🔧 Para editar el archivo .env:")
    print("   nano .env")
    print("   # o")
    print("   code .env")

if __name__ == "__main__":
    setup_environment() 