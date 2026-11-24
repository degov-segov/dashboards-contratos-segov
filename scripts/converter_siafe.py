"""
Converte o relatório do SIAFE-CE "Detalhamento das Despesas - Empenho, Liquidação e Pagamento -
Ordem Cronológica" no arquivo de dados do painel SIAFE (site/siafe/dados/siafe.json).

Como usar
- Exporte o relatório do SIAFE em Excel (.xlsx), sem alterar nada, e coloque na pasta Planilhas/SIAFE.
- Se houver mais de um arquivo na pasta, vale apenas o mais recente (data "Impresso em" do relatório),
  porque cada exportação já traz o acumulado do exercício.
- O contrato é identificado pelo código "CT-xxx/aaaa" escrito na Observação do empenho.
- CPFs de pessoas físicas são mascarados antes da publicação.
- Opcional: se a planilha Planilhas/contratos.xlsx tiver a aba Contratos, valor global e limites
  de empenho são aproveitados quando o código do contrato coincidir (ex.: CT-25/2022).
"""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

ORIGEM = Path("Planilhas/SIAFE")
CADASTRO = Path("Planilhas/contratos.xlsx")
DESTINO = Path("site/siafe/dados")
DESTINO.mkdir(parents=True, exist_ok=True)

COLUNAS = {
    "Unidade Gestora / Nota de Empenho": "ne",
    "Processo": "processo",
    "Observação": "obs",
    "Nota de Liquidação": "nl",
    "Tipo (PD)": "tipo",
    "Programação de Desembolso": "pd",
    "Ordem Bancária": "ob",
    "Credor": "credorDoc",
    "Nome do Credor": "credor",
    "Credor da Retenção": "retencao",
    "Empenhado": "emp",
    "Liquidado": "liq",
    "Pago": "pago",
}
RE_CT = re.compile(r"\bCT\s*-?\s*0*(\d+)\s*/\s*(\d{4})", re.I)
RE_IMPRESSO = re.compile(r"Impresso em (\d{2}/\d{2}/\d{4} \d{2}:\d{2})")


def vazio(v):
    return v is None or (isinstance(v, str) and v.strip(" -") == "")


def texto(v):
    return None if vazio(v) else re.sub(r"\s+", " ", str(v)).strip()


def numero(v):
    if vazio(v):
        return 0.0
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    return round(float(str(v).replace(".", "").replace(",", ".")), 2)


def mascarar(doc):
    """CPF (11 dígitos) vira ***.456.789-**; CNPJ é mantido."""
    if not doc:
        return None
    d = re.sub(r"\D", "", doc)
    if len(d) == 11:
        return f"***.{d[3:6]}.{d[6:9]}-**"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return doc


def mascarar_retencao(v):
    v = texto(v)
    if not v:
        return None
    m = re.match(r"(\d{11}|\d{14})\s*-\s*(.*)", v)
    return f"{mascarar(m.group(1))} - {m.group(2).strip()}" if m else v


