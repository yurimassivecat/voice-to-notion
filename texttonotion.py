import os
import random
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from notion_client import Client

# Please replace 'YOUR-NOTION-TOKEN' with your actual Notion token
notion = Client(auth="YOUR-NOTION-TOKEN")

# Please replace 'YOUR-PARENT-PAGE-ID' with your actual parent page ID
parent_page_id = "YOUR-PARENT-PAGE-ID"

# Please replace 'YOUR-FOLDER-PATH' with the actual path to the folder
folder_path = "YOUR-FOLDER-PATH"

# Function to get the database ID for a given database name
def get_database_id(database_name):
    # Search for all existing databases in the workspace
    existing_databases = notion.search(filter={"property": "object", "value": "database"}).get("results")
    # Loop through the databases and return the ID if the name matches
    for db in existing_databases:
        if db["title"][0]["plain_text"] == database_name:
            return db["id"]
    # If no match is found, return None
    return None

# Function to check if a page with a given title already exists in the database
def page_exists(database_id, title):
    # Query the database for pages with the specified title
    existing_pages = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "property": "Name",
                "title": {
                    "equals": title
                }
            }
        }
    ).get("results")

    # Return True if one or more pages are found, False otherwise
    return len(existing_pages) > 0

# Function to create a new database in the specified parent page
def create_database(parent_id, database_name):
    # Define the database structure
    new_database = {
        "parent": {"page_id": parent_id},
        "properties": {
            "Name": {"title": {}},
            "Summary": {"rich_text": {}},
            "Transcript": {"rich_text": {}},
            "Original File Name": {"rich_text": {}},
            "Tags": {"multi_select": {}},  # Add this line for Tags property
            "Link": {"url": {}}           # Add this line for Links property
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": database_name
                }
            }
        ]
    }
    # Create the database and return the response
    return notion.databases.create(**new_database)

# This function finds the ID of a specific file in a specific folder on Google Drive.
def find_file_id(service, file_name):
    try:
        # folder_id specifies the exact Google Drive folder to search in.
        folder_id = "11zok4Vcx8k-pVToc8wxRyIrtodsoMaL6"

        # A query is constructed to search for the specific file within the specified folder.
        query = f"name = '{file_name}' and mimeType != 'application/vnd.google-apps.folder' and '{folder_id}' in parents"

        # Use the Google Drive service to execute the query.
        results = service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
        items = results.get("files", [])

         # If the file isn't found, print a message and return None. Otherwise, return the ID of the found file.
        if not items:
            print(f"No file found with the name: {file_name}")
            return None
        else:
            return items[0]["id"]
    # If there's an HTTP error (like a connection issue), print a message and return None.
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# This function generates a shareable Google Drive link to a file specified by its ID.   
def generate_shareable_link(file_id):
    try:
        # Connect to the Google Drive API service.
        service = get_drive_service()

        # Define the permissions for the shareable link. In this case, anyone can read the file.
        permission = {"type": "anyone", "role": "reader"}
        # Apply the permissions to the file, then get the web view link.
        service.permissions().create(fileId=file_id, body=permission, fields="id").execute()
        file = service.files().get(fileId=file_id, fields="webViewLink").execute()

        # Return the web view link.
        return file["webViewLink"]
    
    # If there's an HTTP error, print a message and return None.
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    
# This function builds and returns a service object for the Google Drive API.
def get_drive_service():
     # Define the scope of the service. In this case, full drive access is requested.
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # The path to the service account file, which is needed to authenticate with Google.
    SERVICE_ACCOUNT_FILE = 'G:\My Drive\Documents\Python projects\Voice Recordings\Google API\link-to-original-file-384107-be3e62b60836.json'

    # Authenticate with Google using the service account file, then build and return the service.
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

