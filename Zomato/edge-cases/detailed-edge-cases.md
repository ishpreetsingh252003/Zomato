# Detailed Edge Cases: AI-Powered Restaurant Recommendation System

This document captures implementation and product edge cases derived from the problem statement for the Zomato-style LLM recommendation system.

## 1) Data Ingestion Edge Cases

### 1.1 Missing Critical Fields
- Restaurant rows missing name, location, cuisine, rating, or cost.
- **Risk:** Invalid or unusable recommendations.
- **Handling:** Drop rows missing mandatory fields; log counts for audit.

### 1.2 Invalid Data Types
- Ratings stored as text (`"4.2/5"`, `"NEW"`, `"N/A"`), cost stored as strings with symbols (`"Rs. 800"`).
- **Risk:** Filter and ranking failures.
- **Handling:** Build robust parsing rules and fallback defaults.

### 1.3 Duplicate Listings
- Same restaurant appears multiple times with slight name variations.
- **Risk:** Duplicate recommendations in output.
- **Handling:** Deduplicate using normalized name + location + cuisine signatures.

### 1.4 Inconsistent Categorical Values
- Cuisine variants (`"North Indian"`, `"North-Indian"`, `"NorthIndian"`), city aliases (`"Bengaluru"` vs `"Bangalore"`).
- **Risk:** Missed matches during filtering.
- **Handling:** Use normalization dictionaries and synonym mapping.

### 1.5 Outdated or Stale Records
- Closed restaurants or outdated prices/ratings remain in dataset.
- **Risk:** Low trust recommendations.
- **Handling:** Add freshness scoring and stale-data warnings.

### 1.6 Extreme Outliers
- Unrealistically high/low costs or ratings beyond allowed ranges.
- **Risk:** Distorted ranking.
- **Handling:** Validate range constraints and cap or remove outliers.

## 2) User Input Edge Cases

### 2.1 Empty or Partial Input
- User provides only location, or only cuisine, or leaves all fields blank.
- **Risk:** Ambiguous intent.
- **Handling:** Define defaults and prompt for missing critical inputs.

### 2.2 Unsupported City/Area
- User requests recommendations for a location absent in dataset.
- **Risk:** Zero-result response.
- **Handling:** Suggest nearest available locations or broader city-level search.

### 2.3 Ambiguous Budget
- Inputs such as `"affordable"`, `"not expensive"`, `"premium but reasonable"`.
- **Risk:** Incorrect budget mapping.
- **Handling:** Convert qualitative budget terms to configured numeric ranges.

### 2.4 Conflicting Preferences
- Example: very low budget + very high minimum rating + rare cuisine + specific neighborhood.
- **Risk:** No candidates found.
- **Handling:** Use relaxation strategy (progressive constraint loosening) and explain it.

### 2.5 Misspellings and Slang
- `"Itallian"`, `"chineese"`, `"veg only family place"`.
- **Risk:** Intent parser fails to detect cuisine or constraints.
- **Handling:** Fuzzy matching and typo-tolerant normalization.

### 2.6 Multi-intent Free Text
- User asks for fast delivery and romantic ambiance in one request.
- **Risk:** Some constraints ignored.
- **Handling:** Parse multi-label preferences and prioritize based on user-specified order.

## 3) Candidate Retrieval and Filtering Edge Cases

### 3.1 Zero Candidates After Hard Filters
- No restaurants satisfy all strict constraints.
- **Risk:** Empty UX.
- **Handling:** Apply staged fallback (expand radius, lower rating threshold, widen budget).

### 3.2 Too Many Candidates
- Large metros return thousands of matches.
- **Risk:** Slow response and token overflow for LLM.
- **Handling:** Pre-rank with lightweight scoring and send top-N to LLM.

### 3.3 Bias Toward Popular Cuisines
- Common cuisines dominate rare preference recommendations.
- **Risk:** Poor personalization.
- **Handling:** Reweight features to prioritize explicit user preferences.

### 3.4 Cost-Rating Tradeoff Imbalance
- Expensive highly rated places always outrank affordable good options.
- **Risk:** Budget-insensitive ranking.
- **Handling:** Add weighted scoring with explicit budget penalties.

### 3.5 Nearby Area Mismatch
- User says `"Koramangala"` but restaurants labeled under nearby locality only.
- **Risk:** Relevant options excluded.
- **Handling:** Use area hierarchy or geospatial proximity matching.

## 4) LLM Prompting and Generation Edge Cases

