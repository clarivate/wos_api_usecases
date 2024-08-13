# Load necessary libraries
library(httr)
library(jsonlite)
library(bibliometrix)

# Load the Web of Science Starter API key
source('apikeys.R')

# Define your search query
search_query <- "UT=WOS:000245406500017"

# Define if you require cited references metadata (gives you more options for 
# analysis on Bibliometrix/Biblioshiny but significantly increases the time
# required to retrieve all the metadata)
retrieve_cited_references_flag = TRUE

# Process JSON data into a string
json_to_str <- function(x) {
  return_string <- ""
  for(i in rownames(x)) {
    print(x[i, ]$UID)
    static_data <- x[i, ]$static_data
    dynamic_data <- x[i, ]$dynamic_data
    fullrecord_metadata <- x[i, ]$static_data$fullrecord_metadata
    abstracts <- x[i, ]$static_data$fullrecord_metadata$abstracts
    category_info <- x[i, ]$static_data$fullrecord_metadata$category_info
    return_string <- paste(
      return_string,
      "PT ",
      fetch_source_type(static_data$summary$pub_info$pubtype),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "AU ",
      fetch_author_wos_standard_names(static_data$summary$names$name),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "AF ",
      fetch_author_full_names(static_data$summary$names$name),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "TI ",
      fetch_doc_title(static_data$summary$titles$title),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "SO ",
      fetch_source_title(static_data$summary$titles$title),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "JI ",
      fetch_source_abbreviation(static_data$summary$titles$title),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "LA ",
      fetch_languages(fullrecord_metadata$languages$language),
      "\n",
      sep = ""
    )
    
    return_string <- paste(
      return_string,
      "DT ",
      fetch_doctypes(static_data$summary$doctypes$doctype),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "DE ",
      fetch_keywords(fullrecord_metadata$keywords$keyword),
      "\n",
      sep = ""
      )

    return_string <- paste(
      return_string,
      "ID ",
      fetch_keywords(static_data$item$keywords_plus$keyword),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "AB ",
      fetch_abstract(abstracts$abstract$abstract_text$p),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "C1 ",
      fetch_c1(fullrecord_metadata$addresses),
      "\n",
      sep = ""
      )

    return_string <- paste(
      return_string,
      "RP ",
      fetch_rp(fullrecord_metadata$reprint_addresses),
      "\n",
      sep = ""
      )

    if(retrieve_cited_references_flag == TRUE) {
      return_string <- paste(
        return_string,
        "CR ",
        cited_api_request(x[i, ]$UID, .expanded_apikey),
        "\n",
        sep = ""
        )
    }
    
    return_string <- paste(
      return_string,
      "PY ",
      static_data$summary$pub_info$pubyear,
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "TC ",
      fetch_times_cited(dynamic_data$citation_related$tc_list$silo_tc),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "WC ",
      fetch_subject_categories(category_info$subjects$subject),
      "\n",
      sep = ""
      )
    
    return_string <- paste(
      return_string,
      "DI ",
      fetch_doi(dynamic_data$cluster_related$identifiers$identifier),
      "\n",
      sep = ""
      )
    
    return_string <- paste(return_string, "UT ", x[i, ]$UID, "\n", sep = "")
    return_string <- paste(return_string, "ER\n\n", sep = "")
  }
  return(return_string)
}

# Retrieve Source Type field
fetch_source_type <- function(x) {
  if(x == "Journal") {
    return("J")
  } else if(x == "Book" || x == "Books") {
    return("B")
  } else if(x == "Book in series" || x == "Books in series") {
    return("S")
  } else if(x == "Patent") {
    return("P")
  } else {
    print(paste("Unexpected source type:", x, sep = " "))
  }
}

# Retrieve Web of Science standard names (first and middle names abbreviated)
fetch_author_wos_standard_names <- function(x) {
  if(is.null(x$wos_standard)) {
    if(is.null(nrow(x[[1]]))) {
      return(x[[1]]$wos_standard)
    } else {
      return(paste(x[[1]][, "wos_standard"], collapse = "\n   "))
    }
  } else {
    return(x$wos_standard)
  }
}

# Retrieve Web of Science full author names
fetch_author_full_names <- function(x) {
  if(is.null(x$full_name)) {
    if(is.null(nrow(x[[1]]))) {
      return(x[[1]]$full_name)
    } else {
      return(paste(x[[1]][, "full_name"], collapse = "\n   "))
    }
  } else {
    return(x$full_name)
  }
}

# Retrieve the Document Title field
fetch_doc_title <- function(x) {
  row <- x[[1]][x[[1]]$type == 'item', ]
  return(row$content)
}

# Retrieve the full Source Title field
fetch_source_title <- function(x) {
  row <- x[[1]][x[[1]]$type == 'source', ]
  return(row$content)
}

# Retrieve the abbreviated Source Title field
fetch_source_abbreviation <- function(x) {
  if('abbrev_iso' %in% x[[1]]$type) {
    row <- x[[1]][x[[1]]$type == 'abbrev_iso', ]
    return(row$content)
  } else {
    return("")
  }
}

# Retrieve document language
fetch_languages <- function(x) {
  return(x$content)
}

