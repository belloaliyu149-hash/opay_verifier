import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ==========================================
# 1. SYSTEM ENGINE: Environment Initialization
# ==========================================
load_dotenv()

PAYSTACK_KEY = os.getenv("PAYSTACK_SECRET_KEY")
FLUTTERWAVE_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
STATEMENT_PATH = os.getenv("STATEMENT_FILE", "BELLO ALIYU_7038650016_20260908075339.xlsx")

# ==========================================
# 2. DATA ENGINE: Statement Loader
# ==========================================
class StatementEngine:
    """Handles parsing, filtering, and querying local statement files."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = self._load_statement()

    def _load_statement(self):
        try:
            # Load raw ledger ignoring header metadata
            df = pd.read_excel(self.filepath, sheet_name='Wallet Account Transactions').iloc[6:]
            df.columns = ['Trans_Date', 'Value_Date', 'Description', 'Debit', 'Credit', 'Balance_After', 'Channel', 'Ref']
            return df
        except Exception as e:
            print(f"[DataEngine Error] Failed to load statement: {e}")
            return None

    def search_reference(self, reference_str):
        """Filters transactions matching a specific reference or keyword."""
        if self.df is None:
            return pd.DataFrame()
        matches = self.df[
            self.df['Ref'].astype(str).str.contains(reference_str, case=False, na=False) |
            self.df['Description'].astype(str).str.contains(reference_str, case=False, na=False)
        ]
        return matches[['Trans_Date', 'Description', 'Credit', 'Debit', 'Ref']]

# ==========================================
# 3. GATEWAY ENGINE: Paystack API Integrator
# ==========================================
class PaystackGateway:
    """Handles API interactions with Paystack endpoints."""
    
    def __init__(self, secret_key):
        self.headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }

    def verify_transaction(self, tx_ref):
        """Queries Paystack for gateway transaction status."""
        url = f"https://api.paystack.co/transaction/verify/{tx_ref}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def resolve_account(self, account_num, bank_code):
        """Resolves recipient bank account number to verify account owner."""
        url = f"https://api.paystack.co/bank/resolve?account_number={account_num}&bank_code={bank_code}"
        response = requests.get(url, headers=self.headers)
        return response.json()

# ==========================================
# 4. WORKFLOW CONTROLLER: System Orchestrator
# ==========================================
def main():
    print("===========================================")
    print(" OPay Statement & Gateway Query System ")
    print("===========================================\n")

    # Instantiate Engines
    data_engine = StatementEngine(STATEMENT_PATH)
    paystack_engine = PaystackGateway(PAYSTACK_KEY)

    # Interactive Loop
    while True:
        print("\nOptions:")
        print("1. Search Local OPay Statement (By Ref or Keyword)")
        print("2. Verify Paystack Gateway Reference")
        print("3. Resolve NUBAN Bank Account Name")
        print("4. Exit")

        choice = input("\nSelect Option (1-4): ").strip()

        if choice == "1":
            query = input("Enter Reference or Search Term: ").strip()
            results = data_engine.search_reference(query)
            if not results.empty:
                print("\n--- Statement Results ---")
                print(results.to_string(index=False))
            else:
                print("\nNo matching records found in statement.")

        elif choice == "2":
            ref = input("Enter Paystack Reference: ").strip()
            res = paystack_engine.verify_transaction(ref)
            print("\n--- Gateway Response ---")
            print(res)

        elif choice == "3":
            acc = input("Enter 10-digit Account Number: ").strip()
            code = input("Enter Bank Code (e.g., 057 for Zenith, 011 for First Bank): ").strip()
            res = paystack_engine.resolve_account(acc, code)
            print("\n--- Account Resolution Response ---")
            print(res)

        elif choice == "4":
            print("Shutting down query engine.")
            break

if __name__ == "__main__":
    main()

