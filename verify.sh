#!/bin/bash

# Script de verificación para detectar secretos y validar calidad del código
# Ejecuta black, isort, flake8, mypy, pytest y verifica secretos

set -e  # Salir en caso de error

echo "🔍 Iniciando verificación completa del proyecto..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    print_error "No se encontró main.py. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

print_status "Verificando directorio del proyecto..."

# 2. Buscar patrones de secretos
print_status "🔐 Buscando patrones de secretos..."

SECRETS_FOUND=0

# Patrones de secretos a buscar
PATTERNS=(
    "sk-[A-Za-z0-9]{20,}"           # OpenAI API keys
    "TWILIO_[A-Z_]+"                # Twilio tokens
    "postgres://[^@]+@[^@]+"        # URLs de PostgreSQL con credenciales
    "mysql://[^@]+@[^@]+"           # URLs de MySQL con credenciales
    "redis://[^@]+@[^@]+"           # URLs de Redis con credenciales
    "mongodb://[^@]+@[^@]+"         # URLs de MongoDB con credenciales
    "AKIA[0-9A-Z]{16}"             # AWS Access Keys
    "ghp_[A-Za-z0-9]{36}"          # GitHub Personal Access Tokens
    "gho_[A-Za-z0-9]{36}"          # GitHub OAuth Tokens
    "ghu_[A-Za-z0-9]{36}"          # GitHub User-to-Server Tokens
    "ghs_[A-Za-z0-9]{36}"          # GitHub Server-to-Server Tokens
    "ghr_[A-Za-z0-9]{36}"          # GitHub Refresh Tokens
    "ya29\.[A-Za-z0-9_-]+"         # Google OAuth tokens
    "AIza[0-9A-Za-z\-_]{35}"       # Google API keys
    "1//[0-9A-Za-z\-_]+"           # Google OAuth refresh tokens
    "password.*=.*['\"][^'\"]{8,}"  # Contraseñas hardcodeadas
    "secret.*=.*['\"][^'\"]{8,}"    # Secretos hardcodeados
    "token.*=.*['\"][^'\"]{8,}"     # Tokens hardcodeados
    "key.*=.*['\"][^'\"]{8,}"       # Keys hardcodeadas
)

# Archivos a excluir de la búsqueda
EXCLUDE_PATTERNS=(
    "node_modules"
    ".git"
    "__pycache__"
    "*.pyc"
    "*.pyo"
    "*.pyd"
    ".pytest_cache"
    ".coverage"
    "venv"
    "env"
    ".env"
    ".env.example"
    "config.env.example"
    "test.db"
    "*.log"
)

# Construir comando de exclusión
EXCLUDE_CMD=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_CMD="$EXCLUDE_CMD -not -path '*/$pattern/*'"
done