# Retrieve the Document Type(s) field
fetch_doctypes <- function(x) {
  return(paste(x[[1]], collapse = "; "))
}

# Retrieve keywords - both Author Keywords and Keywords Plus
fetch_keywords <- function(x) {
  if(is.null(x[[1]])) {
    return(NA)
  } else {
  return(paste(x[[1]], collapse = "; "))
  }
}

# Retrieve the Abstract field
fetch_abstract <- function(x) {
  if(is.character(x[[1]]) && length(x[[1]]) == 1) {
    return(x[[1]])
  } else {
    return(paste(x[[1]], collapse = "\n   "))
  }
}

# Retrieve the Affiliation links
fetch_c1 <- function(x) {
  browser()
  if(x$count == 1) {
    if(!is.null(x$address_name$names$name)) {
      authors <- fetch_c1_author_names(x$address_name$names$name)
      org <- x$address_name$address_spec$full_address
    } else {
      authors <- fetch_c1_author_names(x$address_name[[1]]$names$name)
      org <- x$address_name[[1]]$address_spec$full_address
    }
    c1 <- paste("[", authors, "] ", org, ".", sep = "")
  } else {
    c1 <- list()
    for(i in rownames(x$address_name[[1]])) {
      if (is.null(x$address_name[[1]][i, ]$names)) {
        authors <- ""
      } else if (is.null(x$address_name[[1]][i, ]$names$name)) {
        authors <- ""
      } else if (is.na(x$address_name[[1]][i, ]$names$count)) {
        authors <- ""
      }else if (x$address_name[[1]][i, ]$names$count == 1) {
        authors <- fetch_c1_author_names(x$address_name[[1]][i, ]$names$name)
      } else {
        authors <- fetch_c1_author_names(x$address_name[[1]][i, ]$names$name)
      }
      org <- x$address_name[[1]][i, ]$address_spec$full_address
      c1[i] <- paste("[", authors, "] ", org, ".", sep = "")
    }
  }
  return(paste(c1, collapse = "\n   "))
}

# Retrieve the Author names for Affiliation (including Reprint) links
fetch_c1_author_names <- function(x) {
  if(!is.list(x[[1]])) {
    return(x$full_name)
  } else if (is.null(nrow(x[[1]]))) {
    return(x[[1]]$full_name)
  } else {
  authors <- list()
  for(i in rownames(x[[1]])) {
    authors[i] <- x[[1]][i, ]$full_name
    }
  }
  return(paste(authors, collapse = "; "))
}

# Retrieve the Reprint Author metadata, including the Corresponding Address
fetch_rp <- function(x) {
  if(is.null(x) | is.na(x$count)) {
    return("")
  } else if(x$count == 1) {
    if(!is.null(x$address_name$names$name)) {
      authors <- fetch_c1_author_names(x$address_name$names$name)
      org <- x$address_name$address_spec$full_address
    } else {
      authors <- fetch_c1_author_names(x$address_name[[1]]$names$name)
      org <- x$address_name[[1]]$address_spec$full_address
    }
    rp <- paste(authors, " (corresponding author), ", org, ".", sep = "")
  } else {
    rp <- list()
    for(i in rownames(x$address_name[[1]])) {
      if(is.null(x$address_name[[1]][i, ]$names)) {
        authors <- ""
      } else if (is.null(x$address_name[[1]][i, ]$names$name)) {
        authors <- ""
      } else if (is.na(x$address_name[[1]][i, ]$names$count)) {
        authors <- ""
      } else if (x$address_name[[1]][i, ]$names$count == 1) {
        authors <- fetch_c1_author_names(x$address_name[[1]][i, ]$names$name)
      } else {
        authors <- fetch_c1_author_names(x$address_name[[1]][i, ]$names$name)
      }
      org <- x$address_name[[1]][i, ]$address_spec$full_address
      rp[i] <- paste(authors, " (corresponding author), ", org, ".", sep = "")
    }
  }
  return(paste(rp, collapse = "; "))
}

# Send the API request to /references endpoint to get the JSON file
# with cited references
cited_api_request <- function(x, .apikey) {
  params <- list(
    'databaseId' = 'WOS',
    'count' = 100,
    'uniqueId' = x,
    'firstRecord' = 1
  )
  
  # Make the initial GET request to the /references endpoint
  response <- GET(
    "https://wos-api.clarivate.com/api/wos/references",
    query = params,
    add_headers(`X-ApiKey` = .apikey)
  )
  
  # Parse the initial JSON content of the response
  initial_cited_content <- content(response, as = "text", encoding = "UTF-8")
  initial_cited_json <- fromJSON(initial_cited_content, flatten = FALSE)
  cited_references <- initial_cited_json$Data

  # Calculate the number of necessary requests to retrieve all the data
  cited_refs_found <- initial_cited_json$QueryResult$RecordsFound
  requests_required <- ((cited_refs_found - 1 ) %/% params$count) + 1
  
  # Send subsequent API requests if required
  if (requests_required > 1) {
    for (i in 2:requests_required) {
      params$firstRecord <- ((i - 1) * 100) + 1 
      response <- GET(
        "https://wos-api.clarivate.com/api/wos/references",
        query = params,
        add_headers(`X-ApiKey` = .apikey)
      )
      
      subsequent_cited_content <- content(
        response,
        as = "text",
        encoding = "UTF-8"
        )
      
      subsequent_cited_json <- fromJSON(
        subsequent_cited_content,
        flatten = FALSE
        )
      
      cited_references <- merge(
        cited_references,
        subsequent_cited_json$Data,
        all = TRUE
        )
    }
  }
  
  # Return necessary metadata fields from cited references JSON
  return(fetch_cited_references(cited_references))
}

