#!/usr/bin/env python3
"""
GEKO Magazine Builder
Compila documenti Typst in PDF

Uso:
    python build.py esempio-geko67.typ
    python build.py esempio-geko67.typ -o output/geko67.pdf
"""

import sys
import argparse
from pathlib import Path

try:
    import typst
except ImportError:
    print("Errore: pacchetto 'typst' non installato")
    print("Installa con: pip install typst")
    sys.exit(1)


def build_magazine(input_file: str, output_file: str = None) -> None:
    """Compila un file .typ in PDF"""
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Errore: file '{input_file}' non trovato")
        sys.exit(1)
    
    if not input_path.suffix == '.typ':
        print(f"Errore: il file deve avere estensione .typ")
        sys.exit(1)
    
    # Output di default
    if output_file is None:
        output_file = input_path.with_suffix('.pdf')
    else:
        output_file = Path(output_file)
    
    # Crea directory output se non esiste
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Compilazione: {input_path} -> {output_file}")
    
    try:
        # Compila
        pdf_bytes = typst.compile(str(input_path))
        
        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✓ PDF generato: {output_file} ({len(pdf_bytes)} bytes)")
        
    except Exception as e:
        print(f"✗ Errore di compilazione: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Compila GEKO Magazine da Typst a PDF"
    )
    parser.add_argument(
        "input",
        help="File .typ da compilare"
    )
    parser.add_argument(
        "-o", "--output",
        help="File PDF di output (default: stesso nome con .pdf)"
    )
    
    args = parser.parse_args()
    build_magazine(args.input, args.output)


if __name__ == "__main__":
    main()
