# Record Outcome — Log Paper Submission Result

Record the outcome of a paper submission for cross-paper analytics. This feeds the self-improvement system by correlating quality scores at submission time with actual results.

## Instructions

1. Parse $ARGUMENTS for outcome type. If not provided, ask the user:
   ```
   What was the outcome?
   1. Accepted
   2. Rejected
   3. Revision requested (major or minor)
   4. Withdrawn
   ```

2. Ask for additional context:
   - Which venue was it submitted to?
   - Any key reviewer feedback? (optional — a one-line summary is enough)

3. Record the outcome:
   ```bash
   python scripts/quality.py record-outcome [OUTCOME] --venue "[VENUE]" --notes "[FEEDBACK]" --project .
   ```

4. Read `.paper-quality.json` if it exists and display the correlation:
   ```
   Paper quality at submission:
     Overall: [score]/100 ([grade])
     Evidence: [score]  Writing: [score]  Structure: [score]
     Research: [score]  Provenance: [score]

   Outcome: [OUTCOME]
   ```

5. If this is a rejection, suggest which dimensions to improve:
   - Map reviewer feedback keywords to dimensions
   - Recommend specific commands to address weaknesses

$ARGUMENTS
