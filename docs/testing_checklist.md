# Testing checklist

- [ ] Run app in a clean virtual environment.
- [ ] Load fictional demo data and check report/chart rendering.
- [ ] Upload CSV with date, description, amount.
- [ ] Upload CSV with debit/credit columns.
- [ ] Test an invalid CSV and confirm helpful errors.
- [ ] Check day-first date parsing.
- [ ] Change an incorrectly classified transaction in the editor.
- [ ] Confirm unclassified transactions trigger a warning.
- [ ] Confirm salary is not double-counted from payslip and statement.
- [ ] Try a text-based PDF statement; if it fails, export CSV.
- [ ] Check every imported amount against the original statement.