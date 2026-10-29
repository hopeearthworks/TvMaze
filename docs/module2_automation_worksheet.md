# Module 2: Automation Planning Worksheet: High-Priority Customer Enquiries

| Item | Detail |
|---|---|
| **Problem** | Every day the team gets a CSV file of customer enquiries. Someone reads every row by hand to find the urgent ones. This is slow and inconsistent, and urgent enquiries can be missed or answered late. |
| **Inputs** | A daily CSV file (`enquiries_YYYY-MM-DD.csv`) with columns such as `enquiry_id, date_received, customer_name, customer_type, category, subject, message`. Priority rules: keywords ("urgent", "complaint", "cancel", "refund", "legal"), VIP/key-account customer types, and an age threshold (e.g. older than 48 hours). |
| **Processing** | 1. Find and open the latest CSV file. 2. Validate it (required columns, no empty or malformed rows). 3. Clean the data (trim whitespace, normalise case, parse dates). 4. Apply the rules to flag each enquiry High or Normal, recording the reason. 5. Sort by priority, then by age. 6. Log what was processed and any rows that were rejected. |
| **Outputs** | `high_priority_YYYY-MM-DD.csv` (flagged enquiries plus a "reason" column). A summary (total, high-priority count, rejected rows). A notification to the team lead (email/Teams). A log file for audit. |
| **Suitable for automation?** | **Yes.** The task happens every day, is rule-based, has a structured input and a well-defined output, and takes a lot of manual effort. The risk is low as long as a human reviews the flagged list before acting on it. |

## Discussion

**Repeatable (automate):** collecting the file, validating and cleaning it, keyword/customer-type/age flagging, sorting, writing the output, sending the summary, logging.

**Needs human judgement:** deciding how to respond (reply, escalate, refund), reading tone or context (sarcasm, a routine "cancel"), edge cases the rules don't cover, adjusting the rules over time, and spot-checking "Normal" enquiries for missed urgent ones.

**Power Automate or Python?**
- **Power Automate** suits orchestration: noticing the file has arrived in SharePoint/OneDrive/email, triggering the run, and sending Teams/Outlook notifications. It is low-code and easy for the team to maintain.
- **Python** suits processing: flexible rules, validation, scoring, testing and logging, and it handles large or messy files better.
- **Recommendation:** a hybrid. Power Automate triggers the run and notifies the team; Python does the classification. If the rules stay simple and nobody on the team supports Python, Power Automate on its own is acceptable.

## How this plan maps onto the TVMaze project
The same input → processing → output thinking is used for the TVMaze automation built in Modules 3–8:

| Planning step | TVMaze project |
|---|---|
| Input | `config.json` (search term, minimum rating) + TVMaze API |
| Processing | `tvmaze/api_client.py`, `tvmaze/automation.py` (rating filter) |
| Output | Console table + summary (`tvmaze/ui.py`), `automation.log` |
