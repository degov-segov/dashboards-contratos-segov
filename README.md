# Painéis de execução contratual — SEGOV/TJCE

Publicados em https://degov-segov.github.io/dashboards-contratos-segov/

- **Execução Contratual** (página inicial, verde-petróleo): contratos com valor global, vigência e limites, execução vinda do SIAFE.
- **Painel SIAFE** (`/siafe/`, violeta): visão orçamentária e financeira do relatório do SIAFE.

## Modelo de atualização

| O que | Onde | Quem atualiza | Quando |
|---|---|---|---|
| Empenhos, liquidações e pagamentos | `Planilhas/SIAFE/` — relatórios do SIAFE-CE | Upload do relatório, sem editar | Sempre que quiser atualizar os números |
| Cadastro dos contratos (valor global, vigência, limites) | `Planilhas/contratos.xlsx`, aba **Contratos** | Digitação | Contrato novo, aditivo ou mudança de limite |
| Empenhos sem código de contrato na observação | `Planilhas/contratos.xlsx`, aba **Vínculos SIAFE** | Digitação (Nº do empenho → Contrato) | Quando o painel avisar |

As abas Empenhos e Pagamentos da contratos.xlsx não são mais usadas pelos painéis e podem ficar como histórico.

## Como atualizar os dados do SIAFE

1. No SIAFE-CE, gere o relatório **Detalhamento das Despesas - Empenho, Liquidação e Pagamento - Ordem Cronológica**,
   com o filtro da Unidade Gestora e das unidades orçamentárias da SEGOV, e exporte em Excel (.xlsx).
   Faça um relatório para cada Unidade Gestora: **040001 (Contrapartida)** e **040101 (Fermoju)**.
2. Antes de enviar, apague o conteúdo da coluna H (**Credor**) nas linhas de pessoas físicas, ou da coluna inteira
   (mantendo o título): o repositório é público e o relatório traz CPF completo.
3. No GitHub, abra `Planilhas/SIAFE` › **Add file** › **Upload files**, envie os arquivos e clique em **Commit changes**.
4. Acompanhe a publicação na aba **Actions** (1 a 2 minutos) e atualize o painel com Ctrl+F5.

Para cada Unidade Gestora vale o relatório mais recente da pasta (data "Impresso em"); os antigos podem ser apagados.

## Estrutura

- `scripts/converter_siafe.py` — junta os relatórios do SIAFE com o cadastro e gera `site/siafe/dados/siafe.json`.
- `scripts/converter.py` — conversor da planilha antiga (mantido por compatibilidade).
- `site/index.html` — painel de Execução Contratual · `site/siafe/index.html` — Painel SIAFE · `site/graficos.js` — gráficos.
- `.github/workflows/publicar.yml` — roda os conversores e publica no GitHub Pages a cada envio.
