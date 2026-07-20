# Implementation prompt: Data Monitoring Pipeline (cross-hospital-platform repo)

Paste this whole document into Claude Code as your task instructions. This targets the
**existing** `cross-hospital-platform` repository — you are modifying real files, not
building from scratch. Read `CLAUDE.md` in the repo root first; if anything in it
conflicts with this document, stop and flag the conflict rather than silently picking
one.

## Context

The repo already has a working FastAPI pipeline: `POST /v1/clinical/inference/ingest`
uploads an image to MinIO, creates an `InferenceRequest` row, runs
`ClinicalPipelineOrchestrator.execute_pipeline`, which currently does drift detection
via `MedicalDriftDetector` (Alibi Detect `KSDrift`), a hard-coded mock inference,
persists a `DriftLog`, and logs telemetry to MLflow. `POST /v1/clinical/feedback/submit`
handles the human-in-the-loop ground-truth loop and is already correct — don't touch it.

**What's currently wrong, and what this task fixes:**

1. `MedicalDriftDetector.__init__` builds its baseline from a **random tensor**, not
   real CheXpert data. It needs a genuine CheXpert-derived reference distribution.
2. `detect_image_drift` computes drift on **raw flattened pixels** (grayscale, resize
   64×64, flatten, slice) — not the four handcrafted feature groups this project has
   already settled on (histogram, FFT band energy, LBP texture, Laplacian sharpness).
3. It runs a **single `KSDrift`** producing one scalar `drift_score`/`status`. We need
   an overall `MMDDrift` score *plus* a per-feature-group `KSDrift` breakdown, so the
   platform can eventually tell which signal moved (contrast vs. texture vs. frequency
   vs. sharpness) rather than just "drift happened."
4. There is **no Great Expectations schema validation** step before drift detection.
5. There is **no alerting** — no threshold check, no webhook dispatch, no `alerts`
   table.
6. **Critical correctness bug**: errors inside drift detection are currently caught and
   suppressed "to keep the pipeline alive." This must be fixed — an unhandled internal
   error must surface as a visible failure state (logged, and reflected in the stored
   status), never silently swallowed into what looks like a normal "no drift" result.
   A silent failure here is precisely the failure mode this platform exists to prevent.

## Non-negotiable constraints

1. Only CheXpert (baseline/source) vs. MIMIC-CXR (target/inference). No other dataset.
2. Drift features: intensity/contrast histogram, FFT band energy ratios, LBP texture
   histogram, Laplacian-variance sharpness. No deep-network/CNN embeddings, ever.
3. Drift computation uses Alibi Detect's built-in `MMDDrift` (overall) and `KSDrift`
   (per feature group) — not a from-scratch statistical reimplementation.
4. **Never guess a library's API signature from memory.** `alibi-detect` and
   `great_expectations` (already in `backend/requirements.txt` — check, don't assume,
   whether `great_expectations` needs to be added) have both had breaking API changes
   across versions. Check the installed version (`pip show <package>`) and confirm the
   real constructor/usage pattern before writing detector or validation code.
5. **Preserve the existing async-first design.** Feature extraction, Great
   Expectations validation, and Alibi Detect scoring are all CPU-bound and
   synchronous — run them via a thread-pool executor, mirroring exactly how
   `TelemetryService` already offloads blocking MLflow calls with
   `run_in_executor`. Do not introduce a blocking call directly in an `async def`
   request path.
6. **Out of scope — do not modify**: the mock inference block, the feedback endpoint
   (`submit_physician_feedback` / `feedback_crud.py`), `anonymizer.py`, or the
   `Hospital` model.
7. Every new/modified function needs type hints and a docstring.

## Step 0 — Reconnaissance (mandatory, before writing implementation code)

1. Read `CLAUDE.md` in full.
2. Read the actual current contents of `backend/app/core/drift_detector.py`,
   `orchestrator.py`, `models/platform_models.py`, `api/endpoints.py`, and
   `core/database.py` — the summaries above are a map, not a substitute for the real
   source.
