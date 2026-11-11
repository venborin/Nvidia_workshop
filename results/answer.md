# Improving the Coupled-Cluster Method: EOM-CC Accuracy, Cost, and Applications

## Range of Comparable Values

From the reviewed paper (Krylov, 2008), the following quantitative values can be fairly compared:

| Value | Unit | Context | Source |
|-------|------|---------|--------|
| 0.1–0.3 | eV | EOM-EE-CCSD error bars for excitation energies | p5 |
| 0.49 | eV | Singlet-triplet gap in meta-xylylene (1¹A₁ – X³B₂) | p10 |
| 1.19 | eV | Energy gap (2¹A₁ – X³B₂) in meta-xylylene | p10 |
| 0.5 | eV | Adiabatic singlet-triplet gap in meta-xylylene | p11 |
| 3.5 | eV | Energy window containing 7 states in 5-DMX triradical | p11 |
| 7 | states | Number of states in 5-DMX under 3.5 eV | p11 (flagged: word "seven") |
| 0.055 | eV | Error vs full CI for methylene ã¹A₁ – X³B₁ gap | p19 |
| 0.024 | eV | Error vs full CI for methylene b̃¹B₁ – X³B₁ gap | p19 |
| 8 | N | Scaling of full triples (N⁸) in EOM-CC | p20 |
| 6 | N | Scaling of EOM-CCSD and CISD (N⁶) | p4 |
| 1.3 | eV | Charge-resonance transition in benzene dimer cation | p14 |

All numeric values pass the checker; qualitative rows are flagged with reasons.

## Explanation and Supporting Rows

### Accuracy Improvements

The paper identifies several accuracy limitations of EOM-CCSD and proposes improvements:

1. **Doubly excited states**: EOM-CCSD fails for states dominated by double excitations (e.g., methylene c̃¹A₁, Z-state in twisted ethylene, dark states in polyenes) because leading configurations appear at different excitation levels and are not treated in a balanced fashion (p19, row 23).

2. **Spin contamination**: Even with spin-pure references, target SF states exhibit small spin contamination because single and double excitations from open-shell references do not form a spin-complete set (p20, row 10 flagged). The paper recommends implementing spin-adapted versions of EOM-SF/EE (p21, row 16 flagged).

3. **Orbital relaxation in EOM-IP/EA/DIP**: Error bars for EOM-IP/EA-CCSD are larger than for EOM-EE-CCSD due to more important orbital-relaxation effects (p20, row 11 flagged). Higher excitations (e.g., 3h2p for EOM-IP) seem necessary (ref 94, 95).

4. **EOM-DIP limitations**: The straightforward EOM-DIP implementation is unsatisfactory due to strong orbital-relaxation effects and physical instability of doubly attached references (p15, row 22 flagged).

Quantitative accuracy benchmarks:
- EOM-EE-CCSD error bars: 0.1–0.3 eV for excitation energies (p5, row 1)
- Methylene energy gaps vs full CI: 0.055 eV (ã¹A₁) and 0.024 eV (b̃¹B₁) (p19, rows 7–8)
- Meta-xylylene singlet-triplet gaps: 0.49 eV and 1.19 eV adiabatic (p10, rows 2–3); ~0.5 eV closed-shell singlet above triplet (p11, row 4)

### Computational Cost Improvements

The paper explicitly discusses scaling and cost reduction:

1. **Current scaling**: EOM-CCSD scales as N⁶ (same as CISD) (p4, row 18). Full triples scale as N⁸ (p20, row 12).

2. **Proposed cost-reduction approaches** (p21, row 17 flagged):
   - Perturbative rather than explicit inclusion of triple excitations (refs 106–113)
   - Methods-of-moments approach (refs 114, 115)
   - Active-space triples (refs 39, 116–119)
   - Energy-additivity schemes
   - Resolution-of-identity implementations (refs 122–124)
   - Reduced-scaling algorithms (refs 125, 126)
   - Parallelization

3. **Alternative strategies**: Fock-space detours and combined CC/EOM-CC schemes can solve problems at lower cost (p20, row 13 flagged; e.g., diradical/triradical stabilization energies, ref 75).

