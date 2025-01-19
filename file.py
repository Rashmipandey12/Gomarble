from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import openai

# Initialize Flask App
app = Flask(__name__)

# OpenAI API Key (replace with your key)
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

# Function to extract reviews dynamically using Playwright
def extract_reviews(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Use OpenAI to dynamically identify review selectors
        page_content = page.content()
        llm_response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Extract CSS selectors for review titles, bodies, ratings, and reviewers from the following HTML: {page_content[:2000]}...",
            max_tokens=200
        )

        selectors = llm_response['choices'][0]['text'].strip()
        selectors = eval(selectors)  # Expected to return a dictionary of selectors

        reviews = []
        while True:
            for element in page.query_selector_all(selectors['review']):
                reviews.append({
                    "title": element.query_selector(selectors['title']).inner_text() if selectors['title'] else "",
                    "body": element.query_selector(selectors['body']).inner_text() if selectors['body'] else "",
                    "rating": element.query_selector(selectors['rating']).inner_text() if selectors['rating'] else "",
                    "reviewer": element.query_selector(selectors['reviewer']).inner_text() if selectors['reviewer'] else "",
                })

            # Pagination handling
            next_button = page.query_selector(selectors.get('next_button'))
            if next_button and next_button.is_enabled():
                next_button.click()
                page.wait_for_load_state("networkidle")
            else:
                break

        browser.close()
        return reviews

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    url = request.args.get("page")
    if not url:
        return jsonify({"error": "URL parameter 'page' is required."}), 400

    try:
        reviews = extract_reviews(url)
        return jsonify({
            "reviews_count": len(reviews),
            "reviews": reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
