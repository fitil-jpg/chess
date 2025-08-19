eval_position_complex <- function(fen) {
  # Simple evaluation: difference in number of pieces
  # between white (uppercase) and black (lowercase).
  board_str <- strsplit(strsplit(fen, " ")[[1]][1], "")[[1]]
  whites <- sum(board_str %in% LETTERS)
  blacks <- sum(board_str %in% letters)
  return(whites - blacks)
}
