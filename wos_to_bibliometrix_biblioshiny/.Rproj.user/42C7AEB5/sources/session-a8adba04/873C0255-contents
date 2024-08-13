# Load necessary libraries
library(httr)
library(jsonlite)

# Load the Web of Science Expanded API key
source('apikeys.R')

# Define your search query
search_query <- "OG=Clarivate"

# Set up the parameters for the API request
params <- list(
  'databaseId' = 'WOS',
  'count' = 100,
  'usrQuery' = search_query,
  'firstRecord' = 1
)

# Make the initial GET request to the Web of Science Expanded API
response <- GET(
  "https://wos-api.clarivate.com/api/wos",
  query = params,
  add_headers(`X-ApiKey` = expanded_apikey)
)

# Parse the initial JSON content of the response
initial_content <- content(response, as = "text", encoding = "UTF-8")
initial_json <- fromJSON(initial_content, flatten = TRUE)
records = initial_json$Data$Records$records$REC

# Calculate the number of necessary requests to retrieve all the data
documents_found <- initial_json$QueryResult$RecordsFound
requests_required <- ((documents_found - 1 ) %/% params$count) + 1

# Send subsequent API requests
if (requests_required > 1) {
  for (i in 2:requests_required) {
    params$firstRecord <- ((i - 1) * 100) + 1 
    response <- GET(
      "https://wos-api.clarivate.com/api/wos",
      query = params,
      add_headers(`X-ApiKey` = expanded_apikey)
    )
    subsequent_content <- content(response, as = "text", encoding = "UTF-8")
    subsequent_json <- fromJSON(subsequent_content, flatten = TRUE)
    records <- merge(records, subsequent_json$Data$Records$records$REC, all = TRUE)
    print(paste("Request #", i, " of ", requests_required, sep=""))
  }
}

# View the result as a dataframe
View(records)
