# Viz Manifest Schema

Use `viz_manifest.json` to track provenance, chart-family choice, route, and output artifacts for both static and interactive workflows.

The generators in this skill do not write `viz_manifest.json` by themselves; the generated plotting/app script writes it when executed with `--manifest`.

## Suggested JSON format

```json
{
  "generated_at": "2026-03-17T12:34:56",
  "figures_dir": "figures",
  "apps_dir": null,
  "visualizations": [
    {
      "id": "viz-01",
      "filename": "01-model-accuracy.pdf",
      "preview_filename": "01-model-accuracy.png",
      "title": "Model accuracy by dataset",
      "plot_system": "seaborn",
      "chart_family": "comparison/ranking",
      "task_mode": "static",
      "interaction_level": "static",
      "script_path": "auto_data_viz.py",
      "data_sources": [
        "results/metrics.csv"
      ],
      "claim": "Model A leads on dataset X while Model B is more stable overall.",
      "caption_suggestion": "Grouped comparison of model accuracy by dataset. Error bars, if shown, indicate variability across seeds.",
      "notes": "Replace the quicklook caption before publication.",
      "checks": {
        "vector_export": true,
        "grayscale_ok": true,
        "red_green_safe": true,
        "legend_non_overlapping": true
      }
    }
  ]
}
```

## Guardrails

- `visualizations` should cover every exported figure or app in the bundle.
- `task_mode` should be `static`, `explore`, `geo`, `app`, or another explicit route.
- `interaction_level` should describe the artifact honestly: `static`, `interactive`, or `server-required`.
- `data_sources` must reference real files.
- Use `notes` for caveats such as tile-backed maps needing network access at view time.
