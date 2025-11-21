# AI SEO Meta Tag For Web Sites

Automated SEO meta tag generator for websites using AI. Crawl your website, discover all internal links, and generate optimized meta tags including title, description, keywords, and canonical URLs. The project can optionally use Ollama AI models to produce advanced SEO suggestions.

**Project URL:** [https://github.com/jamieduk/SEO-AI](https://github.com/jamieduk/SEO-AI)

---

## Features

- Full website crawling with automatic internal link discovery.
- Deduplication and relative URL normalization to ensure no pages are missed.
- Extracts existing meta tags and visible page text.
- Generates suggested meta tags:
  - **Title**
  - **Description** (max 160 characters)
  - **Keywords**
  - **Canonical URL**
- Optional AI-generated meta tags using Ollama.
- Produces **JSON** and **HTML** SEO reports for easy review.
- Fully configurable for max pages, user agent, and request delay.

---

## Requirements

- Python 3.x
- `requests`
- `beautifulsoup4`
- Ollama installed (for AI meta generation)
- A downloaded Ollama model (e.g., `crewai-llama2-uncensored:latest`)

---

## Setup

```bash
sudo chmod +x *.sh
./setup.sh
```

---

## Usage

Run the crawler against a website:

```bash
./start.sh website.com
```

- The crawler will discover all internal pages.
- It will generate a JSON report and an HTML report in the `output/` folder.
- Edit `seo_crawler.py` (or `run.py`) to choose the Ollama model you wish to use for AI-assisted meta generation.

---

## Configuration

Inside `seo_crawler.py`:

```python
OLLAMA_MODEL='crewai-llama2-uncensored:latest'  # Choose your preferred Ollama model
MAX_PAGES=500                                   # Maximum pages to crawl
REQUEST_DELAY=0.2                               # Delay between requests (seconds)
OUTPUT_DIR='output'                             # Folder to store reports
USER_AGENT='seo-crawler-bot/1.0 (+https://example.com)'
```

---

## Notes

- Make sure Ollama is installed and the model is downloaded before running AI meta generation.
- The crawler respects internal links only; external domains are ignored.
- JSON and HTML reports include found meta, missing fields, and AI/heuristic suggestions.
- You can limit the crawl with `--max`:

```bash
./start.sh website.com --max 100
```

---

## License

This project is open-source and available under the MIT License.
