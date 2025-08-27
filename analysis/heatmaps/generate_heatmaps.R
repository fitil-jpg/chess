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
              help = "Resolution (DPI) for output PNG files [default %default]")
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

# Extract file (a-h) and rank (1-8) from destination square
moves <- moves %>%
  mutate(file = substr(to, 1, 1), rank = as.integer(substr(to, 2, 2)))

counts <- moves %>%
  group_by(piece, file, rank) %>%
  tally(name = "freq")

out_dir <- "analysis/heatmaps"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

pieces <- unique(counts$piece)

for (p in pieces) {
  dfp <- counts %>% filter(piece == p)
  mat <- matrix(0, nrow = 8, ncol = 8, dimnames = list(8:1, letters[1:8]))
  for (i in seq_len(nrow(dfp))) {
    r <- dfp$rank[i]
    f <- match(dfp$file[i], letters[1:8])
    mat[r, f] <- dfp$freq[i]
  }
  csv_path <- file.path(out_dir, paste0("heatmap_", p, ".csv"))
  json_path <- file.path(out_dir, paste0("heatmap_", p, ".json"))
  write.csv(mat, file = csv_path)
  write_json(as.data.frame(mat), path = json_path, pretty = TRUE)

  plotdf <- as.data.frame(as.table(mat))
  colnames(plotdf) <- c("rank", "file", "freq")
  theme_fun <- get(paste0("theme_", opts$theme), envir = asNamespace("ggplot2"))
  g <- ggplot(plotdf, aes(x = file, y = rank, fill = freq)) +
    geom_tile() +
    scale_y_continuous(trans = "reverse") +
    scale_fill_distiller(palette = opts$palette, direction = 1) +
    ggtitle(paste("Move frequencies for", p)) +
    theme_fun()
  ggsave(file.path(out_dir, paste0("heatmap_", p, ".png")), g, dpi = opts$resolution)
}
