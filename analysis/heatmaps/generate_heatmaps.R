#!/usr/bin/env Rscript
# Generate heatmaps from FEN data
# Usage: Rscript generate_heatmaps.R <input_csv> [output_dir]

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript generate_heatmaps.R <input_csv> [output_dir]")
}

input_csv <- args[1]
# By default, write outputs next to the input CSV
output_dir <- if (length(args) > 1) args[2] else dirname(normalizePath(input_csv))

# Check if required packages are available
# Keep dependencies minimal: only jsonlite is required
required_packages <- c("jsonlite")
missing_packages <- required_packages[!required_packages %in% installed.packages()[,"Package"]]

if (length(missing_packages) > 0) {
  stop("Missing required R packages: ", paste(missing_packages, collapse = ", "), 
       ". Install with: install.packages(c('", paste(missing_packages, collapse = "', '"), "'))")
}

# Load required libraries
library(jsonlite)

# Read the CSV data
if (!file.exists(input_csv)) {
  stop("Input CSV file not found: ", input_csv)
}

data <- read.csv(input_csv, stringsAsFactors = FALSE)

# Check if data is empty
if (nrow(data) == 0) {
  cat("No data found in CSV file\n")
  quit(status = 0)
}

# Create output directory if it doesn't exist
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Convert square names to coordinates
square_to_coords <- function(square) {
  file <- match(substr(square, 1, 1), letters[1:8]) - 1  # 0-7
  rank <- as.numeric(substr(square, 2, 2)) - 1  # 0-7
  return(c(file, rank))
}

# Create heatmap for each piece type
piece_types <- unique(data$piece)
cat("Processing", length(piece_types), "piece types:", paste(piece_types, collapse = ", "), "\n")

for (piece in piece_types) {
  # Filter data for this piece type
  piece_data <- data[data$piece == piece, ]
  
  # Create 8x8 heatmap matrix
  heatmap_matrix <- matrix(0, nrow = 8, ncol = 8)
  
  # Count occurrences for each square
  for (i in 1:nrow(piece_data)) {
    coords <- square_to_coords(piece_data$to[i])
    # R uses 1-based indexing, and we want rank 8 at top (row 1)
    row <- 8 - coords[2]  # 8 - rank (0-7) = 1-8
    col <- coords[1] + 1  # file (0-7) + 1 = 1-8
    heatmap_matrix[row, col] <- heatmap_matrix[row, col] + 1
  }
  
  # Convert to list format for JSON
  heatmap_list <- lapply(1:8, function(i) heatmap_matrix[i, ])
  
  # Save as JSON
  output_file <- file.path(output_dir, paste0("heatmap_", piece, ".json"))
  write_json(heatmap_list, output_file, pretty = TRUE)
  cat("Saved heatmap for", piece, "to", output_file, "\n")
}

cat("Heatmap generation completed successfully\n")