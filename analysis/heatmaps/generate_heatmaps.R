#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: generate_heatmaps.R <moves.csv>")
}

moves <- read.csv(args[1], stringsAsFactors = FALSE)

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
  g <- ggplot(plotdf, aes(x = file, y = rank, fill = freq)) +
    geom_tile() +
    scale_y_continuous(trans = "reverse") +
    scale_fill_gradient(low = "white", high = "red") +
    ggtitle(paste("Move frequencies for", p))
  ggsave(file.path(out_dir, paste0("heatmap_", p, ".png")), g)
}
