# Stockbit Broker Summary Analyzer

A tool to scrape and analyze broker trading data from Stockbit.

## Setup

1. Create a virtual environment:

```
python -m venv venv
```

2. Activate the virtual environment:

   - On macOS/Linux:

   ```
   source venv/bin/activate
   ```

   - On Windows:

   ```
   venv\Scripts\activate
   ```

3. Install required packages:

```
pip install -r requirements.txt
```

4. Install Chrome WebDriver:
   - Make sure you have Chrome browser installed
   - Download the appropriate ChromeDriver version from: https://chromedriver.chromium.org/downloads
   - Add the ChromeDriver to your PATH or specify its location in the script

## Usage

1. Update your Stockbit credentials in the script or use environment variables
2. Run the script:

```
python runner.py
```

### Manual Login (Bypass reCAPTCHA)

If you're encountering reCAPTCHA issues with automated login, you can use manual login mode:

```
python -m stockbit_analyzer.cli --manual-login
```

This will:
- Open the browser in visible mode (non-headless)
- Navigate to the Stockbit login page
- Wait for you to manually log in and solve the reCAPTCHA
- Automatically detect when login is complete
- Continue with the rest of the script

### Extract Broker Summary Data

To extract broker summary data for a specific stock:

```
python -m stockbit_analyzer.cli --manual-login --stock BUMI --extract
```

To extract data for the last X days (e.g., last 7 days):

```
python -m stockbit_analyzer.cli --manual-login --stock BUMI --extract --days 7
```

The `--days` parameter sets how many days back to look (default: 1, which is today only).

## Features

- Scrapes broker summary data from Stockbit
- Analyzes accumulation/distribution patterns
- Calculates average accumulation price
- Identifies net broker action value
# banmo
