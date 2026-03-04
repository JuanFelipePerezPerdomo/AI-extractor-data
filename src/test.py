import sys
try:
    from google import genai
    print(f"✅ ¡Éxito! Librería 'google-genai' detectada.")
    print(f"🐍 Estás usando Python {sys.version.split()[0]}")
    print(f"📂 Ubicación del entorno: {sys.prefix}")
except ImportError:
    print("❌ Error: No se encuentra la librería. ¿Activaste el entorno virtual?")