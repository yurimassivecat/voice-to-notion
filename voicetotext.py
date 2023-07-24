import os
import time
from pydub import AudioSegment
import openai
import json
from tempfile import NamedTemporaryFile
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Set up your OpenAI API key
openai.api_key = "your_openai_api_key_here"

# Defining the input and output folders
folder_path = "path_to_your_voice_recordings_here"
output_path = "path_to_your_txt_files_here"


# Function to convert audio files to .wav format
def convert_to_wav(input_file):
    base_name, file_extension = os.path.splitext(input_file)
    output_file = f"{base_name}.wav"
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format="wav")
    return output_file

# Function to truncate text if it exceeds max tokens
def truncate_text(text, max_tokens):
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
    trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[MASK]", "[PAD]"])
    tokenizer.pre_tokenizer = Whitespace()
    tokenizer.train_from_iterator([text], trainer)
    tokens = tokenizer.encode(text).tokens

    # Truncating text if it exceeds max tokens
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        truncated_text = "".join(truncated_tokens).replace("▁", " ")
        return truncated_text
    else:
        return text


# Function to split audio into chunks
def split_audio(file_path, max_duration=25 * 1000):
    audio = AudioSegment.from_wav(file_path)
    audio_length = len(audio)

    # Splitting audio into chunks
    chunks = []
    for i in range(0, audio_length, max_duration):
        start = i
        end = min(i + max_duration, audio_length)
        chunks.append(audio[start:end])

    return chunks

# Function to transcribe audio chunks
def transcribe_audio(file_path):
    audio_chunks = split_audio(file_path)
    transcript = ""

    # Loop through each chunk and transcribe
    for chunk in audio_chunks:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            chunk.export(temp_audio_file.name, format="wav")
            with open(temp_audio_file.name, "rb") as file:
                response = openai.Audio.transcribe("whisper-1", file=file)
            temp_audio_file.close()
            os.unlink(temp_audio_file.name)

        transcript += response["text"]

    return transcript


# Main function to process audio files
def process_audio(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()[1:]
    if ext in ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]:
        chunks = chunk_audio(file_path)
        transcriptions = []
        for i, chunk in enumerate(chunks):
            chunk_path = f"temp_{i}.mp3"
            chunk.export(chunk_path, format="mp3")
            transcriptions.append(transcribe_audio(chunk_path))
            os.remove(chunk_path)
        return "\n".join(transcriptions)
    return ""

# Function to generate a summary from the given text
def generate_summary(text, prompt, max_tokens=100):
    input_text = f"Create a summary of the following text with {prompt}: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_text}
        ],
        max_tokens=max_tokens,
        n=1,
        temperature=0.5,
    )

    summary = response['choices'][0]['message']['content'].strip()
    return summary

# Function to generate a headline from the given text
def generate_headline(text, max_tokens=17):
    input_text = f"Create topline summary in 8 words or fewer: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_text}
        ],
        max_tokens=max_tokens,
        n=1,
        temperature=0.5,
    )

    headline = response['choices'][0]['message']['content'].strip().strip('"')  # added .strip('"') to remove quotation marks
    return headline


# Function to monitor a folder and process new files
def monitor_folder(folder_path):
    try:
        processed_files = set()
        skipped_files = set()

        # Looping infinitely to check for new files
        while True:
            for entry in os.scandir(folder_path):
                if (
                    entry.is_file()
                    and entry.name.endswith((".mp3", ".m4a", ".ogg", ".flac", ".wav"))
                    and not entry.name.startswith(".trashed")
                    and entry.name not in processed_files
                ):
                    base_name, file_extension = os.path.splitext(entry.name)
                    processed_wav_path = os.path.join(
                        folder_path, "processed", f"{base_name}.wav"
                    )

                    if os.path.exists(processed_wav_path):
                        if entry.name not in skipped_files:
                            print(f"{base_name} has already been processed. Skipping.")
                            skipped_files.add(entry.name)
                        continue

                    processed_files.add(entry.name)
                    file_path = entry.path
                    base_name, file_extension = os.path.splitext(entry.name)

                    if file_extension.lower() != ".wav":
                        file_path = convert_to_wav(file_path)
                        base_name, file_extension = os.path.splitext(os.path.basename(file_path))
                        file_path = os.path.join(folder_path, f"{base_name}.wav")

                        # Add a delay after the conversion
                        time.sleep(2)

                    # Transcribe and split the audio file if needed
                    transcript = transcribe_audio(file_path)

                    # Truncate the transcript to a certain number of tokens (e.g., 4000) to avoid exceeding the model's token limit
                    truncated_transcript = truncate_text(transcript, 4000)

                    # Print the truncated_transcript to check its content
                    print("Truncated transcript: ", truncated_transcript)

                    # Generate the summary of the recording using OpenAI from the transcript
                    summary = generate_summary(truncated_transcript, prompt="a three-bullet-point summary")

                    # Generate the headline of the recording from the transcript
                    headline = generate_headline(truncated_transcript)

                    # Save transcriptions, three-bullet-point summary, and title in the .txt files
                    os.makedirs(output_path, exist_ok=True)
                    with open(os.path.join(output_path, f"{base_name}_transcript.txt"), "w", encoding="utf-8") as f:
                        f.write(transcript)
                    with open(os.path.join(output_path, f"{base_name}_summary.txt"), "w", encoding="utf-8") as f:
                        f.write(summary)
                    with open(os.path.join(output_path, f"{base_name}_headline.txt"), "w", encoding="utf-8") as f:
                        f.write(headline)

                    print(f"Finished processing {base_name}.")

                    # Move the processed audio file to the "processed" folder
                    os.rename(file_path, os.path.join(folder_path, "processed", f"{base_name}.wav"))

            # Sleep for a while before checking the folder again
            time.sleep(10)

    except KeyboardInterrupt:
        print("Stopping the script.")

if __name__ == "__main__":
    monitor_folder(folder_path)
