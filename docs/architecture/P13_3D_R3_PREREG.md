# P13-3D-R3 Pre-Registration

**Full Name**: P13-3D-R3 — Structure-Preserving Model-to-Paper Transmission Intervention
**Date**: 2026-09-07
**Status**: Draft

---

## 1. R2 Conclusion (Locked)

### 1.1 What R2 Found

R2 tested whether Model Quality advantage (B1-F > B0) reliably translates to Paper Quality advantage across 8 questions.

**Result**: It does not.

| Metric | Value |
|---|---|
| H10 (B1-F > B0 in ≥6/8) | **3/8 FAIL** |
| Mean ΔPaper | **-2.4** (negative!) |
| B1-F wins | 3 questions |
| B0 wins | 5 questions |

### 1.2 What R2 Revealed

**① Transmission is not monotonic.**

Higher Model Quality does not automatically produce higher Paper Quality under the baseline Writer.

**② Semantic Fidelity is high (~90%).**

Writer does not大量篡改 math. The problem is not "Writer writes equations wrong."

**③ P1 omission targets are meta-model elements.**

| Omitted Element | Count |
|---|---|
| candidate_models | 48 |
| selected_model | 24 |
| sensitivity_plan | 12 |
| variables | 3 |

Writer omits **epistemic structure** (model choice reasoning), not **mathematical structure** (equations/variables).

### 1.3 R2's Real Conclusion

> **Model Construction advantage does not automatically translate to Paper Quality advantage. The baseline Writer can transmit core mathematical structure but cannot reliably transmit model-level reasoning structure.**

This transforms P13-3D from "paper generation test" into **representation transformation / capability transmission research**.

---

## 2. R3 Research Question

> **Can explicit structural mapping between a frozen Model Artifact and the paper reduce meta-model omission without introducing unauthorized model mutation?**

This is NOT "optimize the Writer." It is: **intervene on the representation transformation layer and measure causal effects on transmission.**

---

## 3. Experimental Design: 2×3 Factorial

### 3.1 Factors

| Factor | Levels | Description |
|---|---|---|
| **Model** | B0, MMA, B1-F | Frozen from R2 (no changes) |
| **Writer** | W0, W1 | W0 = R2 baseline; W1 = mapping-assisted |

### 3.2 Cells

| | W0 (Baseline) | W1 (Mapping-assisted) |
|---|---|---|
| **B0** | R2 frozen paper | New paper |
| **MMA** | R2 frozen paper | New paper |
| **B1-F** | R2 frozen paper | New paper |

### 3.3 Paper Count

- **W0 papers**: 24 (already generated in R2, frozen)
- **W1 papers**: 24 (to generate in R3)
- **Total**: 48 papers

### 3.4 Why 2×3

Two independent questions:

**Question 1** (W1 vs W0): Does mapping intervention reduce meta-model omission?

**Question 2** (B1-F vs B0 under W1): Does mapping intervention recover Model → Paper transmission?

---

## 4. Writer Definitions

### 4.1 W0: Baseline Writer

Same as R2: fixed prompt, no structural mapping, no artifact→paper correspondence guidance.

### 4.2 W1: Mapping-Assisted Writer

W1 adds an **explicit intermediate mapping layer** between frozen artifact and paper.

**W1 MUST do:**

```
Frozen MODEL_ARTIFACT
        │
        ▼
┌───────────────────────┐
│ Claim Inventory        │
│                       │
│ What does model claim?│
│ (selected_model +     │
│  selection_reason)    │
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│ Element Map            │
│                       │
│ variable → section    │
│ parameter → section   │
│ constraint → section  │
│ mechanism → section   │
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│ Question Mapping       │
│                       │
│ Q1 → M1,M2            │
│ Q2 → M3               │
│ ...                   │
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│ Candidate Model Table  │
│                       │
│ Model A: pros/cons    │
│ Model B: pros/cons    │
│ → Selected: Model X   │
│ → Reason: ...         │
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│ Sensitivity Plan Map   │
│                       │
│ parameter → range     │
│ parameter → metric    │
└───────────────────────┘
        │
        ▼
      Writer
```

**W1 MUST NOT:**

- Add new variables, parameters, constraints, or mechanisms
- Modify existing equations or expressions
- Replace the selected model
- Change assumption statements
- Re-derive or re-justify model choices
- "Improve" the artifact in any way

**W1 is a representation mapper, not a model constructor.**

---

## 5. Metrics (Three Independent Dashboards)

### 5.1 Paper Quality

Same 4 dimensions as R2:
- Mathematical Correctness
- Problem Alignment
- Completeness
- Communication Quality

### 5.2 Structural Transmission Coverage (STC)

**Definition:**

$$
STC = \frac{\text{Artifact structural elements correctly represented in Paper}}{\text{Artifact structural elements required for paper}}
$$

**Decomposition:**

| STC Component | Definition |
|---|---|
| STC_variable | Variables correctly presented |
| STC_parameter | Parameters correctly presented |
| STC_constraint | Constraints correctly presented |
| STC_mechanism | Mechanisms correctly presented |
| STC_assumption | Assumptions correctly presented |
| STC_candidate_model | Candidate models compared |
| STC_selected_model | Selected model + reason presented |
| STC_sensitivity | Sensitivity plan presented |

