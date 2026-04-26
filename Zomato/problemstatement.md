# Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)

Build an AI-powered restaurant recommendation application inspired by Zomato.  
The system should combine structured restaurant data with a Large Language Model (LLM) to provide personalized, easy-to-understand recommendations.

## Objective

Design and implement an application that can:

- Collect user preferences (location, budget, cuisine, rating, etc.)
- Use a real-world restaurant dataset
- Filter and rank relevant restaurants
- Generate natural-language recommendations using an LLM
- Present results clearly for end users

## Functional Workflow

### 1) Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  [https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract key fields such as:
  - Restaurant name
  - Location
  - Cuisine
  - Cost
  - Rating
  - Any other relevant attributes

### 2) User Input

Collect user preferences, including:

- Location (for example, Delhi or Bangalore)
- Budget range (low, medium, high)
- Preferred cuisine (for example, Italian, Chinese)
- Minimum acceptable rating
- Optional constraints (for example, family-friendly, quick service)

### 3) Integration Layer

- Filter the dataset based on user preferences
- Prepare the shortlisted entries in a structured format
- Build a prompt that provides this structured data to the LLM
- Ensure the prompt guides the LLM to compare and rank options logically

### 4) Recommendation Engine

Use the LLM to:

- Rank restaurants by relevance to user preferences
- Explain why each recommendation is a good fit
- Optionally provide a short summary of top picks

### 5) Output Display

Show the top recommendations in a user-friendly format.  
Each recommendation should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation
