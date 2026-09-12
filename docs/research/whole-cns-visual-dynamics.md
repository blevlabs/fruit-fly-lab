# Registered light input and estimated graded visual dynamics

This report records a historical study conducted in September 2026; its numerical results are not new package checks. See the [current status](../status.md), [research roadmap](../roadmap.md), and [public results index](../../results/README.md). Original evidence filenames below identify the historical provenance archive; the results index lists artifacts included in this release.

The visual-input implementation studied here samples **5,713 photoreceptors through 1,694 optical
columns**. The exact author vectors, their official-column joins and the
connectivity-based R1–R6 inference are documented in
[the sensory mapping report](malecns-sensory-mapping.md). This implements an
optical input path, not validated motion vision or full visual physiology.

## Physical observation

[cns_vision.py](../../runtime/cns_vision.py) aligns the author's +x-forward/+y-left/+z-dorsal vectors to the
NeuroMechFly head frame. Each ray starts just outside the corresponding eye
mesh's corneal intersection. Native MuJoCo ray intersections include the fly,
ground and enabled source objects. The head's current world rotation and
translation transform the cached local rays on every optical sample.

This is an **estimated registration between specimens**. Eye-mesh centers and
surface intersections do not identify measured ommatidial optical origins.
Missing column/direction chains remain unconnected; no nearest-neighbor or
behavior-based correspondence is invented. The 378 unmapped compound-eye entries
remain in the central graph with their dark/resting compartment dynamics.

Sampling occurs every 2 ms of simulated time, independent of transport packet
size. Source placement changes refresh the sample immediately; pause stops
neural and physical time. The optical model studied here is broadband and diffuse:
sky radiance is 1, and ground/food/body albedos are .3/.15/.1. These are explicit
environment estimates. All food has the same optical albedo regardless of
taste, odor or temperature. Diagnostic odor halos occupy excluded geometry
group 5. Display recoloring and translucent cuticle views do not change the optical input.

There is no object detector, food classifier, destination vector or visual
motor command. A visible source changes photons/radiance at mapped receptors.
Spectra, UV/polarization, optical acceptance angles, shadows, microvilli and
adaptation remain missing.

## Graded cells in the recurrent graph

Fly photoreceptors depolarize with light and release transmitter through graded
dynamics. Their synaptic feedback is functionally consequential; it must not be
discarded by overwriting receptor voltage with an external response trace.
[Drosophila photoreceptor recordings](https://pmc.ncbi.nlm.nih.gov/articles/PMC4801898/)
and [network feedback experiments](https://pmc.ncbi.nlm.nih.gov/articles/PMC2628722/)
motivate the continuous compartment model. The primary
[L1/L2 recording study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8018773/)
supports light-evoked histaminergic hyperpolarization and cholinergic network
contributions to recovery. These studies do not calibrate the parameters below
for the MaleCNS specimen.

`VisualHybrid` retains Eon's released-edge synapse integrator and LIF dynamics
for other cells. All annotated compound-eye photoreceptors and exact L1/L2 types
use a continuous voltage with **no spike threshold/reset**. Both incoming and
outgoing measured connections remain active. For a photoreceptor:

```text
I_photo = I_max * radiance / (radiance + K)
V_next = V + (1 - exp(-dt/tau)) * (G + I_photo - (V - V_dark))
release = dt * R_max * sigmoid((V - V_mid) / slope)
```

L1/L2 use the same graded voltage/release law with no photo current and Eon's
rest potential. The synapse integrator interprets release in equivalent event
units so it can share the original recurrent matrix. **This is a model-unit
conversion, not a claim that graded neurons fire at that event rate.** Actual
spike counters explicitly exclude every graded output. The published consensus
histamine signs are retained; postsynaptic receptor specificity and R8
cotransmission remain unresolved.

The studied values are specified in [cns-model.json](../../runtime/cns-model.json): photoreceptor dark rest −60 mV;
maximum equivalent photo current 30 mV; half-saturation .5 relative radiance;
voltage time constant 20 ms; sigmoid midpoint −50 mV and slope 4 mV; maximum
release 200 equivalent events/s; coarse voltage bounds −90 to +20 mV.
**These are uncalibrated compartment hypotheses.** They were not optimized for
approach, posture, motor activity or any desired behavior. The shared sigmoid
does not reproduce cell-specific release physiology. Many additional optic-lobe
types have graded responses; their remaining LIF approximation is a material
limitation, not complete visual-circuit physiology.

The initialized graph is not at a measured physiological equilibrium. Graded
release is tonic, and illuminated scenes can produce neural activity without
odor or taste. This is different from the former all-LIF zero-input test and
must not be described as chemical stimulus-driven activity.

## Checks and boundaries

The historical [sensory check](../../tests/check_cns_senses.py) passed exact sugar/bitter identity checks, chemical–optical
isolation, physical object occlusion, changed rays after object movement and
head-frame rotation. The tested object move changes 148 receptor observations.
Original artifact: `cns/sensory-check.json`.

The historical visual-neuron check passed on a separate synthetic two-cell
fixture: graded light depolarization, tonic bounded release, delayed inhibitory
transmission to L1, finite state and exact reset. The fixture's synthetic edge
is never imported into the actual CNS. Original artifact: `cns/visual-neuron-check.json`.

These checks establish implementation properties. They do not establish normal
fly vision, learned recognition, visual navigation or a whole-animal response.

## Deterministic GPU recurrence

Continuous release exposed repeat-to-repeat rounding differences in
CUDA CSR matrix multiplication in the historical study (up to .00390625 in a fixed random-vector probe).
The studied implementation uses native sparse `torch.bmm` with deterministic algorithms
enabled. The same probe repeats bitwise; full neuronal state also repeats
exactly after seed reset. This changes the reduction algorithm, not the graph,
physiology parameters or desired output. A 50-call warm benchmark measured
about .579 ms per deterministic multiplication versus .381 ms for the former
CSR operation in the historical benchmark. Whole-loop speed includes other work.
[PyTorch reproducibility documentation](https://docs.pytorch.org/docs/stable/notes/randomness.html)
describes the deterministic sparse-bmm path.
