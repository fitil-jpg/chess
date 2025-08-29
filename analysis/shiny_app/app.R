library(shiny)
library(jsonlite)
library(ggplot2)

# Paths relative to the application directory
heatmap_dir <- normalizePath(file.path("..", "heatmaps"), mustWork = FALSE)
scenarios_csv <- file.path("..", "scenarios.csv")
scenarios_json <- file.path("..", "scenarios.json")

# discover available pieces from heatmap files
heatmap_files <- list.files(heatmap_dir, pattern = "heatmap_(.*)_bins.*\\.(csv|json)$")
pieces <- sort(unique(sub("heatmap_(.*)_bins.*", "\\1", heatmap_files)))

# helper to load heatmap for a piece
load_heatmap <- function(piece) {
  csv <- file.path(heatmap_dir, sprintf("heatmap_%s_bins8.csv", piece))
  json <- file.path(heatmap_dir, sprintf("heatmap_%s_bins8.json", piece))
  if (file.exists(csv)) {
    as.matrix(read.csv(csv, row.names = 1, check.names = FALSE))
  } else if (file.exists(json)) {
    df <- as.data.frame(fromJSON(json))
    as.matrix(df)
  } else {
    matrix(0, nrow = 8, ncol = 8)
  }
}

# load scenario data from CSV or JSON
load_scenarios <- function() {
  if (file.exists(scenarios_csv)) {
    read.csv(scenarios_csv, stringsAsFactors = FALSE)
  } else if (file.exists(scenarios_json)) {
    fromJSON(scenarios_json)
  } else {
    data.frame()
  }
}

scenarios <- load_scenarios()
scenario_ids <- sort(unique(scenarios$id))

ui <- fluidPage(
  titlePanel("Heatmap viewer"),
  sidebarLayout(
    sidebarPanel(
      selectInput("piece", "Piece", choices = pieces, selected = pieces[1]),
      selectInput("scenario", "Scenario", choices = c("All", scenario_ids), selected = "All")
    ),
    mainPanel(
      plotOutput("board", height = "400px")
    )
  )
)

server <- function(input, output, session) {
  heatmap_data <- reactive({
    req(input$piece)
    mat <- load_heatmap(input$piece)
    df <- as.data.frame(as.table(mat))
    colnames(df) <- c("rank", "file", "value")
    df$rank <- as.numeric(as.character(df$rank))
    df$file_idx <- match(df$file, letters[1:8])
    df
  })

  scenario_data <- reactive({
    if (nrow(scenarios) == 0) return(NULL)
    sc <- scenarios
    sc$file_idx <- match(substr(sc$square, 1, 1), letters[1:8])
    sc$rank <- as.integer(substr(sc$square, 2, 2))
    if (!is.null(input$scenario) && input$scenario != "All") {
      sc <- sc[sc$id == input$scenario, , drop = FALSE]
    }
    sc
  })

  output$board <- renderPlot({
    df <- heatmap_data()
    p <- ggplot(df, aes(file_idx, rank, fill = value)) +
      geom_tile(color = "grey80") +
      scale_x_continuous(breaks = 1:8, labels = letters[1:8]) +
      scale_y_reverse(breaks = 1:8) +
      scale_fill_gradient(low = "white", high = "red") +
      coord_fixed() +
      theme_minimal() +
      theme(panel.grid = element_blank(),
            axis.title = element_blank())
    sc <- scenario_data()
    if (!is.null(sc) && nrow(sc) > 0) {
      p <- p + geom_point(data = sc, aes(x = file_idx, y = rank),
                          colour = "purple", size = 5)
    }
    p
  })
}

shinyApp(ui, server)
