#!/usr/bin/env python3
"""Воспроизводимая модель прогноза и окупаемости. Все входы — в model/params.json.
Запуск: python tools/econ.py projects/<имя>/model/params.json [--grid] [--csv путь]"""
import argparse, csv, json, sys


def surv_sum(c, L): return sum((1 - c) ** j for j in range(1, L + 1))


def run(cm, s):
    npg, hold, el, r0 = cm["numbers_per_group"], cm["holdout_share"], s["eligible_share"], s["rollout_month"]
    x = s["s_attrib"] * s["rho"]                    # относительное снижение оттока номеров
    c0, c1 = s["c0_monthly"], s["c0_monthly"] * (1 - x)
    treated_share = el * (1 - hold)
    g = lambda m: cm["start_groups"] + (cm["groups_nochange_end"] - cm["start_groups"]) * m / 12
    n_prev, months, cost = 0.0, 0.0, 0.0
    for m in range(r0, 13):
        n = g(m) * npg * treated_share
        new = n - n_prev; n_prev = n; L = 13 - m
        months += new * (surv_sum(c1, L) - surv_sum(c0, L))
        cost += n * s["direct_cost_rub_per_number_month"]
    gp = (months * cm["gp_per_month_rub"] - cost) / 1e6
    ge = 1 - (1 - cm["group_exit_annual"]) ** (1 / 12)
    groups_kept = sum(g(m) * treated_share * ge * x for m in range(r0, 13))
    end_t = cm["groups_nochange_end"] * treated_share
    n2 = cm["groups_nochange_end"] * npg * treated_share            # годовой темп, второй год
    m2 = n2 * (surv_sum(c1, 12) - surv_sum(c0, 12)); gp2 = (m2 * cm["gp_per_month_rub"] - n2 * 12 * s["direct_cost_rub_per_number_month"]) / 1e6
    return dict(extra_months=round(months), direct_cost_mln=round(cost / 1e6, 3), gp_delta_mln=round(gp, 3),
                gp_mln=round(cm["gp_nochange_mln"] + gp, 2), groups=round(cm["groups_nochange_end"] + groups_kept),
                active=round(cm["active_nochange"] + end_t * s["active_uplift_pp"]),
                activation_pct=round(100 * (cm["activation_nochange"] + treated_share * s["activation_uplift_pp"]), 1),
                owners=cm["owners_nochange"], rel_churn_drop_pct=round(100 * x, 1), y2_gp_delta_mln=round(gp2, 3))


def ceiling(cm, s):
    """Верхняя граница: отток в охваченных номерах обнулён (x=1)."""
    t = dict(s, s_attrib=1.0, rho=1.0); return run(cm, t)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("params"); ap.add_argument("--grid", action="store_true")
    ap.add_argument("--csv"); a = ap.parse_args(); P = json.load(open(a.params, encoding="utf-8")); cm = P["common"]
    res = {k: run(cm, v) for k, v in P["scenarios"].items()}
    gap_gp = cm["gp_target_mln"] - cm["gp_nochange_mln"]; need = gap_gp * 1e6 / cm["gp_per_month_rub"]
    print("| Показатель | Без изменений | Цель | " + " | ".join(res) + " |\n|---|---|---|" + "---|" * len(res))
    rows = [("Валовая прибыль, млн руб.", cm["gp_nochange_mln"], cm["gp_target_mln"], "gp_mln"),
            ("Активные группы (посл. месяц)", cm["active_nochange"], 8000, "active"),
            ("Подключённые группы (конец года)", cm["groups_nochange_end"], 12000, "groups"),
            ("Подключённые владельцы", cm["owners_nochange"], 2000, "owners"),
            ("Активация за 14 дней, %", 100 * cm["activation_nochange"], 60, "activation_pct")]
    for n, nc, t, k in rows: print(f"| {n} | {nc:g} | {t:g} | " + " | ".join(f"{res[s][k]:g}" for s in res) + " |")
    print("\nДоп. оплаченные месяцы / прямые расходы, млн / Δприбыли, млн / Δприбыли 2-й год, млн:")
    for s, r in res.items(): print(f"  {s}: {r['extra_months']} / {r['direct_cost_mln']} / {r['gp_delta_mln']} / {r['y2_gp_delta_mln']}")
    print(f"\nРазрыв по прибыли до цели: {gap_gp:g} млн = {need:,.0f} доп. оплаченных месяцев при {cm['gp_per_month_rub']} руб.")
    for L in (6, 3):
        print(f"  Эквивалент в новых группах ({cm['numbers_per_group']:g} номера, {L} мес. в году): {need/(cm['numbers_per_group']*L):,.0f} групп; "
              f"предельные расходы на группу до нулевой выгоды: {cm['numbers_per_group']*L*cm['gp_per_month_rub']:,.0f} руб.")
    if a.grid:
        print("\nПотолок эффекта удержания (отток обнулён у охваченных) при разных c0, база-сценарий:")
        for c0 in (0.01, 0.02, 0.03, 0.05, 0.08):
            r = ceiling(cm, dict(P["scenarios"]["base"], c0_monthly=c0)); print(f"  c0={c0:.0%}: Δприбыли ≤ {r['gp_delta_mln']} млн (доп. месяцев {r['extra_months']})")
    if a.csv:
        with open(a.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["scenario"] + list(next(iter(res.values())).keys()))
            for s, r in res.items(): w.writerow([s] + list(r.values()))


if __name__ == "__main__": main()
