# Feasibility Guard: exp003_cross_protocol

Time: 20260520_023453

## Stage 1 Mechanical Checks
- [x] results/metrics.json exists
- [x] metrics JSON parseable
- [x] synthetic data not declared
- [x] target coverage present
- [x] no NaN/Inf float values in metrics

## Gate 3 Findings
- P0: Cross-protocol success criterion failed for: target_recalibrated_CALCE: coverage=0.8618153667505323, ci_low=0.8524057088916567; leave_NASA_out: coverage=0.8608100399315459, ci_low=0.844606021434138
- Pass-note: Cross-protocol criterion passed for: leave_CALCE_out: coverage=0.9051189245087901, ci_low=0.8997868668950517; target_recalibrated_NASA: coverage=0.9272030651340997, ci_low=0.9090052534526982; leave_Oxford_out: coverage=0.9884393063583815, ci_low=0.9792424512950195; target_recalibrated_Oxford: coverage=0.927038626609442, ci_low=0.893644235743093
- P1: Report per-protocol and per-cell coverage; aggregate domain coverage can mask non-exchangeability.
- P1: Disclose persistence-anchor dependence and compare all selected models against persistence baseline.
