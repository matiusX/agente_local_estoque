"""Construção do artefato estruturado (snapshot JSON) para monitoramento de planejamento de estoque.

Entradas
=======
- relacao_relevancia_planejamento_metrica.csv  ➜ lista de métricas relevantes, se há target, valor-alvo, unidade.
- metricas_extraidas.csv                       ➜ dados diários de 49 métricas   (id_contratante, data_extracao, m1..m49)
- problemas_identificados.csv                  ➜ id_problema, descricao
- acoes_planejamento.csv                       ➜ id_acao, descricao, impacto_esperado, data_impl (opcional)
- relation_action_problem_metrics.json         ➜ mapeia problema ⇄ ação ⇄ métricas

Saída
=====
- structured_snapshot_YYYYMMDDTHHMM.json  ➜ artefato descrito no design anterior

Como funciona
=============
1. ETL: lê todos os CSV/JSON, filtra contratante/plano.
2. Calcula baseline (primeiro dia) e current (último dia) para cada métrica.
3. Para cada métrica ➜ delta_abs, delta_pct, slope_7d, trend, status.
4. Constrói blocos problems, actions, metrics usando os relacionamentos.
5. Detecta alerts (regras simples).
6. Chama LLM **apenas** para gerar `llm_summary` (headline curtinha).
7. Serializa em JSON, grava em diretório particionado.

Uso
---
$ python build_structured_snapshot.py --input_dir ./data --contratante 45 --planejamento 123 --out snapshot/snapshots
"""
from __future__ import annotations
import argparse, json, os, sys, textwrap
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

import pandas as pd
from dateutil import parser as dtparser

# OpenAI é opcional; importe só se chave existir
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

################################################################################
# Configuráveis
################################################################################
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.2
MAX_TOKENS = 120
EPSILON = 0.1  # limiar mínimo de slope por dia (ajustável)
FAST_FACTOR = 2  # slope > 2*epsilon => *_fast
ALERT_DELTA_PCT = 15  # desv pct p alerta se meta

################################################################################
# Utilidades de data & metrica
################################################################################

def slope(series: pd.Series) -> float:
    """Inclinação por dia numa regressão linear simples (x=dia ordinal)."""
    if len(series) < 2:
        return 0.0
    y = series.values
    x = (series.index - series.index[0]).days.values
    # coeficiente β1 = cov(x,y)/var(x)
    cov = ((x - x.mean()) * (y - y.mean())).mean()
    var = ((x - x.mean()) ** 2).mean()
    return float(cov / var) if var else 0.0


def classify_trend(slp: float, eps: float = EPSILON, fast_factor: int = FAST_FACTOR) -> str:
    if abs(slp) < eps:
        return "flat"
    if slp > 0:
        return "up_fast" if slp >= fast_factor * eps else "up"
    else:
        return "down_fast" if slp <= -fast_factor * eps else "down"

################################################################################
# LLM prompt para llm_summary
################################################################################
SYSTEM_PROMPT = (
    "Você é um analista sênior de planejamento de estoques. Escreva um resumo de até 120 caracteres, "+
    "mencionando o principal risco ou alerta e a principal conquista no período, em português."
)

HUMAN_TEMPLATE = textwrap.dedent(
    """
    ALERTAS CRÍTICOS:
    {alertas}

    MÉTRICAS ABAIXO DA META: {qt_baixo}
    MÉTRICAS DENTRO/ACIMA DA META: {qt_ok}
    """
)

################################################################################
# Pipeline principal
################################################################################