3. Check `backend/requirements.txt` for `scikit-image` (needed for LBP),
   `great_expectations`, and `scipy`/`opencv-python` (FFT, Laplacian). Add whatever's
   missing; don't assume presence or absence.
4. Determine how DB tables are currently created (`Base.metadata.create_all()` on
   startup? Alembic? Only `deployment/postgres/init.sql`?) and follow that same
   mechanism for new tables/columns — don't introduce Alembic if the project isn't
   using it, and vice versa.
5. Search the repo for every reference to `DriftLog`, `drift_score`, and `drift_status`
   (schemas, telemetry params, response payloads) before changing the model — anything
   reading those fields needs to keep working or be updated consistently.
6. Locate where local CheXpert and MIMIC-CXR image data lives on disk for baseline
   calibration and test purposes (this is separate from the runtime PACS-upload flow
   the API serves) — it is not part of the described repo layout, so find it or ask
   rather than assuming a path.
7. Report findings before proceeding; flag anything here that turns out to be wrong.

## Step 1 — Feature extraction module

New file: `backend/app/core/drift_features.py` (flat file, matching the existing
`core/` convention — no new subpackages).

```python
def load_and_preprocess(image_bytes: bytes, target_size: tuple[int, int] = (320, 320)) -> np.ndarray:
    """Decode image bytes, convert to grayscale, resize, return float32 array in [0, 1].
    Raises a specific exception (not bare except) on corrupt/unreadable input."""

def extract_histogram_features(image: np.ndarray, bins: int = 64) -> np.ndarray: ...
def extract_fft_band_features(image: np.ndarray, n_bands: int = 8) -> np.ndarray: ...
def extract_lbp_features(image: np.ndarray, radius: int = 2, n_points: int = 16) -> np.ndarray: ...
def extract_sharpness_features(image: np.ndarray, kernel_sizes: tuple[int, ...] = (3, 5, 7)) -> np.ndarray: ...

def extract_all_features(image: np.ndarray) -> dict[str, np.ndarray]:
    """{'histogram': ..., 'fft': ..., 'lbp': ..., 'sharpness': ..., 'concat': <all four concatenated>}"""
```

Each feature function needs a unit test against a synthetic image with a known
property (flat image → zero Laplacian variance, etc.).

## Step 2 — Baseline calibration script

New file: `scripts/build_drift_baseline.py`, styled like the existing
`scripts/freeze_and_register.py` (standalone, run outside the API).

