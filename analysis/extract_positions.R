#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
})

#' Extract piece coordinates from FEN strings
#'
#' @param fens Character vector of FEN strings.
#' @return Data frame with columns `file`, `rank`, and `piece`.
extract_positions <- function(fens) {
  records <- data.frame(file = character(), rank = integer(), piece = character(), stringsAsFactors = FALSE)
  for (fen in fens) {
    parts <- strsplit(fen, " ")[[1]]
    board <- parts[1]
    ranks <- strsplit(board, "/")[[1]]
    for (r_idx in seq_along(ranks)) {
      rank_num <- 9 - r_idx
      row <- ranks[r_idx]
      file_idx <- 1
      chars <- strsplit(row, "")[[1]]
      for (ch in chars) {
        if (grepl("^[1-8]$", ch)) {
          file_idx <- file_idx + as.integer(ch)
        } else {
          file_letter <- letters[file_idx]
          records <- rbind(records, data.frame(file = file_letter, rank = rank_num, piece = ch, stringsAsFactors = FALSE))
          file_idx <- file_idx + 1
        }
      }
    }
  }
  records
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: extract_positions.R <fen_file> <out_csv>")
}

fen_strings <- read_lines(args[1])
positions <- extract_positions(fen_strings)
write_csv(positions, args[2])
