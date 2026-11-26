"""
Gera os dados dos painéis (site/siafe/dados/siafe.json) a partir dos relatórios do SIAFE-CE
"Detalhamento das Despesas - Empenho, Liquidação e Pagamento - Ordem Cronológica"
e do cadastro de contratos (Planilhas/contratos.xlsx, aba Contratos).

Como atualizar
- Exporte o relatório do SIAFE em Excel (.xlsx), um arquivo por Unidade Gestora (ex.: 040001 e 040101),
  e envie para a pasta Planilhas/SIAFE. O nome do arquivo não importa.
- Para cada Unidade Gestora vale o relatório mais recente (data "Impresso em"); os antigos podem ficar ou ser apagados.
- O contrato de cada empenho é o código "CT-xxx/aaaa" escrito na observação. Sem código, vale o contrato
  mais citado para o mesmo credor. A aba "Vínculos SIAFE" da contratos.xlsx (colunas "Nº do empenho" e
  "Contrato") permite indicar manualmente o contrato de qualquer empenho.
- CPFs de pessoas físicas são mascarados antes da publicação.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, date
from pathlib import Path

import openpyxl

ORIGEM = Path("Planilhas/SIAFE")
CADASTRO = Path("Planilhas/contratos.xlsx")
DESTINO = Path("site/siafe/dados")
DESTINO.mkdir(parents=True, exist_ok=True)

FONTES = {"040001": "Contrapartida (UG 040001)", "040101": "Fermoju (UG 040101)"}
COLUNAS = {
    "Unidade Gestora / Nota de Empenho": "ne", "Processo": "processo", "Observação": "obs",
    "Nota de Liquidação": "nl", "Tipo (PD)": "tipo", "Programação de Desembolso": "pd",
    "Ordem Bancária": "ob", "Credor": "credorDoc", "Nome do Credor": "credor",
    "Credor da Retenção": "retencao", "Empenhado": "emp", "Liquidado": "liq", "Pago": "pago",
}
RE_CT = re.compile(r"\bCT\s*-?\s*0*(\d+)\s*/\s*(\d{4})", re.I)
RE_IMPRESSO = re.compile(r"Impresso em (\d{2}/\d{2}/\d{4} \d{2}:\d{2})")
RE_DADOS = re.compile(r"Dados atualizados em:\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2})")
RE_EXERC = re.compile(r"de (20\d\d)")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
RE_MES = re.compile(r"\b(janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b(?:\s*(?:/|de|-)?\s*(20\d\d))?", re.I)


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


def codigo(v):
    m = RE_CT.search(v or "")
    return f"CT-{int(m.group(1))}/{m.group(2)}" if m else None


def mascarar(doc):
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


def data_br(txt):
    return datetime.strptime(txt, "%d/%m/%Y %H:%M").isoformat() if txt else None


def mes_referencia(obs, exercicio):
    """Primeiro mês citado na observação do empenho (ex.: 'NOVEMBRO/2026'); sem ano, usa o exercício."""
    m = RE_MES.search(obs or "")
    if not m:
        return None
    nome = m.group(1).lower().replace("marco", "março")
    ano = int(m.group(2)) if m.group(2) else exercicio
    return f"{ano}-{MESES.index(nome) + 1:02d}"


def ler_relatorio(caminho):
    ws = openpyxl.load_workbook(caminho, data_only=True).worksheets[0]
    linhas = list(ws.iter_rows(values_only=True))
    titulo = next((texto(c) for r in linhas[:6] for c in r if texto(c) and "Detalhamento" in str(c)), None)
    exercicio = int(RE_EXERC.findall(titulo or "")[-1]) if RE_EXERC.findall(titulo or "") else date.today().year
    impresso = dados_ate = filtro = None
    for i, r in enumerate(linhas):
        for c in r:
            if isinstance(c, str):
                if m := RE_IMPRESSO.search(c):
                    impresso = data_br(m.group(1))
                if m := RE_DADOS.search(c):
                    dados_ate = data_br(m.group(1))
        if r[0] == "Filtro" and i + 1 < len(linhas):
            filtro = texto(linhas[i + 1][0])
    inicio = next((i for i, r in enumerate(linhas) if isinstance(r[0], str) and r[0].startswith("Unidade Gestora")), None)
    if inicio is None:
        raise SystemExit(f"{caminho.name}: não parece ser o relatório do SIAFE (cabeçalho 'Unidade Gestora / Nota de Empenho' não encontrado).")
    cab = [texto(c) for c in linhas[inicio]]
    idx = {COLUNAS[c]: j for j, c in enumerate(cab) if c in COLUNAS}
    faltam = set(COLUNAS.values()) - set(idx)
    if faltam:
        raise SystemExit(f"{caminho.name}: colunas não encontradas no relatório: {', '.join(sorted(faltam))}")

    registros, ug, ugs = [], None, []
    for ordem, r in enumerate(linhas[inicio + 1:]):
        primeira = r[0]
        if not isinstance(primeira, str) or not primeira.strip():
            continue
        if primeira.strip() == "Total":
            break
        if not primeira.startswith(" "):  # subtotal da Unidade Gestora
            ug = texto(primeira)
            ugs.append(ug)
            continue
        g = lambda k: r[idx[k]]
        cod_ug = (ug or "")[:6]
        registros.append({
            "ordem": ordem, "ug": ug, "fonte": FONTES.get(cod_ug, ug),
            "ne": texto(g("ne")), "processo": texto(g("processo")), "obs": texto(g("obs")),
            "nl": texto(g("nl")), "tipo": texto(g("tipo")), "pd": texto(g("pd")), "ob": texto(g("ob")),
            "credorDoc": mascarar(texto(g("credorDoc"))), "credor": texto(g("credor")),
            "retencao": mascarar_retencao(g("retencao")),
            "emp": numero(g("emp")), "liq": numero(g("liq")), "pago": numero(g("pago")),
            "mesRef": mes_referencia(texto(g("obs")), exercicio),
        })
    info = {"arquivo": caminho.name, "titulo": titulo, "impressoEm": impresso, "dadosAte": dados_ate,
            "filtro": filtro, "ugs": ugs, "linhas": len(registros)}
    return info, registros


def valor_json(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def ler_cadastro():
    """Aba Contratos (cadastro) e aba Vínculos SIAFE (empenho -> contrato), se existirem."""
    if not CADASTRO.exists():
        return {}, {}
    wb = openpyxl.load_workbook(CADASTRO, data_only=True)
    cad, vinc = {}, {}
    if "Contratos" in wb.sheetnames:
        linhas = list(wb["Contratos"].iter_rows(values_only=True))
        cab = [texto(c) for c in linhas[0]]
        for ordem, r in enumerate(linhas[1:]):
            d = {k: valor_json(v) for k, v in zip(cab, r) if k}
            cod = codigo(texto(d.get("Contrato")))
            if cod:
                d["_ordem"] = ordem
                cad[cod] = d
    if "Vínculos SIAFE" in wb.sheetnames:
        linhas = list(wb["Vínculos SIAFE"].iter_rows(values_only=True))
        cab = [texto(c) for c in linhas[0]]
        for r in linhas[1:]:
            d = dict(zip(cab, r))
            ne, cod = texto(d.get("Nº do empenho")), codigo(texto(d.get("Contrato")))
            if ne and cod:
                vinc[ne.upper()] = cod
    return cad, vinc


# ---------- relatórios: o mais recente de cada conjunto de Unidades Gestoras ----------
arquivos = [a for a in sorted(ORIGEM.glob("*.xlsx")) if not a.name.startswith("~$")]
if not arquivos:
    raise SystemExit("Nenhum relatório .xlsx encontrado em Planilhas/SIAFE.")
por_ug = {}
for a in arquivos:
    info, regs = ler_relatorio(a)
    chave = tuple(sorted(info["ugs"]))
    atual = por_ug.get(chave)
    if not atual or (info["impressoEm"] or "", info["arquivo"]) > (atual[0]["impressoEm"] or "", atual[0]["arquivo"]):
        por_ug[chave] = (info, regs)
relatorios = sorted((v[0] for v in por_ug.values()), key=lambda i: i["ugs"])
linhas = [l for v in por_ug.values() for l in v[1]]
for r in relatorios:
    print(f"Relatório usado: {r['arquivo']} · {', '.join(r['ugs'])} · impresso em {r['impressoEm']} · {r['linhas']} linhas")

# ---------- contrato de cada empenho ----------
cadastro, vinculos = ler_cadastro()
por_credor = defaultdict(Counter)
for l in linhas:
    if c := codigo(l["obs"]):
        por_credor[l["credor"]][c] += 1
for l in linhas:
    ne = (l["ne"] or "").upper()
    cod = vinculos.get(ne) or codigo(l["obs"]) or (por_credor[l["credor"]].most_common(1)[0][0] if por_credor[l["credor"]] else None)
    l["contrato"] = cod
    l["semContrato"] = cod is None
    l["origemVinculo"] = "aba Vínculos SIAFE" if ne in vinculos else ("observação do empenho" if codigo(l["obs"]) else ("credor" if cod else None))

datas = [r["dadosAte"] for r in relatorios if r["dadosAte"]]
saida = {
    "atualizadoEm": datetime.now(timezone.utc).isoformat(),
    "dadosAte": min(datas) if datas else None,
    "relatorios": relatorios,
    "fonte": max(relatorios, key=lambda r: r["impressoEm"] or ""),  # compatibilidade
    "cadastro": cadastro,
    "linhas": linhas,
}
(DESTINO / "siafe.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
sem = {l["ne"] for l in linhas if l["semContrato"]}
semcad = sorted({l["contrato"] for l in linhas if l["contrato"] and l["contrato"] not in cadastro})
print(f"Arquivo gerado: site/siafe/dados/siafe.json · {len(linhas)} linhas · {len(sem)} empenho(s) sem contrato"
      + (f" · sem cadastro: {', '.join(semcad)}" if semcad else ""))