- Build a stratified CheXpert sample (~2,000 images, balanced by view/label using
  CheXpert's metadata CSV — located in Step 0).
- Run each through `load_and_preprocess` + `extract_all_features`.
- Persist the reference feature arrays as a baseline artifact. Default recommendation:
  a local artifact file mounted into the `backend_api` container via a Docker volume
  (simplest, and the baseline changes rarely) — only push it to MinIO instead if you
  find a reason the local-volume approach won't work in this deployment.
- Must be runnable standalone and print a summary (sample size, per-view/label counts)
  on completion.

## Step 3 — Refactor `MedicalDriftDetector`

File: `backend/app/core/drift_detector.py`

- Replace the random-tensor baseline in `__init__` with the artifact produced by Step 2.
- Replace the raw-pixel-flatten path with `extract_all_features` from
  `drift_features.py`.
- Replace the single `KSDrift` with:
  - One `MMDDrift` on the concatenated feature vector → overall stat + p-value.
  - Four `KSDrift` detectors, one per feature group → per-signal p-values.
- Fix the swallowed-exception bug: on internal failure, log the error with context and
  propagate a distinct, visible failure status — never fall back to a default result
  that looks like "no drift."
- Confirm real `MMDDrift`/`KSDrift` constructor arguments against the installed
  `alibi-detect` version (per constraint 4) rather than assuming a signature.
- Wrap the now-heavier computation in a thread-pool executor call (constraint 5).

## Step 4 — Great Expectations schema validation

New file: `backend/app/core/schema_validator.py`.

Validates: file is readable/not corrupt, extension matches an allow-list, dimensions
fall within a configured range. Call this in `endpoints.py`'s
`ingest_medical_image`, before the MinIO upload — reject invalid files with a clear
4xx response before any storage or DB write happens, rather than persisting a
request that never should have been ingested.

## Step 5 — Extend the Postgres schema

File: `backend/app/models/platform_models.py`

- **Keep** `DriftLog.drift_score` / `.status` (something may already read them — Step
  0.5 tells you what). **Add** `overall_mmd_stat`, `overall_p_value` (floats), and
  `signal_breakdown` (JSONB: `{histogram: p, fft: p, lbp: p, sharpness: p}`). Derive
  the old `drift_score`/`status` fields from the new overall MMD result so existing
  readers keep working unchanged.
- **Add** a new `AlertLog` model, matching `DriftLog`'s PK style (integer, not UUID):
  `id, drift_log_id (FK), threshold_used (float), severity (str), channel (str),
  sent_at (timestamp)`.
- Apply via whatever schema-creation mechanism Step 0.4 found — don't introduce a new
  one.

## Step 6 — Alerting

New file: `backend/app/core/alerting.py`. Reads a webhook URL / threshold from
environment variables, following the same pattern `TelemetryService` already uses for
`MLFLOW_S3_ENDPOINT_URL` (check that pattern, don't invent a new config system). On
drift breach: insert an `AlertLog` row, then dispatch to Slack webhook and/or email.
Dispatch failure must be logged, not silently swallowed.

## Step 7 — Wire it into the orchestrator

File: `backend/app/core/orchestrator.py`, `execute_pipeline`:

1. (Validation now happens earlier, in the endpoint — see Step 4.)
2. Call the refactored `MedicalDriftDetector` → get overall + per-signal result.
3. Mock inference — **unchanged**.
4. Persist the extended `DriftLog`.
5. If threshold breached, call `alerting.py` and persist `AlertLog`.
6. MLflow telemetry — extend the logged metrics to include the per-signal breakdown
   alongside what's already logged.
7. Return dict — extend it with the breakdown so callers of `/inference/ingest` can
   see it, after checking what `InferenceRequestResponse` currently expects.

## Step 8 — Tests

- Unit tests per feature extractor (synthetic images, known properties).
- A sanity test: held-out CheXpert vs. CheXpert baseline (expect low/no drift) and
  CheXpert baseline vs. MIMIC-CXR (expect the engine to report a result — don't
  hardcode an expected pass/fail; report the actual numbers and sanity-check they're
  directional).
- An integration test hitting `/v1/clinical/inference/ingest` end-to-end with a real
  sample image, confirming a `DriftLog` (and `AlertLog` when applicable) is persisted.
- An explicit test that a forced internal error in drift detection produces a visible
  failure state, not a silently "normal" result — this directly tests the Step 3 bug
  fix.
- Run the full suite and show the output before declaring anything done.

## Config defaults (env vars, alongside existing `.env` entries)

| Setting | Default | Note |
|---|---|---|
| Canonical resolution | 320×320 | confirm against Step 0 findings |
| Baseline sample size | ~2,000 | stratified across view/label |
| Histogram bins | 64 | |
| FFT bands | 8 | |
| LBP radius / points | 2 / 16 | |
| Sharpness kernel sizes | (3, 5, 7) | |
| Drift p-value threshold | 0.05 | tune after first real calibration run |
| Alert webhook URL | (from `.env`) | Slack incoming webhook or SMTP config |

## Rules of engagement

- If something depends on data you haven't actually verified (paths, formats, whether
  a field is read elsewhere, how migrations work in this repo), stop and ask.
- No hardcoded absolute paths or credentials.
- Don't claim a step is complete without having run it — show test output, show the
  calibration script's summary output, show a real request/response from the ingest
  endpoint.
- Update `README.md` with how to run the baseline calibration script and any new env
  vars required.