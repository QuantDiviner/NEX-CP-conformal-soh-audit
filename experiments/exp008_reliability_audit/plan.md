# exp008_reliability_audit Plan

## Objective

Execute the abandon-forward RESS framework revision as a bounded reliability and
safety audit. The experiment must not try to prove method superiority. It must
quantify when conformal SOH intervals are trustworthy, when protocol
non-exchangeability breaks them, and what the safety-decision consequences are.

## Inputs

- Real CALCE, NASA, and Oxford SOH data only.
- Existing QA outputs and splits from exp001-exp007.
- Existing exp007 methods and outputs:
  `persistence_anchor_protocol_mondrian_cp`, `qr_gradient_boosting`,
  `cqr_gradient_boosting`, and `ngboost_normal_cqr`.

Synthetic data is forbidden.

## Required Analyses

1. Operational `prev_soh` availability audit
   - Classify each reported task as nowcasting, one-step forecasting, or
     lag-constrained forecasting.
   - Recompute or bound results under decision-time feature availability.
   - If `prev_soh` is unavailable, downgrade the claim instead of imputing it.

2. Coverage-aligned baseline comparison
   - Compare methods under the same tasks, splits, and bootstrap protocol.
   - Report coverage, width, RMSE, and decision utility.
   - Add a coverage-aligned view where possible: compare width and decision
     utility at comparable empirical coverage rather than raw selected q only.

3. Double-coverage and subgroup reliability
   - Report marginal coverage plus dependence-aware cell/block coverage.
   - Report per-domain, per-cell, and degradation-stage failure clusters.
   - Preserve failed cells/tasks as evidence, not as outliers to hide.

4. Shift-to-failure diagnostics
   - Quantify calibration/test representativeness using available feature,
     residual, and SOH-stage distributions.
   - Link shift magnitudes to coverage collapse for CALCE/NASA/Oxford tasks.
   - Avoid physical-mechanism claims not supported by the data.

5. Decision-utility uncertainty
   - Add bootstrap CIs for false-safe, false-alarm, and uncertain rates at SOH
     thresholds 0.80 and 0.70.
   - Provide cost curves over false-safe/false-alarm cost ratios.
   - State the minimum viable policy: trust, recalibrate first, or abstain.

## Success Criteria

The plan succeeds if it produces a coherent RESS reliability-audit evidence
packet with:

- no synthetic data;
- no method-superiority, Neural-ODE, NEX-CP, or broad-transfer claim;
- explicit trust/failure boundaries with dependence-aware uncertainty;
- decision-utility uncertainty for SOH thresholds;
- a reproducible run manifest and all outputs listed in metadata.

## Review Gate

After execution, create Step 07 review artifacts and run a clean-room experiment
review with external-AI wall timeouts of at least 1800 seconds. Use 2400 seconds
by default for formal review/FPA calls.
