# Advanced evaluation that considers king safety and enemy material.
# The function returns a score from White's perspective.
# ``enemy_material`` is a named list with entries ``white`` and ``black``
# representing the attacking potential of each side (1 = full material).

#' Evaluate a chess position with basic king-safety heuristics.
#'
#' @param fen FEN string describing the position.
#' @param enemy_material named list with keys ``white`` and ``black`` used to
#'   scale king safety depending on remaining attacking material.
#' @return numeric evaluation (positive = advantage for White).
#' @examples
#' eval_position_complex("8/8/8/8/8/8/8/4K3 w - - 0 1")
#' eval_position_complex("8/8/8/8/8/8/8/4K3 w - - 0 1", list(white=1, black=0.5))


.eval_parse_board <- function(fen) {
  rows <- strsplit(strsplit(fen, " ")[[1]][1], "/")[[1]]
  board <- character()
  for (row in rows) {
    chars <- strsplit(row, "")[[1]]
    for (ch in chars) {
      if (grepl("[0-9]", ch)) {
        board <- c(board, rep(" ", as.integer(ch)))
      } else {
        board <- c(board, ch)
      }
    }
  }
  board
}

.eval_to_index <- function(r, c) (r - 1) * 8 + c
.eval_to_row   <- function(i) ((i - 1) %/% 8) + 1
.eval_to_col   <- function(i) ((i - 1) %% 8) + 1

.eval_king_zone <- function(kidx) {
  if (is.na(kidx) || length(kidx) == 0) return(integer())
  r <- .eval_to_row(kidx)
  c <- .eval_to_col(kidx)
  zone <- integer()
  for (dr in -1:1) {
    for (dc in -1:1) {
      if (dr == 0 && dc == 0) next
      nr <- r + dr; nc <- c + dc
      if (nr >= 1 && nr <= 8 && nc >= 1 && nc <= 8) {
        zone <- c(zone, .eval_to_index(nr, nc))
      }
    }
  }
  zone
}

.eval_get_attacks <- function(board, color) {
  attacks <- integer()
  pieces <- if (color == "white") LETTERS else letters
  for (i in seq_along(board)) {
    p <- board[i]
    if (!(p %in% pieces)) next
    r <- .eval_to_row(i); c <- .eval_to_col(i)
    lower <- tolower(p)
    if (lower == "p") {
      dir <- if (color == "white") -1 else 1
      for (dc in c(-1, 1)) {
        nr <- r + dir; nc <- c + dc
        if (nr >= 1 && nr <= 8 && nc >= 1 && nc <= 8) {
          attacks <- c(attacks, .eval_to_index(nr, nc))
        }
      }
    } else if (lower == "n") {
      moves <- list(c(-2,-1),c(-2,1),c(-1,-2),c(-1,2),c(1,-2),c(1,2),c(2,-1),c(2,1))
      for (mv in moves) {
        nr <- r + mv[1]; nc <- c + mv[2]
        if (nr >= 1 && nr <= 8 && nc >= 1 && nc <= 8) {
          attacks <- c(attacks, .eval_to_index(nr, nc))
        }
      }
    } else if (lower %in% c("b", "r", "q")) {
      dirs <- list()
      if (lower %in% c("b", "q")) {
        dirs <- c(dirs, list(c(-1,-1),c(-1,1),c(1,-1),c(1,1)))
      }
      if (lower %in% c("r", "q")) {
        dirs <- c(dirs, list(c(-1,0),c(1,0),c(0,-1),c(0,1)))
      }
      for (d in dirs) {
        nr <- r; nc <- c
        repeat {
          nr <- nr + d[1]; nc <- nc + d[2]
          if (nr < 1 || nr > 8 || nc < 1 || nc > 8) break
          idx <- .eval_to_index(nr, nc)
          attacks <- c(attacks, idx)
          if (board[idx] != " ") break
        }
      }
    } else if (lower == "k") {
      for (dr in -1:1) {
        for (dc in -1:1) {
          if (dr == 0 && dc == 0) next
          nr <- r + dr; nc <- c + dc
          if (nr >= 1 && nr <= 8 && nc >= 1 && nc <= 8) {
            attacks <- c(attacks, .eval_to_index(nr, nc))
          }
        }
      }
    }
  }
  attacks
}

.eval_compute_threat <- function(board, kidx, attacker) {
  if (is.na(kidx) || length(kidx) == 0) {
    return(list(attack = 0, double = 0, check = 0))
  }
  atk <- .eval_get_attacks(board, attacker)
  zone <- .eval_king_zone(kidx)
  zone_hits <- atk[atk %in% zone]
  check <- ifelse(kidx %in% atk, 1, 0)
  doubles <- sum(table(zone_hits) > 1)
  list(attack = length(zone_hits), double = doubles, check = check)
}

#' @export
#' @rdname eval_position_complex

eval_position_complex <- function(fen, enemy_material = list(white = 1, black = 1)) {
  board <- .eval_parse_board(fen)
  whites <- sum(board %in% LETTERS)
  blacks <- sum(board %in% letters)
  material <- whites - blacks

  wk <- if (any(board == "K")) which(board == "K")[1] else NA
  bk <- if (any(board == "k")) which(board == "k")[1] else NA

  weights <- c(attack = 0.5, double = 1.0, check = 3.0)
  white_threat <- .eval_compute_threat(board, wk, "black")
  black_threat <- .eval_compute_threat(board, bk, "white")

  white_penalty <- sum(unlist(white_threat) * weights) * enemy_material$black
  black_penalty <- sum(unlist(black_threat) * weights) * enemy_material$white

  material + (black_penalty - white_penalty)
}

