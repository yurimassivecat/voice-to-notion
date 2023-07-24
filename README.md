voice-to-notion

An automated workflow that converts voice recordings to text using OpenAI's API and then uploads the text to Notion.
Introduction
This tool automatically creates new pages in Notion for voice recordings that are stored in a specific folder. It continuously monitors a specified folder for new voice recordings, and when it finds one, it creates a new page in a specified Notion database, attaching a transcript, a summary, and a shareable link to the original file in Google Drive. The tool is implemented in Python.

Setup
1.	Install Python
Make sure you have Python installed on your computer. You can download it from the official Python website.
2.	Install Required Libraries
Run the following command to install the required libraries:
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client notion-client
3.	Get your Notion API Key
You'll need to create an integration on Notion in order to get your API key. Go to the Notion integrations page to create one.
4.	Find your Parent Page ID
Navigate to the parent page in Notion where you want your voice recording pages to be created. The URL will look something like this: https://www.notion.so/My-Page-6f130c6104f347bea5a451a838a6ff10. The Parent Page ID is the last part of the URL.
5.	Folder to Monitor
Set the folder path that you want to monitor for new voice recordings.

User Workflow
Here is a typical user workflow for these scripts:
1.	Record an Audio Message
The user records an audio message on their phone or any other recording device. The type and length of the recording can vary depending on the user's needs. It could be a personal voice note, a meeting, a lecture, an interview, etc.
2.	Save to Google Drive
The recorded audio file is automatically saved to a designated folder in Google Drive. This can be set up on most smartphones and computers, providing an efficient and seamless way to manage and store recordings. Folder Sync for Android is good to sync the default save folder for your audio files with a folder in Google Drive. Folder Sync
3.	Automatic Conversion to Text
The voicetotext.py script monitors the Google Drive folder for new audio files. When it detects a new file, it automatically converts the spoken words in the audio file into written text using OpenAI's API.
4.	Save Text Files to Google Drive
The script then saves the transcribed text into a text file in a designated output folder in Google Drive. This creates a written record of the audio that can be easily accessed, searched, and shared.
5.	Upload to Notion
The txttoNotion.py script monitors the output folder for new text files. When it detects a new file, it automatically uploads the content of the text file to a specified page in Notion as a block of text.
This workflow creates an efficient system for turning spoken words into written notes in Notion, without requiring any manual transcription or data entry. It can be used in a variety of scenarios, from personal voice notes to business meetings and academic lectures.

Usage
1.	Setup the Script
Replace the placeholders in the script with your actual Notion API key, parent page ID, and the path to the folder you're monitoring.
2.	Run the Script
Run the script from the command line with the following command:
python script_name.py
3.	Create a Voice Recording
When you create a new voice recording in the folder that you're monitoring, the script will automatically create a new page in the specified Notion database.

Features
•	Continuously monitors a specific folder for new voice recordings.
•	Automatically creates new pages in a Notion database for each new voice recording.
•	Attaches a transcript, a summary, and a shareable link to the original file in Google Drive to the new Notion page.

Please replace script_name.py with the actual name of the Python script that you're running.