**Key**: STC_candidate_model + STC_selected_model + STC_sensitivity are the **meta-model STC** components that R2 showed were omitted.

### 5.3 Unauthorized Mutation

Same as R2 Fidelity Gate:
- Addition
- Deletion
- Modification
- Renaming
- Semantic Drift

### 5.4 Four Possible Outcome States

| Paper Quality | STC | Mutation | Interpretation |
|---|---|---|---|
| ↑ | ↑ | ↓ | **Ideal**: mapping restores transmission |
| ↑ | ↓ | ↓ | Writer compressing model |
| ↓ | ↑ | ↓ | Model/paper expression issue |
| ↑ | ↑ | ↑ | **Dangerous**: Writer mutating model |

---

## 6. Hypotheses

### H13 — Structural Transmission

> **W1 significantly reduces meta-model omission (candidate_models, selected_model, sensitivity_plan) compared to W0.**

**Test**: STC_candidate_model, STC_selected_model, STC_sensitivity higher in W1 than W0.

**Criterion**: Each meta-model STC component increases by ≥15 percentage points.

### H14 — Paper Quality Recovery

> **W1 produces higher Paper Quality than W0.**

**Test**: Mean Paper Quality (4 dimensions) higher in W1 than W0 across 8 questions.

**Criterion**: Mean improvement ≥ 5 points.

### H15 — Capability Transmission Recovery

> **Under W1, B1-F Paper Quality > B0 Paper Quality, and the difference is larger than under W0.**

**Test**:
- (Paper(B1-F, W1) - Paper(B0, W1)) > (Paper(B1-F, W0) - Paper(B0, W0))

**Criterion**: ΔPaper(B1-F vs B0) under W1 > ΔPaper under W0 by ≥10 points.

### H16 — No Unauthorized Mutation

> **W1 does not significantly increase Unauthorized Model Mutation compared to W0.**

**Test**: Total mutations (additions + modifications + renamings) not significantly higher in W1 than W0.

**Criterion**: W1 mutations ≤ W0 mutations + 2 (across 8 questions).

### H17 — Mechanistic Mediation

> **STC improvement mediates Paper Quality improvement.**

**Test**: Correlation between STC improvement (W1-W0) and Paper Quality improvement (W1-W0) across 8 questions.

**Criterion**: Spearman ρ > 0.5 between ΔSTC and ΔPaper Quality.

---

## 7. Frozen Artifacts from R2

All 24 R2 papers (W0 condition) are frozen and serve as control:

| File | Condition |
|---|---|
| `{Q}_{letter}.md` | W0 paper (frozen) |

R3 generates only 24 new papers (W1 condition).

---

## 8. Execution Plan

### Phase 1: W1 Protocol Design

- [ ] Define mapping schema (Claim Inventory / Element Map / Question Map)
- [ ] Write W1 prompt with mapping instructions
- [ ] Validate W1 prompt on 1 test question

### Phase 2: W1 Paper Generation (24 papers)

- [ ] Generate 24 W1 Writer inputs (same 8Q × 3 arms)
- [ ] Generate 24 W1 papers
- [ ] Freeze W1 papers

### Phase 3: Evaluation

- [ ] Run Fidelity Gate v2 on 24 W1 papers
- [ ] Compute STC for all 48 papers (24 W0 + 24 W1)
- [ ] Blind Paper Quality evaluation on 24 W1 papers

### Phase 4: Analysis

- [ ] H13: Meta-model STC comparison (W1 vs W0)
- [ ] H14: Paper Quality comparison (W1 vs W0)
- [ ] H15: Capability transmission recovery
- [ ] H16: Unauthorized mutation check
- [ ] H17: STC → Paper Quality mediation

### Phase 5: Report

- [ ] Update P13_3D_REPORT.md
- [ ] Write R3 results

---

## 9. Expected产出

### Table 1: STC Comparison

| Component | W0 Mean | W1 Mean | Δ | p-value |
|---|---|---|---|---|
| STC_variable | ... | ... | ... | ... |
| STC_parameter | ... | ... | ... | ... |
| STC_constraint | ... | ... | ... | ... |
| STC_mechanism | ... | ... | ... | ... |
| STC_candidate_model | ... | ... | ... | ... |
| STC_selected_model | ... | ... | ... | ... |
| STC_sensitivity | ... | ... | ... | ... |

### Table 2: Paper Quality × Writer × Model

| | W0 | W1 | Δ |
|---|---|---|---|
| B0 | ... | ... | ... |
| MMA | ... | ... | ... |
| B1-F | ... | ... | ... |

### Table 3: Four Outcome States

| Condition | Quality | STC | Mutation | State |
|---|---|---|---|---|
| B0-W0 | ... | ... | ... | ... |
| B0-W1 | ... | ... | ... | ... |
| MMA-W0 | ... | ... | ... | ... |
| MMA-W1 | ... | ... | ... | ... |
| B1-F-W0 | ... | ... | ... | ... |
| B1-F-W1 | ... | ... | ... | ... |

---

## 10. Risk & Mitigation

| Risk | Mitigation |
|---|---|
| W1 still omits meta-model elements | Check mapping layer completeness |
| W1 introduces unauthorized mutations | Fidelity Gate catches additions |
| STC rubric too strict/loose | Pilot on 1 question, calibrate |
| H15 fails (B1-F still < B0 under W1) | Writer intervention insufficient; need deeper structural change |
