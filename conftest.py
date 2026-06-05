import sys
from pathlib import Path

# src/ zum Python-Pfad hinzufügen damit `cloudlockfixer` importierbar ist
sys.path.insert(0, str(Path(__file__).parent / "src"))