# This function creates a new page on Notion using the provided information.
def create_page(parent_id, title, summary, transcript, original_file_name, tags, link, max_retries=3):
    drive_service = get_drive_service()

    # Find the file ID and generate a shareable link
    file_id = None
    for _ in range(max_retries):
        file_id = find_file_id(drive_service, original_file_name)
        if file_id is not None:
            break
        else:
            print(f"File '{original_file_name}' not found. Retrying in 10 seconds...")
            time.sleep(10)

    if file_id is None:
        print(f"Skipping page with title '{title}' as the original file was not found after {max_retries} retries.")
        return

    link = generate_shareable_link(file_id)
    new_page = {
        "parent": {"database_id": parent_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Original File Name": {
                "rich_text": [
                    {
                        "text": {
                            "content": original_file_name
                        }
                    }
                ]
            },
            "Tags": {                       # Add this block for Tags property
                "multi_select": [
                    {
                        "name": tag
                    }
                    for tag in tags
                ]
            },
            "Link": {
                "url": link
            }

}

        }


    created_page = notion.pages.create(**new_page)
    page_id = created_page["id"]

    # Split the transcript into chunks of up to 2000 characters each
    transcript_chunks = [transcript[i:i + 2000] for i in range(0, len(transcript), 2000)]

    # Create a paragraph block for each transcript chunk
    transcript_blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        }
        for chunk in transcript_chunks
    ]

    # Add the summary and transcript as separate blocks
    page_content = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": summary}}]
            }
        },
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "Transcript"}}]
            }
        }
    ]

    # Add the transcript_blocks to the page_content list
    page_content.extend(transcript_blocks)

    for retry in range(max_retries):
        try:
            notion.blocks.children.append(
                block_id=page_id,
                children=page_content
            )
            print(f"Created new page with summary and transcript: {title}")
            break
        except notion_client.errors.HTTPResponseError as e:
            if e.status == 502 and retry < max_retries - 1:
                sleep_duration = 2 ** retry + random.uniform(0, 1)
                print(f"Encountered a 502 error. Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print(f"Failed to create page with summary and transcript: {title}")
                raise

# This function monitors a specified folder for new files.
def monitor_folder(folder_path, database_id):
    # A set of files that have already been processed, to avoid duplicates.
    processed_files = set()

    # A buffer time in seconds to avoid processing files that are still being written to.
    modification_buffer = 10  # 10-second buffer for file modification

    # Run indefinitely
    while True:
        # For each file in the folder
        for entry in os.scandir(folder_path):
            if (entry.is_file() and
                    entry.name.endswith("_summary.txt") and
                    entry.name not in processed_files):

                base_name, _ = os.path.splitext(entry.name)
                original_file_name = f"{base_name.replace('_summary', '')}.wav"
                transcript_file_name = f"{base_name.replace('_summary', '_transcript')}.txt"
                transcript_file_path = os.path.join(folder_path, transcript_file_name)

                # Check if both summary and transcript files are completely written to disk
                summary_mtime = entry.stat().st_mtime
                if not os.path.exists(transcript_file_path):
                    continue

                transcript_mtime = os.stat(transcript_file_path).st_mtime
                current_time = time.time()
                if (current_time - summary_mtime < modification_buffer or
                        current_time - transcript_mtime < modification_buffer):
                    continue

                with open(entry.path, "r", encoding="utf-8") as summary_file:
                    summary_lines = summary_file.readlines()
                    title = summary_lines[0].strip()
                    summary = "".join(summary_lines[1:])

                with open(transcript_file_path, "r", encoding="utf-8") as transcript_file:
                    transcript = transcript_file.read()

                tags = ["voice recording"]
                link = "link to original file"

                # Add a 10-second delay before creating the page in Notion
                print(f"Waiting for .5 seconds before creating the page for '{title}'...")
                time.sleep(.5)

                if not page_exists(database_id, title) and entry.name not in processed_files:
                    create_page(database_id, title, summary, transcript, original_file_name, tags, link)
                    print(f"Created new page with summary and transcript: {title}")
                    processed_files.add(entry.name)  # Add the filename to the processed_files set
                else:
                    print(f"Skipping page with title '{title}' as it already exists in the database or has been processed.")
            else:
                continue

        time.sleep(10)





if __name__ == "__main__":
    database_name = "Voice Recordings"
    database_id = get_database_id(database_name)
    
    if not database_id:
        database = create_database(parent_page_id, database_name)
        database_id = database["id"]
    
    monitor_folder(folder_path, database_id)