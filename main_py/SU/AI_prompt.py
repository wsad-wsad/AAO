"""
The prompt needed for SU
"""

pattern_prompt = """
# Act as a web scraping engineer. Generate a JSON schema for JsonCssExtractionStrategy to extract user-centric data from the provided HTML.

# Objective: Map relevant data to a specific naming convention using two primary categories.

# Instructions for Schema Generation:
1. Categorization & Prefixes: You must use the following two prefixes for every key in your JSON, followed by a descriptive name for the data point. The format must be [prefix]_[specific_data_name]:
- user_identity_... (Use ONLY for name, full_name, gender, age, email)
- user_metrics_... (Use for all other data: counts, scores, streaks, elo, activity levels, followers, following, posts, or any other numeric/status metric)
2. Dynamic Logic: Do not use a static template. Analyze the HTML structure to find the elements that correspond to these categories. If a category is missing data, simply omit it or use an empty array/null.
3. Robust Selectors: Prioritize id, data-attributes, aria-labels, or semantic tags (<article>, <header>) over generic, deep-nested class structures.
4. Exclusions: Exclude all global UI boilerplate (navigation, login, cookies, terms) and all the images.

## Example Pattern: 
- If you find a 'Full Name', name it user_identity_full_name.
- If you find a 'Chess Elo', name it user_metrics_chess_elo.
- If you find a 'Activity', name it user_metrics_streak.

# remember this: if the html data doesn't contain any user data, or the data quality is poor, return an empty object {}
"""

def web_info_prompt(url: str):
    return f"""
# Act as a web research assistant. Your task is to extract general information from the base domain of the provided URL: {url}.

# Instructions:
1. Normalize the URL: Ignore any specific sub-pages, paths, or user identifiers; extract information based on the root domain/website home.
2. Analysis: Identify and summarize the following:
    - Purpose: A single sentence defining what the website/company does.
    - Target Audience: The sector they serve or the general audience.
3. Format:
- Include only essential facts needed to identify the the website/company.
- Make it each 1 sentence.
- Do not include promotional jargon or filler text.
"""

summary_prompt = """
# Role: OSINT Data Compressor
# Your task is to summarize TOON scraped user data for semantic embedding.

# Instructions:
1. Output: Single continuous text string.
2. Content: Prioritize unique identifiers, specific achievements (e.g., "Chess Grandmaster"), scale (e.g., "500k followers"), and niche keywords. 
3. Logic: If the JSON lacks web context, use `get_web_info()` to determine the source site's niche first.
4. Style: Flatten the data into a high-density keyword narrative. Instead of "He is a person who...", use "High-elo chess player, 100k followers, professional athlete."
"""