def build_snapshot(args: argparse.Namespace) -> Dict[str, Any]:
    base_dir = Path(args.input_dir)

    # 1. Carregar CSVs/JSON ---------------------------------------------------
    df_relev = pd.read_csv(base_dir / "relacao_relevancia_planejamento_metrica.csv")  # columns: metric_id, has_target, target
    df_extr = pd.read_csv(base_dir / "metricas_extraidas.csv")  # id_contratante, data_extracao, …
    df_prob  = pd.read_csv(base_dir / "problemas_identificados.csv")  # problem_id, descricao
    df_acoes = pd.read_csv(base_dir / "acoes_planejamento.csv")       # action_id, descricao, impacto_esperado, implementada_em

    with open(base_dir / "relation_action_problem_metrics.json", "r", encoding="utf-8") as fp:
        rel_map = json.load(fp)

    contratante = args.contratante
    df_extr = df_extr[df_extr["id_contratante"] == contratante].copy()
    if df_extr.empty:
        raise SystemExit("Nenhum dado encontrado para id_contratante fornecido.")

    # converter col data_extracao
    df_extr["data_extracao"] = pd.to_datetime(df_extr["data_extracao"])
    df_extr.sort_values("data_extracao", inplace=True)

    # Baseline & current ------------------------------------------------------
    baseline_ts = df_extr["data_extracao"].iloc[0]
    current_ts  = df_extr["data_extracao"].iloc[-1]

    metrics_dict: Dict[str, Any] = {}

    metric_cols = [c for c in df_extr.columns if c not in ("id_contratante", "data_extracao")]
    for metric_id in metric_cols:
        series = df_extr.set_index("data_extracao")[metric_id].dropna()
        if series.empty:
            continue
        baseline_val = float(series.iloc[0])
        current_val  = float(series.iloc[-1])
        delta_abs = current_val - baseline_val
        delta_pct = (delta_abs / baseline_val * 100) if baseline_val != 0 else None

        # slope em janela 7 dias ------------------------------------------------
        last7 = series[last_window(series.index, days=7)]
        slp = slope(last7) if len(last7) >= 2 else 0.0
        trend = classify_trend(slp)

        # target ---------------------------------------------------------------
        row_target = df_relev[df_relev["metric_id"] == metric_id]
        has_target = bool(row_target["has_target"].iloc[0]) if not row_target.empty else False
        target_val = float(row_target["target"].iloc[0]) if has_target else None

        # status ---------------------------------------------------------------
        status = "sem_meta"
        if has_target and target_val is not None:
            # menor = melhor ou maior = melhor ? simplificamos: assume target é valor máximo permitido
            status = (
                "acima_meta" if current_val < target_val else
                "abaixo_meta" if current_val > target_val else
                "dentro_meta"
            )

        metrics_dict[metric_id] = {
            "name": metric_id,
            "has_target": has_target,
            "baseline": baseline_val,
            "current": current_val,
            "target": target_val,
            "delta_abs": delta_abs,
            "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
            "slope_7d": round(slp, 3),
            "trend": trend,
            "status": status,
            # placeholders, serão preenchidos depois
            "problem_ids": [],
            "action_ids": []
        }

    # 2. Preencher relationships ---------------------------------------------
    problems_block: List[Dict[str, Any]] = []
    actions_block: List[Dict[str, Any]] = []

    # inversos para fácil atribuição
    metric_to_problems: Dict[str, List[str]] = {}
    metric_to_actions: Dict[str, List[str]] = {}

    # problems
    for pid, pdata in rel_map["problems"].items():
        p_metrics = pdata["metric_ids"]
        p_actions = pdata["action_ids"]

        problems_block.append({
            "problem_id": pid,
            "descricao": df_prob.loc[df_prob["problem_id"] == int(pid), "descricao"].squeeze() if not df_prob.empty else "",
            "status": "em_andamento",
            "metric_ids": p_metrics,
            "action_ids": p_actions
        })
        for m in p_metrics:
            metric_to_problems.setdefault(m, []).append(pid)

    # actions
    for aid, adata in rel_map["actions"].items():
        a_metrics = adata["metric_ids"]
        a_row = df_acoes.loc[df_acoes["action_id"] == int(aid)] if not df_acoes.empty else pd.DataFrame()
        actions_block.append({
            "action_id": aid,
            "descricao": a_row["descricao"].squeeze() if not a_row.empty else "",
            "implementada_em": a_row["implementada_em"].squeeze() if "implementada_em" in a_row else None,
            "problem_ids": rel_map["problems"].get(str(aid), {}).get("problem_ids", []),
            "metric_ids": a_metrics,
            "impacto_esperado": a_row["impacto_esperado"].squeeze() if "impacto_esperado" in a_row else None,
            "observado": None,  # calculado abaixo
            "eficacia": None,
            "recomendacao": None
        })
        for m in a_metrics:
            metric_to_actions.setdefault(m, []).append(aid)

    # atribuir inversos na métrica
    for mid, mdict in metrics_dict.items():
        mdict["problem_ids"] = metric_to_problems.get(mid, [])
        mdict["action_ids"] = metric_to_actions.get(mid, [])

    # 3. Eficácia de ações -----------------------------------------------------
    def evaluate_action(action: Dict[str, Any]):
        exp = action.get("impacto_esperado")
        met_ids = action["metric_ids"]
        deltas = [metrics_dict[m]["delta_abs"] for m in met_ids if m in metrics_dict]
        if not deltas:
            return None, None, None
        mean_delta = sum(deltas) / len(deltas)
        # heurística: se impacto_esperado começar com '+/-X', comparar sinal
        efficacy = "média"
        if exp and isinstance(exp, str):
            sign_exp = -1 if "-" in exp else 1
            if sign_exp * mean_delta < 0:
                efficacy = "contrária"
            elif abs(mean_delta) >= abs(sign_exp):
                efficacy = "alta"
            else:
                efficacy = "baixa"
        action["observado"] = round(mean_delta, 2)
        action["eficacia"] = efficacy
        action["recomendacao"] = "manter" if efficacy == "alta" else "ajustar"

    for action in actions_block:
        evaluate_action(action)

    # 4. Alertas --------------------------------------------------------------
    alerts: List[Dict[str, Any]] = []
    for mid, mdict in metrics_dict.items():
        if mdict["status"] == "abaixo_meta" and abs(mdict["delta_pct"] or 0) > ALERT_DELTA_PCT:
            alerts.append({
                "metric": mid,
                "issue": "abaixo_meta",
                "detail": f"{mid} {mdict['current']} acima da meta {mdict['target']}",
                "severity": "alta",
                "timestamp": datetime.utcnow().isoformat()
            })
        if mdict["trend"] in ("up_fast", "down_fast"):
            alerts.append({
                "metric": mid,
                "issue": mdict["trend"],
                "detail": f"Tendência {mdict['trend']} (slope {mdict['slope_7d']})",
                "severity": "média",
                "timestamp": datetime.utcnow().isoformat()
            })

    # 5. LLM summary ----------------------------------------------------------
    llm_summary = ""
    if OpenAI and os.getenv("OPENAI_API_KEY"):
        qt_baixo = sum(1 for m in metrics_dict.values() if m["status"] == "abaixo_meta")
        qt_ok    = sum(1 for m in metrics_dict.values() if m["status"] in ("dentro_meta","acima_meta"))
        top_alerts = [f"{al['metric']} – {al['issue']}" for al in alerts[:3]]
        human_prompt = HUMAN_TEMPLATE.format(alertas="; ".join(top_alerts) or "nenhum", qt_baixo=qt_baixo, qt_ok=qt_ok)
        client = OpenAI()
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":human_prompt}
            ]
        )
        llm_summary = resp.choices[0].message.content.strip()

    # 6. Montar snapshot dict --------------------------------------------------
    snapshot = {
        "schema_version": 1,
        "planejamento_id": args.planejamento,
        "contratante_id": contratante,
        "run_timestamp": datetime.utcnow().isoformat(),
        "window": {
            "start": baseline_ts.date().isoformat(),
            "end": current_ts.date().isoformat()
        },
        "problems": problems_block,
        "actions": actions_block,
        "metrics": metrics_dict,
        "alerts": alerts,
        "llm_summary": llm_summary,
        "next_report_due": (current_ts + timedelta(days=15)).date().isoformat()
    }

    return snapshot

################################################################################
# Helpers
################################################################################

def last_window(idx: pd.DatetimeIndex, days: int = 7) -> pd.DatetimeIndex:
    """Retorna True/False mask p/ última janela de 'days' dias."""
    end = idx.max()
    start = end - timedelta(days=days)
    return (idx >= start) & (idx <= end)

################################################################################
# CLI
################################################################################

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gera artefato estruturado de análise de progresso")
    p.add_argument("--input_dir", required=True, help="Diretório onde estão os CSV/JSON de entrada")
    p.add_argument("--contratante", type=int, required=True, help="ID do contratante")
    p.add_argument("--planejamento", type=int, required=True, help="ID do planejamento")
    p.add_argument("--out", required=True, help="Path destino (arquivo ou dir). Use s3:// para S3")
    return p.parse_args()


def save_snapshot(snapshot: Dict[str, Any], out_path: str):
    data = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if out_path.startswith("s3://"):
        import boto3, re
        match = re.match(r"s3://([^/]+)/(.+)", out_path)
        if not match:
            raise ValueError("Path S3 inválido")
        bucket, key = match.groups()
        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucket, Key=key, Body=data.encode("utf-8"))
    else:
        Path(out_path).write_text(data, encoding="utf-8")


if __name__ == "__main__":
    args = parse_args()
    snap = build_snapshot(args)

    # gerar path se for diretório
    out = args.out
    if out.endswith("/") or os.path.isdir(out):
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out = os.path.join(out, f"structured_snapshot_{ts}.json")

    save_snapshot(snap, out)
    print(f"Snapshot gerado em {out}")
