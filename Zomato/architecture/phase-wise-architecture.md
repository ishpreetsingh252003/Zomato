# Phase-wise Architecture

### Phase 1: Data Foundation

**Goal:** Build a reliable restaurant data layer.

- **Input:** Raw Zomato dataset from Hugging Face
- **Processing:**
  - Load data into the system
  - Clean missing or inconsistent values
  - Normalize fields (cost ranges, cuisine labels, location names)
  - Define a standard schema
- **Output:** Cleaned and queryable restaurant dataset
- **Core Components:** Data loader, preprocessing pipeline, schema validator
- **Implementation:** [`phase_1_data_foundation/`](phase_1_data_foundation/) — primary entry: **basic web UI** (`python web_ui.py` from that folder, then open `http://127.0.0.1:5000/`, submit the form to download the Hugging Face dataset and run Phase 1). CLI: `python __main__.py` (see `requirements.txt`; `--source huggingface` or `--source json --path sample_input.json`).

### Phase 2: Preference Capture Layer

**Goal:** Capture and validate user intent.

- **Input:** User selections and optional free-text preferences
- **Processing:**
  - Collect location, budget, cuisine, and minimum rating
  - Parse optional preferences (for example, family-friendly)
  - Validate and normalize user input
- **Output:** Structured user preference object
- **Core Components:** Input UI/API, validation module, preference normalizer
- **Implementation:** [`phase_2_preference_capture/`](phase_2_preference_capture/) — primary entry: **basic web UI** (`python web_ui.py`, then open `http://127.0.0.1:5001/`). CLI: `python __main__.py --location "Bangalore" --budget medium --cuisines "Italian, Chinese" --min-rating 4.0`.

### Phase 3: Candidate Retrieval and Filtering

**Goal:** Narrow down restaurants to relevant candidates.

- **Input:** Structured user preferences + cleaned dataset
- **Processing:**
  - Apply hard filters (location, budget range, minimum rating)
  - Apply soft matching (cuisine similarity, optional preferences)
  - Select top-N candidate restaurants for LLM reasoning
- **Output:** Shortlisted candidate set
- **Core Components:** Filter engine, ranking pre-processor, candidate selector
- **Implementation:** [`phase_3_candidate_retrieval/`](phase_3_candidate_retrieval/) — primary entry: **basic web UI** (`python web_ui.py`, then open `http://127.0.0.1:5002/`). CLI: `python __main__.py --dataset-path sample_restaurants.jsonl --location "Bangalore" --budget medium --cuisines "Italian,Chinese" --min-rating 4 --top-n 10`.

### Phase 4: LLM Reasoning and Recommendation

**Goal:** Generate personalized and explainable recommendations.

- **Input:** Shortlisted restaurant set + user preferences
- **Processing:**
  - Construct prompt with structured restaurant context
  - Ask LLM to rank and explain top choices
  - Enforce output format for consistency
- **Output:** Ranked recommendations with natural-language explanations
- **Core Components:** Prompt builder, LLM service, response formatter
- **Implementation:** [`phase_4_llm_recommendation/`](phase_4_llm_recommendation/) — LLM provider: **Groq**. Set `GROQ_API_KEY`, then run web UI (`python web_ui.py`, open `http://127.0.0.1:5003/`) or CLI: `python __main__.py --candidates-path sample_candidates.json --preferences-path sample_preferences.json --top-n 5 --model llama-3.3-70b-versatile`.

### Phase 5: Response Delivery and UX

**Goal:** Present recommendations in a clear and actionable way.

- **Input:** Ranked recommendations from LLM
- **Processing:**
  - Display cards/list view with key details
  - Show concise "why recommended" explanation
  - Support refresh/re-query with changed preferences
- **Output:** User-facing recommendation screen/API response
- **Core Components:** Frontend display layer, API response handler, UX formatter

### Phase 6: Monitoring and Continuous Improvement

**Goal:** Improve recommendation quality over time.

- **Input:** User interactions and feedback signals
- **Processing:**
  - Track clicks, selections, skips, and feedback
  - Measure relevance and response quality
  - Tune filters, prompts, and ranking strategy
- **Output:** Improved recommendation logic and prompt quality
- **Core Components:** Analytics logger, feedback loop, evaluation dashboard

## Suggested End-to-End Flow

`Dataset -> Preprocessing -> User Preferences -> Candidate Filtering -> LLM Ranking -> Recommendation UI -> Feedback Loop`
