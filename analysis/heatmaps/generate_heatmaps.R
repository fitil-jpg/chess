#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
  library(optparse)
  library(RColorBrewer)
})

option_list <- list(
  make_option(c("-p", "--palette"), type = "character", default = "Reds",
              help = "Color palette for heatmap (RColorBrewer palette name) [default %default]"),
  make_option(c("-t", "--theme"), type = "character", default = "minimal",
              help = "ggplot2 theme to use (e.g., minimal, classic) [default %default]"),
  make_option(c("-r", "--resolution"), type = "integer", default = 300,
              help = "Resolution (DPI) for output PNG files [default %default]"),
  make_option(c("-b", "--bins"), type = "integer", default = 8,
              help = "Number of bins for heatmap grid [default %default]")
)

parser <- OptionParser(usage = "%prog [options] <moves.csv>",
                       option_list = option_list)
args <- parse_args(parser, positional_arguments = TRUE)

if (length(args$args) < 1) {
  print_help(parser)
  stop("Missing moves.csv")
}

input_csv <- args$args[1]
opts <- args$options

moves <- read.csv(input_csv, stringsAsFactors = FALSE)

# Extract numeric file (1-8) and rank (1-8) from destination square
moves <- moves %>%
  mutate(file = match(substr(to, 1, 1), letters[1:8]),
         rank = as.integer(substr(to, 2, 2)))

out_dir <- "analysis/heatmaps"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

pieces <- unique(moves$piece)

bin_edges <- seq(0, 8, length.out = opts$bins + 1)

for (p in pieces) {
  dfp <- moves %>% filter(piece == p)

  # Compute bin counts for export
  counts <- dfp %>%
    mutate(file_bin = cut(file, breaks = bin_edges, labels = FALSE, include.lowest = TRUE),
           rank_bin = cut(rank, breaks = bin_edges, labels = FALSE, include.lowest = TRUE)) %>%
    group_by(rank_bin, file_bin) %>%
    tally(name = "freq")

  mat <- matrix(0, nrow = opts$bins, ncol = opts$bins,
                dimnames = list(opts$bins:1, letters[1:opts$bins]))
  for (i in seq_len(nrow(counts))) {
    r <- counts$rank_bin[i]
    f <- counts$file_bin[i]
    mat[r, f] <- counts$freq[i]
  }
  csv_path <- file.path(out_dir, paste0("heatmap_", p, "_bins", opts$bins, ".csv"))
  json_path <- file.path(out_dir, paste0("heatmap_", p, "_bins", opts$bins, ".json"))
  write.csv(mat, file = csv_path)
  write_json(as.data.frame(mat), path = json_path, pretty = TRUE)

  theme_fun <- get(paste0("theme_", opts$theme), envir = asNamespace("ggplot2"))
  g <- ggplot(dfp, aes(x = file, y = rank)) +
    geom_bin2d(bins = opts$bins) +
    scale_x_continuous(breaks = 1:8, labels = letters[1:8]) +
    scale_y_continuous(trans = "reverse", breaks = 1:8) +
    scale_fill_distiller(palette = opts$palette, direction = 1) +
    ggtitle(paste("Move frequencies for", p)) +
    theme_fun()
  ggsave(file.path(out_dir, paste0("heatmap_", p, "_bins", opts$bins, ".png")), g,
         dpi = opts$resolution)
}
