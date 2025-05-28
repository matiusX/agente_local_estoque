"""Gera relatório quinzenal de progresso de um planejamento de estoque
usando um snapshot JSON estruturado + OpenAI LLM.

Requisitos:
- python-dotenv (para OPENAI_API_KEY) ou defina OPENAI_API_KEY em env.
- openai>=1.3.7 (nova lib)

Uso:
$ python generate_relatorio_quinzenal.py structured_analysis_eg.json  > relatorio_Q2.md
"""

from __future__ import annotations
import json, sys, textwrap, os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from openai import OpenAI, RateLimitError  # pip install openai>=1.3.7

MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.2
MAX_TOKENS = 2400  # suficiente p/ ~3k palavras

# ---------------------------------------------------------------------------
#  Utilidades
# ---------------------------------------------------------------------------

def load_snapshot(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def iso_to_pt(date_iso: str) -> str:
    return datetime.fromisoformat(date_iso).strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
#  Prompt Engineering
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent(
    """
    Você é um Analista Sênior de Planejamento de Estoques.
    Objetivo: produzir um **relatório quinzenal** claro, conciso e orientado a ação, usando os dados estruturados do snapshot JSON.
    • Sempre responda em **Markdown** bem formatado.
    • Apresente números com separador decimal vírgula e unidade, quando existir.
    • Realce alertas críticos com emoji 🔴 e conquistas com ✅.
    • Limite o **Resumo Executivo** a no máximo 200 palavras.
    • Assuma raciocínio analítico antes de escrever.
    """
)

HUMAN_PROMPT_TEMPLATE = textwrap.dedent(
    """
    ## CONTEXTO JSON
    ```json
    {context_json}
    ```

    ## TAREFA
    Gere o relatório quinzenal para o contratante **ID {contratante_id}**, cobrindo o período {periodo_str}.

    Estrutura esperada:
    1. **Resumo Executivo** (≤ 200 palavras)
    2. **Painel de Métricas-Objetivo**
       - Tabela: Métrica | Baseline | Atual | Meta | Δ% | Status
    3. **Tendências & Insights**
       - Destaque métricas observacionais relevantes (sem meta) com suas tendências.
    4. **Avaliação de Ações**
       - Tabela: Ação | Implementada | Eficácia | Métricas afetadas | Próximos Passos
    5. **Recomendações** (curto prazo ≤2 semanas & médio prazo)
       - Inclua matriz ICE (Impacto, Confiança, Esforço) 1-10-10.
    6. **Próximos Passos**

    Gere respostas num português formal, mas direto.
    """
)


def build_human_prompt(snapshot: Dict[str, Any]) -> str:
    """Gera o prompt de usuário com o JSON compacto (truncando métricas se >15)."""
    # Seleciona até 15 métricas (priorizando com target e alerts)
    metrics = snapshot["metrics"]
    target_metrics = [m for m in metrics if metrics[m].get("has_target")]
    observe_metrics = [m for m in metrics if not metrics[m].get("has_target")]
    selected = (
        target_metrics[:10]
        + observe_metrics[:5]
    )
    compact_metrics = {k: metrics[k] for k in selected}
    # substitui no contexto para ficar leve
    ctx = snapshot.copy()
    ctx["metrics"] = compact_metrics
    ctx_json = json.dumps(ctx, ensure_ascii=False, indent=2)[:6000]  # cabe no contexto

    periodo = f"{iso_to_pt(ctx['window']['start'])} – {iso_to_pt(ctx['window']['end'])}" if "window" in ctx else "(últimas 2 semanas)"

    return HUMAN_PROMPT_TEMPLATE.format(
        context_json=ctx_json,
        contratante_id=ctx.get("contratante_id", "?"),
        periodo_str=periodo,
    )


# ---------------------------------------------------------------------------
#  Geração de relatório
# ---------------------------------------------------------------------------

def generate_report(snapshot_path: str | Path) -> str:
    snapshot = load_snapshot(snapshot_path)
    human_prompt = build_human_prompt(snapshot)

    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": human_prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except RateLimitError as e:
        raise SystemExit(f"Chamada à API excedeu limite: {e}")


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_relatorio_quinzenal.py <snapshot.json> [saida.md]", file=sys.stderr)
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    report_md = generate_report(in_path)

    if out_path:
        out_path.write_text(report_md, encoding="utf-8")
        print(f"Relatório gravado em {out_path}")
    else:
        print(report_md)
