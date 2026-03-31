# Bibliography Harvest

Use this helper when the manuscript needs new citations and you want a fast Semantic Scholar sweep before manually choosing what to cite.

## Workflow
1. Identify citation gaps with `references/citation-workflow.md`.
2. Prepare search queries.
   - Put one query per line in `queries.txt`, or pass repeated `--query` flags.
3. Run the harvester.
   ```bash
   uv run -s scripts/citation_harvest.py \
     --online --in queries.txt --out-json citations.json --out-bib citations.bib
   ```
4. Review the outputs.
   - `citations.json` records queries and raw harvested results.
   - `citations.bib` contains deduplicated BibTeX entries ready for manual vetting.
5. Merge only vetted entries into the manuscript bibliography.

## Inputs
- `--in`: text file with one query per line.
- `--query`: repeatable query string.
- `--limit`: results per query. Default `5`.
- `--online`: required for network calls.

## Outputs
- `citations.json`
- `citations.bib`

## Notes
- The helper is offline by default. `--online` is required.
- Only query strings are sent to Semantic Scholar.
- `S2_API_KEY` may be required for higher-rate access.
- See `references/bibliography-harvest-safeguards.md` before using harvested results in a paper.
