# Plot Manifest Schema

Use a manifest to track provenance, plotting system, and caption guidance for each exported figure.

## Suggested JSON format

```json
{
  "generated_at": "2026-03-17T12:34:56",
  "figures_dir": "figures",
  "figures": [
    {
      "id": "fig-01",
      "filename": "fig-01-loss.pdf",
      "preview_filename": "fig-01-loss.png",
      "title": "Training loss vs epoch",
      "plot_system": "matplotlib",
      "script_path": "auto_plot_aggregator.py",
      "data_sources": [
        "runs/exp-01/train_loss.npy",
        "runs/exp-01/val_loss.npy"
      ],
      "claim": "Training stabilizes after roughly 40 epochs.",
      "caption_suggestion": "Training and validation loss over epoch. Error bands, if shown, indicate variability across seeds.",
      "notes": "Use the exact smoothing rule or state that no smoothing was applied.",
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

- `data_sources` must point to real files.
- `plot_system` should be `matplotlib`, `ggplot2`, or another explicit plotting stack.
- `claim` and `caption_suggestion` must not say more than the figure supports.
- `checks` is optional but recommended when the figure is intended for a paper submission.