# Retrieve necessary metadata field for cited references
fetch_cited_references <- function(x) {
  if(is.null(nrow(x))) {
    return("")
  } else {
    cited_suboutput <- c()
    for(i in rownames(x)) {
      cited_reference <- c()
      if ("CitedAuthor" %in% colnames(x[i, ])) {
        if (!is.null(x[i, ]$CitedAuthor)) {
          cited_reference <- append(
            cited_reference,
            fetch_cited_authors(x[i, ]$CitedAuthor)
          )
        }
      }
      
      if ("Year" %in% colnames(x[i, ])) {
        if (x[i, ]$Year != 1000) {
          cited_reference <- append(cited_reference, x[i, ]$Year)
        }
      }
      
      if ("CitedWork" %in% colnames(x[i, ])) {
        if (!is.null(x[i, ]$CitedWork)) {
          cited_reference <- append(cited_reference, x[i, ]$CitedWork)
        }
      }
      
      if("Volume" %in% colnames(x[i, ])) {
        if(!is.na(x[i, ]$Volume)) {
          cited_reference <- append(
            cited_reference,
            paste("V", x[i, ]$Volume, sep = "")
            )
        }
      }
      if("Page" %in% colnames(x[i, ])) {
        if(!is.na(x[i, ]$Page)) {
          cited_reference <- append(
            cited_reference,
            paste("P", x[i, ]$Page, sep = "")
            )
        }
      }
      if("DOI" %in% colnames(x[i, ])) {
        if(!is.na(x[i, ]$DOI)) {
          cited_reference <- append(
            cited_reference,
            paste("DOI", x[i, ]$DOI, sep = " ")
            )
        }
      }
      cited_suboutput <- append(
        cited_suboutput,
        paste(cited_reference, collapse = ", ")
        )
    }
    return(paste(sort(cited_suboutput), collapse = "\n   "))
  }
}

# Retrieve cited authors metadata
fetch_cited_authors <- function(x) {
  x_vectorized <- strsplit(x, split = ', ')
  non_last_name <- strsplit(x_vectorized[[1]][2], split = " ")[[1]]
  initials = ""
  for(i in c(1:length(non_last_name))) {
    initials <- paste(initials, substr(non_last_name[i], 1, 1), sep = "")
  }
  return(paste(x_vectorized[[1]][1], initials, sep=" "))
}

# Retrieve Times Cited counts
fetch_times_cited <- function(x) {
  row <- x[[1]][x[[1]]$coll_id == 'WOS', ]
  return(row$local_count)
}

# Retrieve Web of Science Subject Categories
fetch_subject_categories <- function(x) {
  categories <- c()
  for(i in rownames(x[[1]])) {
    if(x[[1]][i, ]$ascatype == "traditional") {
      categories <- append(categories, x[[1]][i, ]$content)
    }
  }
  return(paste(categories, collapse = "; "))
}

# Retrieve DOI
fetch_doi <- function(x) {
  if("doi" %in% x[[1]]$type) {
    row <- x[[1]][x[[1]]$type == 'doi', ]
    return(row$value)
  } else {
    return("")
  }
}

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
  add_headers(`X-ApiKey` = .expanded_apikey)
)

# Parse the initial JSON content of the response
initial_content <- content(response, as = "text", encoding = "UTF-8")
initial_json <- fromJSON(initial_content, flatten = FALSE)
output <- "FN Clarivate Analytics Web of Science\nVR 1.0\n"
output <- paste(
  output,
  json_to_str(initial_json$Data$Records$records$REC),
  sep = ""
  )

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
      add_headers(`X-ApiKey` = .expanded_apikey)
    )
    subsequent_content <- content(response, as = "text", encoding = "UTF-8")
    subsequent_json <- fromJSON(subsequent_content, flatten = FALSE)

    output <- paste(output,
                    json_to_str(subsequent_json$Data$Records$records$REC),
                    sep = ""
                    )
    print(paste(i, "out of", requests_required, "requests complete", sep = " "))
  }
}

output <- paste(output, "EF", sep = "")

# Save output string into a text file
if(retrieve_cited_references_flag == TRUE) {
  filename <- paste(search_query, " - with cited references.txt", sep = "")
} else {
  filename <- paste(search_query, ".txt", sep = "")
}
safe_filename <- gsub("*", "", gsub("?", "", gsub("'", "", filename)))
writeLines(output, file(paste("Downloads/", safe_filename, sep = "")))

# mem.maxVSize(vsize = 128000)

# biblioshiny(maxUploadSize=2000)

M <- convert2df(output)
View(M)
