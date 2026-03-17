#!/usr/bin/env python3
"""
Generate a runnable ggplot2 plot aggregator skeleton from a tabular inventory.

The generated R script expects ggplot2, readr, and jsonlite.
"""

import argparse
import json
from pathlib import Path


TEMPLATE = """#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
  library(jsonlite)
  library(readr)
})

default_max_plots <- __MAX_PLOTS__
inventory_json <- __INVENTORY_JSON_LITERAL__
inventory <- fromJSON(txt = inventory_json, simplifyVector = FALSE)

sanitize_stem <- function(text) {
  text <- tolower(text)
  text <- gsub("[^a-z0-9]+", "-", text)
  text <- gsub("(^-+|-+$)", "", text)
  if (!nzchar(text)) {
    return("figure")
  }
  text
}

parse_args <- function() {
  figures_dir <- "__FIGURES_DIR__"
  manifest <- NULL
  max_plots <- default_max_plots
  args <- commandArgs(trailingOnly = TRUE)
  index <- 1

  while (index <= length(args)) {
    arg <- args[[index]]
    if (arg == "--figures-dir") {
      index <- index + 1
      figures_dir <- args[[index]]
    } else if (startsWith(arg, "--figures-dir=")) {
      figures_dir <- sub("^--figures-dir=", "", arg)
    } else if (arg == "--manifest") {
      index <- index + 1
      manifest <- args[[index]]
    } else if (startsWith(arg, "--manifest=")) {
      manifest <- sub("^--manifest=", "", arg)
    } else if (arg == "--max-plots") {
      index <- index + 1
      max_plots <- as.integer(args[[index]])
    } else if (startsWith(arg, "--max-plots=")) {
      max_plots <- as.integer(sub("^--max-plots=", "", arg))
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    index <- index + 1
  }

  list(
    figures_dir = figures_dir,
    manifest = manifest,
    max_plots = max_plots
  )
}

resolve_path <- function(entry) {
  if (!is.null(entry$abs_path) && file.exists(entry$abs_path)) {
    return(entry$abs_path)
  }
  base_dir <- inventory$base_dir
  if (is.null(base_dir) || !nzchar(base_dir)) {
    base_dir <- getwd()
  }
  file.path(base_dir, entry$rel_path)
}

read_json_frame <- function(path) {
  data <- jsonlite::fromJSON(path, flatten = TRUE)
  if (is.data.frame(data)) {
    return(data)
  }
  stop(sprintf("JSON source is not tabular: %s", path))
}

read_entry <- function(entry) {
  path <- resolve_path(entry)
  format <- entry$file_format

  if (format == "csv") {
    return(readr::read_csv(path, show_col_types = FALSE))
  }
  if (format == "tsv") {
    return(readr::read_tsv(path, show_col_types = FALSE))
  }
  if (format == "json") {
    return(read_json_frame(path))
  }
  if (format == "jsonl") {
    return(jsonlite::stream_in(file(path), verbose = FALSE))
  }

  stop(sprintf("Unsupported format: %s", format))
}

detect_x_column <- function(entry) {
  columns <- vapply(entry$columns, function(column) column$name, character(1))
  preferred <- c("epoch", "step", "iteration", "iter", "time", "timestamp", "date")
  for (candidate in preferred) {
    if (candidate %in% columns) {
      return(candidate)
    }
  }
  if (length(entry$datetime_columns) > 0) {
    return(entry$datetime_columns[[1]])
  }
  if (length(entry$numeric_columns) > 0) {
    return(entry$numeric_columns[[1]])
  }
  columns[[1]]
}

detect_y_column <- function(entry, x_column) {
  candidates <- entry$numeric_columns[entry$numeric_columns != x_column]
  if (length(candidates) > 0) {
    return(candidates[[1]])
  }
  if (length(entry$numeric_columns) > 0) {
    return(entry$numeric_columns[[1]])
  }
  NULL
}

build_plot <- function(entry, data_frame) {
  x_column <- detect_x_column(entry)
  y_column <- detect_y_column(entry, x_column)
  rel_path <- if (!is.null(entry$rel_path)) entry$rel_path else basename(resolve_path(entry))
  title <- tools::file_path_sans_ext(basename(rel_path))

  if (!is.null(y_column) && x_column != y_column) {
    plot <- ggplot(data_frame, aes(x = .data[[x_column]], y = .data[[y_column]])) +
      geom_line(linewidth = 0.5, colour = "#1f77b4") +
      geom_point(size = 1.2, colour = "#1f77b4")
    y_label <- y_column
  } else if (!is.null(y_column)) {
    plot <- ggplot(data_frame, aes(x = .data[[y_column]])) +
      geom_histogram(bins = 30, fill = "#4c78a8", colour = "white")
    x_column <- y_column
    y_label <- "Count"
  } else if (length(entry$categorical_columns) > 0) {
    category <- entry$categorical_columns[[1]]
    plot <- ggplot(data_frame, aes(x = .data[[category]])) +
      geom_bar(fill = "#4c78a8") +
      coord_flip()
    x_column <- category
    y_label <- "Count"
  } else {
    stop(sprintf("No plottable columns found for %s", rel_path))
  }

  plot +
    labs(
      title = gsub("[-_]+", " ", title),
      x = x_column,
      y = y_label,
      caption = paste("Source:", rel_path)
    ) +
    theme_bw(base_size = 8, base_family = "sans") +
    theme(
      panel.grid.minor = element_blank(),
      legend.position = "top",
      plot.title = element_text(face = "bold")
    )
}

save_plot_bundle <- function(plot, stem, figures_dir) {
  width_in <- 90 / 25.4
  height_in <- 65 / 25.4
  pdf_name <- sprintf("%s.pdf", stem)
  png_name <- sprintf("%s.png", stem)

  ggsave(
    filename = file.path(figures_dir, pdf_name),
    plot = plot,
    width = width_in,
    height = height_in,
    units = "in"
  )
  ggsave(
    filename = file.path(figures_dir, png_name),
    plot = plot,
    width = width_in,
    height = height_in,
    units = "in",
    dpi = 300
  )

  list(filename = pdf_name, preview_filename = png_name)
}

main <- function() {
  options <- parse_args()
  dir.create(options$figures_dir, recursive = TRUE, showWarnings = FALSE)

  entries <- inventory$entries
  if (is.null(entries) || length(entries) == 0) {
    stop("Inventory contains no entries")
  }

  total <- min(length(entries), max(0, options$max_plots))
  manifest_figures <- list()

  for (index in seq_len(total)) {
    entry <- entries[[index]]
    rel_path <- if (!is.null(entry$rel_path)) entry$rel_path else sprintf("plot-%02d", index)
    plot <- build_plot(entry, read_entry(entry))
    stem <- sprintf("%02d-%s", index, sanitize_stem(tools::file_path_sans_ext(basename(rel_path))))
    saved <- save_plot_bundle(plot, stem, options$figures_dir)
    manifest_figures[[index]] <- list(
      id = sprintf("fig-%02d", index),
      filename = saved$filename,
      preview_filename = saved$preview_filename,
      title = gsub("[-_]+", " ", tools::file_path_sans_ext(basename(rel_path))),
      plot_system = "ggplot2",
      script_path = "auto_plot_aggregator.R",
      data_sources = list(resolve_path(entry)),
      caption_suggestion = sprintf(
        "Quicklook view of %s. Replace with a claim-driven caption before submission.",
        gsub("[-_]+", " ", tools::file_path_sans_ext(basename(rel_path)))
      )
    )
  }

  if (!is.null(options$manifest)) {
    manifest <- list(
      generated_at = inventory$generated_at,
      figures_dir = normalizePath(options$figures_dir, mustWork = FALSE),
      figures = manifest_figures
    )
    write_json(manifest, path = options$manifest, auto_unbox = TRUE, pretty = TRUE)
    message(sprintf("[OK] Wrote manifest: %s", options$manifest))
  }

  message(sprintf("[OK] Wrote figures to: %s", normalizePath(options$figures_dir, mustWork = FALSE)))
}

main()
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate auto_plot_aggregator.R ggplot2 skeleton.")
    ap.add_argument("--inventory", required=True, help="Input inventory JSON from tabular_inventory.py.")
    ap.add_argument("--out", required=True, help="Output path for auto_plot_aggregator.R.")
    ap.add_argument("--figures-dir", default="figures", help="Figures directory (default: figures).")
    ap.add_argument(
        "--max-plots",
        type=int,
        default=12,
        help="Max quicklook plots the generated script will attempt (default: 12).",
    )
    args = ap.parse_args(argv)

    inv_path = Path(args.inventory).expanduser().resolve()
    try:
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERROR] Failed to read inventory JSON: {inv_path}: {exc}")
        return 2

    entries = inv.get("entries", [])
    if not isinstance(entries, list):
        print("[ERROR] inventory.entries must be a list")
        return 2

    embedded = {
        "base_dir": inv.get("base_dir"),
        "generated_at": inv.get("generated_at"),
        "entries": [
            {
                "rel_path": entry.get("rel_path"),
                "abs_path": entry.get("abs_path"),
                "file_format": entry.get("file_format"),
                "columns": entry.get("columns", []),
                "numeric_columns": entry.get("numeric_columns", []),
                "categorical_columns": entry.get("categorical_columns", []),
                "datetime_columns": entry.get("datetime_columns", []),
            }
            for entry in entries
            if isinstance(entry, dict) and (entry.get("rel_path") or entry.get("abs_path"))
        ],
    }

    inventory_json = json.dumps(embedded, indent=2)
    inventory_json_literal = json.dumps(inventory_json)
    script = (
        TEMPLATE.replace("__FIGURES_DIR__", args.figures_dir)
        .replace("__MAX_PLOTS__", str(int(args.max_plots)))
        .replace("__INVENTORY_JSON_LITERAL__", inventory_json_literal)
    )

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(script, encoding="utf-8")
    print(f"[OK] Wrote skeleton: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
