import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ORIGEM = Path("Planilhas")
DESTINO = Path("site/dados")
DESTINO.mkdir(parents=True, exist_ok=True)

for arquivo in ORIGEM.glob("*.xlsx"):
    df = pd.read_excel(arquivo, sheet_name="Dados").dropna(how="all")
    saida = {
        "atualizadoEm": datetime.now(timezone.utc).isoformat(),
        "dados": json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False)),
    }
    (DESTINO / f"{arquivo.stem}.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )
