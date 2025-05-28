```markdown
# Análise de Problemas de Inventário

Este documento fornece uma análise dos problemas de inventário identificados usando os dados de KPI fornecidos. Cada problema é analisado em termos de KPIs relevantes, possíveis causas raízes e impacto financeiro estimado.

## Problema 1: Alta Percentagem de SKUs com Estoque Zero

| **Descrição do Problema** | Alta percentagem de SKUs com estoque zero (20% dos SKUs têm estoque zero, 2.000 de um total de 10.000 SKUs) |
|---------------------------|-------------------------------------------------------------------------------------------------------------|
| **KPIs Relevantes**       | - TOTAL SKU COM ESTOQUE ZERO: 2.000 <br> - %SKU COM ESTOQUE ZERO: 20% <br> - TOTAL SKU ATIVO (ESTOQUE <= 0): 2.000 (20%) |
| **Possíveis Causas**      | - Previsão de demanda ineficiente levando a rupturas de estoque <br> - Disrupções na cadeia de suprimentos afetando o reabastecimento <br> - Práticas inadequadas de gestão de inventário |
| **Impacto Financeiro**    | - Potenciais vendas perdidas devido a rupturas de estoque, impactando a receita <br> - Insatisfação do cliente levando à perda de vendas futuras |

## Problema 2: Capital Imobilizado Significativo em SKUs Inativos com Estoque

| **Descrição do Problema** | Capital imobilizado significativo em SKUs inativos com estoque (4% dos SKUs estão inativos, mas ainda têm estoque, com um custo total de $30.000) |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| **KPIs Relevantes**       | - TOTAL SKU INATIVO (ESTOQUE > 0): 400 <br> - %SKU INATIVO (ESTOQUE > 0): 4% <br> - CUSTO TOTAL INATIVO (ESTOQUE > 0): $30.000 |
| **Possíveis Causas**      | - Gestão de giro de inventário deficiente <br> - Falta de gestão do ciclo de vida do produto <br> - Estratégias ineficazes de liquidação para itens de baixa movimentação |
| **Impacto Financeiro**    | - $30.000 imobilizados em inventário não performante <br> - Aumento dos custos de manutenção e risco de obsolescência |

## Problema 3: Presença de SKUs com Estoque Negativo

| **Descrição do Problema** | Presença de SKUs com estoque negativo (2% dos SKUs têm estoque negativo, totalizando um custo de $20.000) |
|---------------------------|-----------------------------------------------------------------------------------------------------------|
| **KPIs Relevantes**       | - TOTAL SKU COM ESTOQUE NEGATIVO: 200 <br> - %SKU COM ESTOQUE NEGATIVO: 2% <br> - CUSTO TOTAL ESTOQUE NEGATIVO: $20.000 |
| **Possíveis Causas**      | - Erros no rastreamento e gestão de inventário <br> - Entrada de dados imprecisa ou erros de sistema <br> - Falta de atualizações em tempo real do inventário |
| **Impacto Financeiro**    | - $20.000 em potenciais discrepâncias financeiras <br> - Ineficiências operacionais e potenciais imprecisões nos relatórios financeiros |

## Problema 4: Alta Percentagem de SKUs Não Comercializados, mas com Estoque

| **Descrição do Problema** | Alta percentagem de SKUs não comercializados, mas com estoque (2% dos SKUs não são comercializados, mas ainda têm estoque, com um custo total de $20.000) |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **KPIs Relevantes**       | - TOTAL SKU NAO COMERCIALIZADO (ESTOQUE > 0): 200 <br> - %SKU NAO COMERCIALIZADO (ESTOQUE > 0): 2% <br> - CUSTO TOTAL NAO COMERCIALIZADO (ESTOQUE > 0): $20.000 |
| **Possíveis Causas**      | - Gestão ineficaz do portfólio de produtos <br> - Falta de alinhamento entre estratégias de vendas e inventário <br> - Atrasos nos processos de descontinuação de produtos |
| **Impacto Financeiro**    | - $20.000 em inventário que não contribui para a receita <br> - Aumento dos custos de manutenção e risco de obsolescência |

## Problema 5: Dias de Cobertura de Inventário Excessivos para SKUs do Grupo C

| **Descrição do Problema** | Dias de cobertura de inventário excessivos para SKUs do Grupo C (Grupo C tem 110 dias de cobertura) |
|---------------------------|------------------------------------------------------------------------------------------------------|
| **KPIs Relevantes**       | - TOTAL SKU GRUPO C: 5.000 <br> - %SKU GRUPO C: 50% <br> - COBERTURA EM DIAS GRUPO C: 110 |
| **Possíveis Causas**      | - Superestimação da demanda para itens de baixo valor <br> - Políticas de reabastecimento de inventário ineficientes <br> - Falta de foco na otimização dos níveis de inventário para itens de menor impacto |
| **Impacto Financeiro**    | - Capital imobilizado em inventário excessivo <br> - Aumento do risco de obsolescência e custos de manutenção |

Esta análise destaca a necessidade de melhorar as práticas de gestão de inventário, incluindo melhor previsão de demanda, rastreamento de inventário e gestão do ciclo de vida do produto, para abordar esses problemas de forma eficaz.
```