# Load necessary libraries
library(httr)
library(jsonlite)

# Load the Web of Science Starter API key
source('apikeys.R')

# Define your search query
search_query <- "TS=(('artificial intelligence' or ai) and 'scientific writing')"

# Set up the parameters for the API request
params <- list(
  'db' = 'WOS',
  'limit' = 50,
  'q' = search_query,
  'page' = 1
)

# Make the initial GET request to the Web of Science Starter API
response <- GET(
  "https://api.clarivate.com/apis/wos-starter/v1/documents",
  query = params,
  add_headers(`X-ApiKey` = .starter_apikey)
)

# Parse the initial JSON content of the response
initial_content <- content(response, as = "text", encoding = "UTF-8")
initial_json <- fromJSON(initial_content, flatten = TRUE)
records = initial_json$hits

# Calculate the number of necessary requests to retrieve all the data
documents_found <- initial_json$metadata$total
requests_required <- ((documents_found - 1 ) %/% params$limit) + 1

# Send subsequent API requests
if (requests_required > 1) {
  for (i in 2:requests_required) {
    params$page <- i
    response <- GET(
      "https://api.clarivate.com/apis/wos-starter/v1/documents",
      query = params,
      add_headers(`X-ApiKey` = .starter_apikey)
    )
    subsequent_content <- content(response, as = "text", encoding = "UTF-8")
    subsequent_json <- fromJSON(subsequent_content, flatten = TRUE)
    records <- merge(records, subsequent_json$hits, all = TRUE)
    print(paste("Request #", i, " of ", requests_required, sep=""))
  }
}

# View the result as a dataframe
View(records)

# Start plotting
pub_years <- table(records$source.publishYear)
barplot(pub_years, col="#B175E1", border="#B175E1")

