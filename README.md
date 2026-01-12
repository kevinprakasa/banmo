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

## Features

- Scrapes broker summary data from Stockbit
- Analyzes accumulation/distribution patterns
- Calculates average accumulation price
- Identifies net broker action value
# banmo
