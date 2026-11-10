"""
Converte a planilha de execução contratual (pasta Planilhas) no arquivo de dados do dashboard.

- Lê todas as planilhas .xlsx da pasta Planilhas.
- Publica as abas Contratos, Empenhos e Pagamentos (e qualquer outra aba que não comece com "_").
- Abas que começam com "_" (ex.: _Instruções, _Resumo) são ignoradas.
- Se houver mais de uma planilha com a mesma aba, as linhas são somadas.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ORIGEM = Path("Planilhas")
DESTINO = Path("site/dados")
DESTINO.mkdir(parents=True, exist_ok=True)

abas = {}
for arquivo in sorted(ORIGEM.glob("*.xlsx")):
    if arquivo.name.startswith("~$"):  # arquivo temporário do Excel
        continue
    for nome, df in pd.read_excel(arquivo, sheet_name=None).items():
        if nome.startswith("_"):
            continue
        df = df.dropna(how="all")
        if df.empty:
            continue
        registros = json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False))
        abas.setdefault(nome.strip(), []).extend(registros)
        print(f"OK  {arquivo.name} > {nome}: {len(df)} linhas")

for obrigatoria in ("Contratos", "Empenhos", "Pagamentos"):
    if obrigatoria not in abas:
        raise SystemExit(f"Aba obrigatória não encontrada: {obrigatoria}")

saida = {"atualizadoEm": datetime.now(timezone.utc).isoformat(), "abas": abas}
(DESTINO / "execucao.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
print("Arquivo gerado: site/dados/execucao.json")
