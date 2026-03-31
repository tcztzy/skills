#!/usr/bin/env python3
"""
Generate a runnable ggplot2 publication-visualization skeleton from a tabular inventory.

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
    return("visualization")
  }
  text
}

ensure_figures_dir <- function(figures_dir, clean) {
  cwd <- normalizePath(getwd(), mustWork = TRUE)
  if (!grepl("^(/|[A-Za-z]:[/\\\\])", figures_dir)) {
    figures_dir <- normalizePath(file.path(cwd, figures_dir), winslash = "/", mustWork = FALSE)
  } else {
    figures_dir <- normalizePath(figures_dir, winslash = "/", mustWork = FALSE)
  }

  if (clean) {
    parent_dir <- dirname(figures_dir)
    if (!(identical(figures_dir, cwd) || startsWith(figures_dir, paste0(cwd, "/")))) {
      stop(sprintf("Refusing to clean figures outside CWD: %s", figures_dir))
    }
    if (dir.exists(figures_dir)) {
      unlink(figures_dir, recursive = TRUE)
    }
    if (!dir.exists(parent_dir)) {
      dir.create(parent_dir, recursive = TRUE, showWarnings = FALSE)
    }
  }

  dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
  figures_dir
}

parse_args <- function() {
  figures_dir <- "__FIGURES_DIR__"
  manifest <- NULL
  max_plots <- default_max_plots
  clean <- FALSE
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
    } else if (arg == "--clean") {
      clean <- TRUE
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    index <- index + 1
  }

  list(
    figures_dir = figures_dir,
    manifest = manifest,
    max_plots = max_plots,
    clean = clean
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

build_plot <- function(entry, data_frame) {
  x_column <- entry$likely_x
  y_column <- entry$likely_y
  group_column <- entry$likely_group
  facet_column <- entry$likely_facet
  families <- entry$recommended_chart_families
  rel_path <- if (!is.null(entry$rel_path)) entry$rel_path else basename(resolve_path(entry))
  title <- tools::file_path_sans_ext(basename(rel_path))

  if (!is.null(x_column) && !is.null(y_column) && "evolution" %in% families) {
    mapping <- aes(x = .data[[x_column]], y = .data[[y_column]])
    if (!is.null(group_column)) {
      mapping <- aes(x = .data[[x_column]], y = .data[[y_column]], color = .data[[group_column]])
    }
    plot <- ggplot(data_frame, mapping) + geom_line(linewidth = 0.5) + geom_point(size = 1.2)
    chart_family <- "evolution"
  } else if (!is.null(x_column) && !is.null(y_column) && x_column %in% entry$categorical_columns) {
    mapping <- aes(x = .data[[x_column]], y = .data[[y_column]])
    if (!is.null(group_column)) {
      mapping <- aes(x = .data[[x_column]], y = .data[[y_column]], fill = .data[[group_column]])
    }
    plot <- ggplot(data_frame, mapping) + geom_col(position = "dodge")
    chart_family <- "comparison/ranking"
  } else if (!is.null(x_column) && !is.null(y_column)) {
    mapping <- aes(x = .data[[x_column]], y = .data[[y_column]])
    if (!is.null(group_column)) {
      mapping <- aes(x = .data[[x_column]], y = .data[[y_column]], color = .data[[group_column]])
    }
    plot <- ggplot(data_frame, mapping) + geom_point(alpha = 0.75, size = 1.4)
    chart_family <- "correlation"
  } else if (!is.null(y_column)) {
    plot <- ggplot(data_frame, aes(x = .data[[y_column]])) + geom_histogram(bins = 30, fill = "#4c78a8", color = "white")
    chart_family <- "distribution"
  } else if (length(entry$categorical_columns) > 0) {
    category <- entry$categorical_columns[[1]]
    plot <- ggplot(data_frame, aes(x = .data[[category]])) + geom_bar(fill = "#4c78a8")
    chart_family <- "comparison/ranking"
  } else {
    stop(sprintf("No plottable columns found for %s", rel_path))
  }

  plot <- plot +
    labs(
      title = gsub("[-_]+", " ", title),
      caption = paste("Source:", rel_path)
    ) +
    theme_bw(base_size = 8) +
    theme(
      legend.position = "top",
      plot.title = element_text(face = "bold")
    )

  if (!is.null(facet_column)) {
    plot <- plot + facet_wrap(stats::as.formula(paste("~", facet_column)))
  }

  list(plot = plot, chart_family = chart_family, title = gsub("[-_]+", " ", title))
}

save_plot_bundle <- function(plot, stem, figures_dir) {
  width_in <- 90 / 25.4
  height_in <- 65 / 25.4
  pdf_name <- sprintf("%s.pdf", stem)
  png_name <- sprintf("%s.png", stem)

  ggsave(filename = file.path(figures_dir, pdf_name), plot = plot, width = width_in, height = height_in, units = "in")
  ggsave(filename = file.path(figures_dir, png_name), plot = plot, width = width_in, height = height_in, units = "in", dpi = 300)

  list(filename = pdf_name, preview_filename = png_name)
}

main <- function() {
  options <- parse_args()
  figures_dir <- ensure_figures_dir(options$figures_dir, options$clean)

  entries <- inventory$entries
  if (is.null(entries) || length(entries) == 0) {
    stop("Inventory contains no entries")
  }

  total <- min(length(entries), max(0, options$max_plots))
  items <- list()

  for (index in seq_len(total)) {
    entry <- entries[[index]]
    built <- build_plot(entry, read_entry(entry))
    stem <- sprintf("%02d-%s", index, sanitize_stem(built$title))
    saved <- save_plot_bundle(built$plot, stem, figures_dir)
    items[[index]] <- list(
      id = sprintf("viz-%02d", index),
      filename = saved$filename,
      preview_filename = saved$preview_filename,
      title = built$title,
      plot_system = "ggplot2",
      chart_family = built$chart_family,
      task_mode = "static",
      interaction_level = "static",
      script_path = "auto_data_to_viz.R",
      data_sources = list(resolve_path(entry)),
      caption_suggestion = sprintf("Quicklook %s view of %s. Replace with a claim-driven caption before publication.", built$chart_family, built$title)
    )
  }

  if (!is.null(options$manifest)) {
    manifest <- list(
      generated_at = inventory$generated_at,
      figures_dir = figures_dir,
      apps_dir = NULL,
      visualizations = items
    )
    write_json(manifest, path = options$manifest, auto_unbox = TRUE, pretty = TRUE)
    message(sprintf("[OK] Wrote manifest: %s", options$manifest))
  }

  message(sprintf("[OK] Wrote figures to: %s", figures_dir))
}

main()
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate auto_data_to_viz.R ggplot2 skeleton.")
    ap.add_argument("--inventory", required=True, help="Input inventory JSON from tabular_inventory.py.")
    ap.add_argument("--out", required=True, help="Output path for auto_data_to_viz.R.")
    ap.add_argument("--figures-dir", default="figures", help="Figures directory (default: figures).")
    ap.add_argument("--max-plots", type=int, default=12, help="Max quicklook plots the script will attempt.")
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
                "numeric_columns": entry.get("numeric_columns", []),
                "categorical_columns": entry.get("categorical_columns", []),
                "likely_x": entry.get("likely_x"),
                "likely_y": entry.get("likely_y"),
                "likely_group": entry.get("likely_group"),
                "likely_facet": entry.get("likely_facet"),
                "recommended_chart_families": entry.get("recommended_chart_families", []),
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
