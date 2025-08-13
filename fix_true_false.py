#!/usr/bin/env python3
import re
from pathlib import Path

# Carpeta donde buscar, por ejemplo tests/ o todo el repo
base_dir = Path(".")

# Extensiones a corregir
exts = [".py"]

for file_path in base_dir.rglob("*"):
    if file_path.suffix in exts:
        text = file_path.read_text(encoding="utf-8")

        # Reemplazar '' por nada
        text = re.sub(r"(\s*==\s*True)", "", text)

        # Reemplazar '== False' por not expresión
        text = re.sub(r"assert\s+(.+?)\s*==\s*False",
                      lambda m: f"assert not {m.group(1).strip()}",
                      text)

        file_path.write_text(text, encoding="utf-8")
        print(f"✔ Corregido: {file_path}")
