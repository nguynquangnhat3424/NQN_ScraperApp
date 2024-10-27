# NQN_ScraperApp
**Objective:**  To create an application that scrapes content from 6 news channels and 2 video platforms (YouTube & TikTok) using keywords.

## Implementation Steps:
1. For each data source that needs to be scraped, the following 4 steps are required:
   * Scrape content from any given article/video using its URL.
   * Analyze the URL of the desired website to transform keywords into URLs as if searching in the site's search bar.
   * Scrape a list of articles/videos based on the URL generated from the keywords (ensuring each article/video in the list has a corresponding URL).
   * Apply a content scraping function on the dataframe containing the list of articles/videos to retrieve the corresponding content.
2. Build a user interface for the app that allows users to input keywords and specify the number of articles/videos to scrape, while also enabling users to download the scraped dataframe as an Excel file.

**Note:** Ensure to customize the scraping functions according to the specific structure of each website and platform.

![image](https://github.com/user-attachments/assets/fab9ed26-8457-45fe-a827-d88db7cac11b)