### 4.1 Hallucinated Restaurant Details
- LLM invents dishes, offers, or amenities not present in data.
- **Risk:** Misinformation.
- **Handling:** Restrict prompt to structured context and require citation from provided fields only.

### 4.2 Ignoring Hard Constraints
- LLM recommends restaurants below minimum rating or outside budget.
- **Risk:** Trust and correctness issues.
- **Handling:** Add rule checks post-generation; discard invalid outputs.

### 4.3 Verbose or Generic Explanations
- Explanations become repetitive (`"great ambiance"`) without user-specific linkage.
- **Risk:** Low perceived intelligence.
- **Handling:** Enforce explanation template tied to preference fields.

### 4.4 Unstable Ranking Across Runs
- Same input yields very different ranking order each call.
- **Risk:** Inconsistent user experience.
- **Handling:** Lower randomness and add deterministic pre-ranking anchor.

### 4.5 Prompt Token Overflow
- Too many candidate restaurants exceed model context window.
- **Risk:** Truncation and incomplete reasoning.
- **Handling:** Candidate compression and strict top-N budget before prompt assembly.

### 4.6 Unsafe Content in Explanations
- LLM may produce inappropriate or biased statements.
- **Risk:** Safety and brand issues.
- **Handling:** Apply moderation filters and safety policies on responses.

## 5) Output and UX Edge Cases

### 5.1 Missing Fields in Final Cards
- Recommendation includes no cost or no rating after transformation.
- **Risk:** Poor usability.
- **Handling:** Render graceful placeholders and confidence warnings.

### 5.2 Duplicate Restaurants in Top Results
- Same listing appears multiple times due to minor data variation.
- **Risk:** Perceived low quality.
- **Handling:** Final deduplication before display.

### 5.3 Recommendation-Reason Mismatch
- Ranked first for budget, but explanation talks only about cuisine.
- **Risk:** Confusing rationale.
- **Handling:** Validate explanation references at least two matched preferences.

### 5.4 No Results Scenario
- System returns empty list without guidance.
- **Risk:** Drop-off.
- **Handling:** Show actionable suggestions: relax rating, widen budget, expand location.

### 5.5 Latency Spikes
- LLM delays cause slow page responses.
- **Risk:** Poor UX.
- **Handling:** Timeout + fallback shortlist response from deterministic ranker.

## 6) Monitoring and Feedback Edge Cases

### 6.1 Feedback Sparsity
- Very few explicit ratings from users.
- **Risk:** Hard to improve model quality.
- **Handling:** Use implicit signals (clicks, saves, skips, dwell time).

### 6.2 Popularity Feedback Loop
- Frequently clicked restaurants keep getting promoted regardless of fit.
- **Risk:** Reduced diversity and novelty.
- **Handling:** Add exploration factor and diversity constraints.

### 6.3 Drift in User Preferences
- Seasonal or local trend changes make old ranking logic weak.
- **Risk:** Relevance decay.
- **Handling:** Periodic reweighting and prompt tuning based on recent data windows.

### 6.4 Silent Failures in Pipeline
- Upstream parser fails but system still serves stale recommendations.
- **Risk:** Undetected quality regression.
- **Handling:** Add health checks, alerts, and freshness indicators.

## 7) Security and Reliability Edge Cases

### 7.1 Prompt Injection in Free Text
- User attempts to override system instructions through free-text preferences.
- **Risk:** Model behavior manipulation.
- **Handling:** Escape/segment user text and preserve system prompt boundaries.

### 7.2 API Rate Limits or LLM Downtime
- Model provider throttling or temporary outage.
- **Risk:** Service interruption.
- **Handling:** Retry with backoff, queueing, and deterministic fallback recommender.

### 7.3 Data Privacy Leakage
- Logs accidentally store sensitive user context.
- **Risk:** Compliance and trust issues.
- **Handling:** Redact PII in logs and enforce retention limits.

### 7.4 Version Mismatch
- Prompt template updated but parser still expects old output format.
- **Risk:** Runtime parsing errors.
- **Handling:** Version prompts and response schema together with compatibility checks.

## 8) Recommended Test Scenarios

- **Happy path:** Valid preferences with sufficient candidates.
- **Strict filters:** Inputs that initially produce zero results.
- **Noisy input:** Misspelled cuisines and ambiguous budget text.
- **Large city load:** High candidate volume and token-limit pressure.
- **LLM failure path:** Timeout and fallback response behavior.
- **Safety path:** Prompt injection-like text and content moderation checks.