def ler_relatorio(caminho):
    ws = openpyxl.load_workbook(caminho, data_only=True).worksheets[0]
    linhas = list(ws.iter_rows(values_only=True))
    titulo = next((texto(c) for r in linhas[:6] for c in r if texto(c) and "Detalhamento" in str(c)), None)
    impresso, filtro = None, None
    for i, r in enumerate(linhas):
        for c in r:
            if isinstance(c, str) and (m := RE_IMPRESSO.search(c)):
                impresso = datetime.strptime(m.group(1), "%d/%m/%Y %H:%M").isoformat()
        if r[0] == "Filtro" and i + 1 < len(linhas):
            filtro = texto(linhas[i + 1][0])
    inicio = next(i for i, r in enumerate(linhas) if isinstance(r[0], str) and r[0].startswith("Unidade Gestora"))
    cab = [texto(c) for c in linhas[inicio]]
    idx = {COLUNAS[c]: j for j, c in enumerate(cab) if c in COLUNAS}
    faltam = set(COLUNAS.values()) - set(idx)
    if faltam:
        raise SystemExit(f"{caminho.name}: colunas não encontradas no relatório: {', '.join(sorted(faltam))}")

    registros, ug = [], None
    for ordem, r in enumerate(linhas[inicio + 1:]):
        primeira = r[0]
        if not isinstance(primeira, str) or not primeira.strip():
            continue
        if primeira.strip() == "Total":
            break
        if not primeira.startswith(" "):  # linha de subtotal da Unidade Gestora
            ug = texto(primeira)
            continue
        g = lambda k: r[idx[k]]
        registros.append({
            "ordem": ordem,
            "ug": ug,
            "ne": texto(g("ne")),
            "processo": texto(g("processo")),
            "obs": texto(g("obs")),
            "nl": texto(g("nl")),
            "tipo": texto(g("tipo")),
            "pd": texto(g("pd")),
            "ob": texto(g("ob")),
            "credorDoc": mascarar(texto(g("credorDoc"))),
            "credor": texto(g("credor")),
            "retencao": mascarar_retencao(g("retencao")),
            "emp": numero(g("emp")),
            "liq": numero(g("liq")),
            "pago": numero(g("pago")),
        })
    return {"arquivo": caminho.name, "titulo": titulo, "impressoEm": impresso, "filtro": filtro}, registros


def ler_cadastro():
    """Lê (se existir) a aba Contratos da planilha manual, para valor global e limites."""
    if not CADASTRO.exists():
        return {}
    wb = openpyxl.load_workbook(CADASTRO, data_only=True)
    if "Contratos" not in wb.sheetnames:
        return {}
    linhas = list(wb["Contratos"].iter_rows(values_only=True))
    cab = [texto(c) for c in linhas[0]]
    cad = {}
    for r in linhas[1:]:
        d = dict(zip(cab, r))
        cod = texto(d.get("Contrato"))
        if not cod or not (m := RE_CT.search(cod)):
            continue
        chave = f"CT-{int(m.group(1))}/{m.group(2)}"
        cad[chave] = {
            "contratada": texto(d.get("Contratada")),
            "objeto": texto(d.get("Objeto")),
            "valorGlobal": d.get("Valor global (R$)") if isinstance(d.get("Valor global (R$)"), (int, float)) else None,
            "limiteEmpenho": d.get("Limite de empenho 2026 (R$)") if isinstance(d.get("Limite de empenho 2026 (R$)"), (int, float)) else None,
            "fimVigencia": d["Fim da vigência"].isoformat() if isinstance(d.get("Fim da vigência"), datetime) else None,
        }
    return cad


arquivos = [a for a in sorted(ORIGEM.glob("*.xlsx")) if not a.name.startswith("~$")]
if not arquivos:
    raise SystemExit("Nenhum relatório .xlsx encontrado em Planilhas/SIAFE.")
lidos = [ler_relatorio(a) for a in arquivos]
fonte, linhas = max(lidos, key=lambda x: (x[0]["impressoEm"] or "", x[0]["arquivo"]))
print(f"Relatório usado: {fonte['arquivo']} (impresso em {fonte['impressoEm']}) · {len(linhas)} linhas")

# Contrato de cada credor = código CT mais citado nas observações dos seus empenhos
codigos = {}
for l in linhas:
    for m in RE_CT.finditer(l["obs"] or ""):
        codigos.setdefault(l["credor"], Counter())[f"CT-{int(m.group(1))}/{m.group(2)}"] += 1
for l in linhas:
    c = codigos.get(l["credor"])
    l["contrato"] = c.most_common(1)[0][0] if c else "Sem nº de contrato"

saida = {
    "atualizadoEm": datetime.now(timezone.utc).isoformat(),
    "fonte": fonte,
    "cadastro": ler_cadastro(),
    "linhas": linhas,
}
(DESTINO / "siafe.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print("Arquivo gerado: site/siafe/dados/siafe.json")