### New Applications

The paper demonstrates several applications beyond standard excitation energies:

1. **Diradicals and triradicals via EOM-SF**: Meta-xylylene (p10–11, rows 2–5) and 5-DMX with 7 states under 3.5 eV (p11, rows 5–6). EOM-SF provides balanced description and error cancellation for singlet-triplet gaps.

2. **Charge-transfer systems via EOM-IP**: Benzene dimer cation with 10 low-lying states; properly describes charge localization and charge-resonance transition at 1.3 eV (p13–14, rows 19, 20). EOM-IP overcomes failures of open-shell doublet references.

3. **EOM-DIP for sophisticated diradicals**: Lower cost than EOM-SF for four-electrons-in-three-orbitals systems (p15, row 21 flagged), though currently limited.

4. **Conical intersections, JT/pseudo-JT systems**: EOM's multistate nature and simultaneous inclusion of dynamical and non-dynamical correlation make it attractive (p21, flagged rows).

## Hypotheses Tested and Rejected

| Hypothesis | Test | Result |
|------------|------|--------|
| *Full triples (N⁸) are the only way to fix doubly excited states* | Paper proposes perturbative triples, active-space triples, methods-of-moments, similarity-transformed EOM-CC as cheaper alternatives (p20–21, rows 12–17 flagged) | **Rejected**: Multiple cheaper approaches exist |
| *Spin contamination is negligible in EOM-CCSD* | Paper states target states are "much more sensitive" than reference; residual contamination exists even with spin-pure references (p20, row 10 flagged) | **Rejected**: Spin adaptation needed for accuracy |
| *EOM-IP/EA has same accuracy as EOM-EE* | Paper states error bars are "larger" due to orbital relaxation (p20, row 11 flagged) | **Rejected**: EOM-IP/EA needs higher excitations |
| *EOM-DIP is a drop-in replacement for EOM-SF* | Paper: "performance... found unsatisfactory" due to orbital relaxation and reference instability (p15, row 22 flagged) | **Rejected**: Needs future development |

## Unexplained / Open Questions

1. **Quantitative cost–accuracy tradeoffs**: The paper lists many algorithmic improvements (RI, reduced-scaling, parallelization, active-space triples) but gives no quantitative comparison of their speedup or accuracy impact. No benchmarks are provided for the proposed methods.

2. **Spin-adaptation implementation status**: The paper calls spin adaptation "desirable" (ref 65) but does not report whether it has been implemented or what accuracy gain it yields.

3. **EOM-DIP future**: The paper says "hopefully future developments will resolve this problem" but gives no roadmap or timeline.

4. **Similarity-transformed EOM-CC**: Mentioned as "promising" (refs 120, 121) with no details on what it improves or its scaling.

5. **Transition metals / multiple bond breaking**: The paper notes these "warrant explorations of other sectors of Fock space (e.g., double SF and SF-DEA)" but does not quantify the difficulty or progress.

6. **Benchmark for active-space triples**: Ref 39 is cited but no numbers are given for cost reduction vs full triples.

7. **Error bars for EOM-IP/EA-CCSD**: The paper says they are "larger than those of EOM-EE-CCSD" but gives no numeric value.

8. **Scaling of proposed reduced-scaling algorithms**: Refs 125, 126 are cited but no target scaling (e.g., N⁵, N⁴) is stated.

## Conclusion

The paper (Krylov, 2008) provides a comprehensive review of EOM-CC methods as of 2008, identifying clear accuracy limitations (doubly excited states, spin contamination, orbital relaxation in IP/EA/DIP), computational bottlenecks (N⁶ for CCSD, N⁸ for full triples), and promising new applications (diradicals, triradicals, charge-transfer systems). It proposes multiple improvement directions—perturbative/active-space triples, spin adaptation, Fock-space detours, RI, reduced-scaling algorithms—but does not quantitatively benchmark them. The quantitative values extracted (0.1–0.3 eV EE error bars, 0.024–0.055 eV vs full CI for methylene, N⁶/N⁸ scaling, specific singlet-triplet gaps in model systems) provide a baseline for comparing later developments.