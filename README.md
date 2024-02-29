# CryptoTokenHunter ReadMe

Welcome to CryptoTokenHunter, a blockchain analysis tool designed to uncover emerging crypto tokens by monitoring transactions from a curated list of addresses. To get started, add a list of wallet address that you'd like to monitor to the wallet.txt file and then run the script to quickly discover which tokens these addresses transfered (bought, sold, swapped, etc) in the last 8000 blocks (roughly 24 hours).

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)

This script also requires several Python libraries, including `requests`, `aiohttp`, `pandas`, and `python-dotenv`. Additionally, you'll need an API key from Alchemy to fetch blockchain data.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/CryptoTokenHunter.git
   cd CryptoTokenHunter
   ```

2. **Set Up a Virtual Environment (Optional but Recommended):**

   - Create a virtual environment:

     ```bash
     python -m venv venv
     ```

   - Activate the virtual environment:

     - On Windows:

       ```bash
       .\venv\Scripts\activate
       ```

     - On Unix or MacOS:

       ```bash
       source venv/bin/activate
       ```

3. **Install Required Libraries:**

   ```bash
   pip install -r requirements.txt
   ```

4. **API Key Configuration:**

   - Sign up for an Alchemy account and obtain an API key.
   - Create a `.env` file in the root directory of the project.
   - Add the following line to your `.env` file, replacing `YOUR_API_KEY` with your actual Alchemy API key:

     ```plaintext
     ALCHEMY_API_KEY=YOUR_API_KEY
     ```

## Usage

To run CryptoTokenHunter, navigate to the script's directory in your terminal and execute:

```bash
python cryptotokenhunter.py
```

Ensure you have configured the list of wallet addresses you wish to monitor by editing the `wallet.txt` file, adding one address per line.

If you'd like to exclude any tokens from analysis, place them in the `tokens.txt` file, one per line. For example, you can exclude stablecoins.

## Understanding the Output

- The script will generate several output files, including:
  - `found-tokens_DATE.txt`: Lists the tokens found during the script's execution.
  - `prime_token_data_DATE.json`: Contains detailed token data fetched from the security API.
  - `extracted_token_data_DATE.csv`: A CSV file summarizing the tokens' liquidity and other relevant metrics.

The script will replace `DATE` with the actual date of execution, formatted as `YYYY-MM-DD`.

## License

You may use CryptoTokenHunter for non-commercial purposes as long as you cite me. If you want to use it for commercial purposes, get in touch.

## Support

If you encounter any problems or have questions, please open an issue on the GitHub repository.

Thank you for using CryptoTokenHunter!
