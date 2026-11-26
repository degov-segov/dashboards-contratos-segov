# Painéis de execução contratual — SEGOV/TJCE

Publicados em https://degov-segov.github.io/dashboards-contratos-segov/

| Painel | Endereço | De onde vêm os dados |
|---|---|---|
| **Execução Contratual** (verde-petróleo) | página inicial | `Planilhas/contratos.xlsx` — abas **Contratos**, **Empenhos** e **Pagamentos** (lançamento manual) |
| **Painel SIAFE** (violeta) | `/siafe/` | Relatórios do SIAFE-CE em `Planilhas/SIAFE/` (um por Unidade Gestora) |

O Painel SIAFE serve também de conferência: compare com a Execução Contratual para encontrar lançamentos que faltam na planilha.

## Como lançar empenhos e pagamentos (Execução Contratual)

1. Baixe a `Planilhas/contratos.xlsx` do repositório (abra o arquivo › botão de download).
2. Na aba **Empenhos** ou **Pagamentos**, acrescente uma linha ao final da tabela, uma por registro.
   - **Contrato**: escolha na lista (mesmo código da aba Contratos).
   - **Empenhos**: Tipo = Empenho (valor positivo) ou Anulação (valor negativo, com o Empenho de origem preenchido). Fonte / UG obrigatória na linha do Empenho.
   - **Pagamentos**: Empenho vinculado = número do empenho; Situação = Pago ou Em aberto. Fonte / UG em branco herda a do empenho.
   - Valores só com números (sem "R$"); datas como data.
3. Salve e envie para a pasta `Planilhas` (Add file › Upload files › Commit changes). O GitHub substitui a versão anterior.
4. Acompanhe na aba **Actions** (1 a 2 minutos) e atualize o painel com Ctrl+F5.

## Como atualizar o Painel SIAFE

1. No SIAFE-CE, exporte o relatório **Detalhamento das Despesas - Empenho, Liquidação e Pagamento - Ordem Cronológica**
   para a UG **040001** e para a UG **040101** (UOs 04100191 e 04200211), em Excel.
2. Esvazie a coluna H (**Credor**), mantendo o título: o repositório é público e o relatório traz CPF.
3. Salve como `SIAFE_040001_Contrapartida.xlsx` e `SIAFE_040101_Fermoju.xlsx` e envie para `Planilhas/SIAFE`
   (os arquivos com o mesmo nome são substituídos).

## Estrutura

- `scripts/converter.py` — lê a contratos.xlsx e gera `site/dados/execucao.json` (Execução Contratual).
- `scripts/converter_siafe.py` — lê os relatórios do SIAFE e gera `site/siafe/dados/siafe.json` (Painel SIAFE).
- `site/index.html`, `site/siafe/index.html`, `site/graficos.js` — páginas e gráficos.
- `.github/workflows/publicar.yml` — roda os conversores e publica no GitHub Pages a cada envio.
