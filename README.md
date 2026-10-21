# SmartSpend — Your Money, Made Clear

A personal money organiser that imports bank statements and payslips, lets users review the imported records, and produces a report with income, expenses, spending categories and practical budgeting suggestions.

## Supported inputs
- CSV and Excel bank statement exports (recommended).
- Some text-based PDF bank statements; PDF layouts vary.
- Text-based PDF payslips for common net/gross pay labels.
- Manual entry of monthly take-home pay.
- Scanned/image-only PDFs may not work. Export CSV/Excel or enter pay manually.

A payslip alone cannot show spending. Upload a bank statement for expense analysis. Review every transaction's income/expense type before trusting the report.

## Run on Windows
Extract ZIP, open folder in VS Code, select Terminal → New Terminal, then run separately:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`. Open `http://localhost:8501`.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Recommended first test
1. Open Upload & build report.
2. Click Load demonstration data.
3. Review transaction types.
4. Explore Your report and Spending breakdown.
5. Then test a bank-exported CSV after removing unnecessary personal identifiers.

## Privacy
Financial records are sensitive. Do not upload credentials, PINs, full card numbers or unnecessary identity details. Local processing does not automatically make a public deployment private; review hosting security, access and retention before inviting real users.

## Limitations
This is a budgeting-awareness project, not a production banking service or professional financial advice. Category detection and recommendations are rule-based and can be wrong. Verify the report against original records.