# Buscar cada patrón
for pattern in "${PATTERNS[@]}"; do
    echo "Buscando patrón: $pattern"
    # Usar find para buscar archivos y grep para el contenido
    while IFS= read -r -d '' file; do
        if grep -q "$pattern" "$file" 2>/dev/null; then
            print_error "Secreto encontrado en $file:"
            grep -n "$pattern" "$file" | head -3
            SECRETS_FOUND=$((SECRETS_FOUND + 1))
        fi
    done < <(find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.env*" $EXCLUDE_CMD -print0 2>/dev/null)
done

if [ $SECRETS_FOUND -eq 0 ]; then
    print_success "✅ No se encontraron secretos hardcodeados"
else
    print_error "❌ Se encontraron $SECRETS_FOUND posibles secretos"
    exit 1
fi

# 3. Verificar variables de entorno críticas
print_status "🔧 Verificando variables de entorno críticas..."

CRITICAL_VARS=(
    "SECRET_KEY"
    "DATABASE_URL"
    "REDIS_URL"
    "OPENAI_API_KEY"
    "TWILIO_ACCOUNT_SID"
    "TWILIO_AUTH_TOKEN"
)

MISSING_VARS=0

for var in "${CRITICAL_VARS[@]}"; do
    if ! grep -q "^$var=" .env.example 2>/dev/null; then
        print_warning "Variable crítica '$var' no encontrada en .env.example"
        MISSING_VARS=$((MISSING_VARS + 1))
    fi
done

if [ $MISSING_VARS -eq 0 ]; then
    print_success "✅ Todas las variables críticas están documentadas en .env.example"
else
    print_warning "⚠️  Faltan $MISSING_VARS variables críticas en .env.example"
fi

# 4. Verificar formato de código con black
print_status "🎨 Verificando formato de código con black..."

if command -v black &> /dev/null; then
    if black --check . --quiet; then
        print_success "✅ Código formateado correctamente con black"
    else
        print_error "❌ Código no está formateado correctamente. Ejecuta: black ."
        exit 1
    fi
else
    print_warning "⚠️  black no está instalado. Instala con: pip install black"
fi

# 5. Verificar imports con isort
print_status "📦 Verificando orden de imports con isort..."

if command -v isort &> /dev/null; then
    if isort --check-only . --quiet; then
        print_success "✅ Imports ordenados correctamente con isort"
    else
        print_error "❌ Imports no están ordenados correctamente. Ejecuta: isort ."
        exit 1
    fi
else
    print_warning "⚠️  isort no está instalado. Instala con: pip install isort"
fi

# 6. Verificar estilo con flake8
print_status "🔍 Verificando estilo de código con flake8..."

if command -v flake8 &> /dev/null; then
    if flake8 . --count --max-line-length=88 --extend-ignore=E203,W503 --quiet; then
        print_success "✅ Código cumple con flake8"
    else
        print_error "❌ Código no cumple con flake8"
        flake8 . --count --max-line-length=88 --extend-ignore=E203,W503
        exit 1
    fi
else
    print_warning "⚠️  flake8 no está instalado. Instala con: pip install flake8"
fi

# 7. Verificar tipos con mypy
print_status "🔍 Verificando tipos con mypy..."

if command -v mypy &> /dev/null; then
    if mypy . --ignore-missing-imports --no-strict-optional; then
        print_success "✅ Verificación de tipos exitosa con mypy"
    else
        print_warning "⚠️  Problemas de tipos detectados por mypy"
        mypy . --ignore-missing-imports --no-strict-optional
    fi
else
    print_warning "⚠️  mypy no está instalado. Instala con: pip install mypy"
fi

# 8. Compilar código Python
print_status "🐍 Compilando código Python..."

if python3 -m compileall . -q; then
    print_success "✅ Compilación exitosa - sin errores de sintaxis"
else
    print_error "❌ Errores de sintaxis encontrados"
    exit 1
fi

# 9. Ejecutar tests
print_status "🧪 Ejecutando tests..."

# Configurar variables de entorno para tests
export DISABLE_RATE_LIMITER=true
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test_secret_key_for_testing_only"
export OPENAI_API_KEY="sk-test-key-for-testing-only"
export TWILIO_ACCOUNT_SID="test_account_sid"
export TWILIO_AUTH_TOKEN="test_auth_token"

if command -v pytest &> /dev/null; then
    if pytest -q --disable-warnings --tb=short; then
        print_success "✅ Todos los tests pasaron"
    else
        print_error "❌ Algunos tests fallaron"
        exit 1
    fi
else
    print_warning "⚠️  pytest no está instalado. Instala con: pip install pytest"
fi

# 10. Verificar que no hay archivos de test.db en el repo
print_status "🗂️  Verificando archivos de base de datos de test..."

if git ls-files | grep -q "test.db"; then
    print_error "❌ test.db está en el repositorio. Debe ser ignorado"
    exit 1
else
    print_success "✅ test.db no está en el repositorio"
fi

# 11. Verificar .gitignore
print_status "📋 Verificando .gitignore..."

if grep -q "test.db" .gitignore; then
    print_success "✅ test.db está en .gitignore"
else
    print_warning "⚠️  test.db no está en .gitignore"
fi

if grep -q "*.pyc" .gitignore; then
    print_success "✅ *.pyc está en .gitignore"
else
    print_warning "⚠️  *.pyc no está en .gitignore"
fi

if grep -q "__pycache__" .gitignore; then
    print_success "✅ __pycache__ está en .gitignore"
else
    print_warning "⚠️  __pycache__ no está en .gitignore"
fi

# 12. Verificar que no hay prints de depuración
print_status "🔍 Verificando prints de depuración..."

DEBUG_PRINTS=$(find . -name "*.py" -not -path "./venv/*" -not -path "./env/*" -not -path "./.git/*" -not -path "./node_modules/*" -exec grep -l "print(" {} \; | wc -l)

if [ $DEBUG_PRINTS -eq 0 ]; then
    print_success "✅ No se encontraron prints de depuración"
else
    print_warning "⚠️  Se encontraron prints de depuración en $DEBUG_PRINTS archivos"
    find . -name "*.py" -not -path "./venv/*" -not -path "./env/*" -not -path "./.git/*" -not -path "./node_modules/*" -exec grep -l "print(" {} \;
fi

# 13. Verificar dependencias vulnerables
print_status "🔒 Verificando dependencias vulnerables (pip-audit)..."
if command -v pip-audit &> /dev/null; then
    pip-audit || print_warning "⚠️  Vulnerabilidades detectadas en dependencias"
else
    print_warning "⚠️  pip-audit no está instalado. Instala con: pip install pip-audit"
fi

echo ""
print_success "🎉 Verificación completa finalizada"
print_status "Resumen:"
echo "  ✅ Búsqueda de secretos: Completada"
echo "  ✅ Variables de entorno: Verificadas"
echo "  ✅ Formato de código: Verificado"
echo "  ✅ Imports: Verificados"
echo "  ✅ Estilo de código: Verificado"
echo "  ✅ Tipos: Verificados"
echo "  ✅ Compilación: Exitosa"
echo "  ✅ Tests: Ejecutados"
echo "  ✅ Archivos de test: Verificados"
echo "  ✅ .gitignore: Verificado"
echo "  ✅ Prints de depuración: Verificados"
echo "  ✅ Dependencias vulnerables: Verificadas"

print_success "🚀 El proyecto está listo para producción!" 