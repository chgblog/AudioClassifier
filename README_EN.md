# Audio Classifier

This is a tool that uses Google Gemini API to analyze and classify audio files.

[中文文档](README.md) | English

## Features

- Scans all supported audio files in the specified directory and its subdirectories
- Analyzes each audio file's content using Gemini AI
- Generates content descriptions, usage scenarios, and tags for each audio file
- Saves analysis results to an Excel file
- Supports API request limit handling with automatic waiting and retry

## Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- FLAC (.flac)
- AAC (.aac)
- OGG (.ogg)

## Installation

You can install all dependencies at once using the following command:

```bash
pip install -r requirements.txt
```

Or manually install each dependency:

```bash
pip install pandas google-generativeai tqdm openpyxl
```

## Usage

```bash
python audio_classifier.py --directory "AUDIO_DIRECTORY" --api_key "YOUR_GEMINI_API_KEY" [--output "OUTPUT_FILE_PATH"] [--max_retries RETRY_COUNT] [--retry_delay WAIT_SECONDS] [--proxy "PROXY_SERVER_ADDRESS"] [--model "MODEL_NAME"]
```

### Parameters

- `--directory`, `-d`: Audio file directory path (required)
- `--api_key`, `-k`: Gemini API key (required)
- `--output`, `-o`: Output Excel file path (optional, defaults to audio_classification_results.xlsx in the current directory)
- `--max_retries`, `-r`: Maximum number of retries when API requests fail (optional, defaults to 60)
- `--retry_delay`, `-t`: Wait time in seconds before retrying after an API request failure (optional, defaults to 60)
- `--category_dir`, `-c`: Directory for storing categorized audio files (optional, defaults to "分类音频" folder in the current directory)
- `--proxy`, `-p`: HTTP/HTTPS proxy server address (optional, format: http://127.0.0.1:7890)
- `--model`, `-m`: Gemini model name to use (optional, defaults to gemini-2.0-flash-001)

### Proxy Settings

If you need to use a proxy to access the Gemini API, you can specify the proxy server address using the `--proxy` parameter. The proxy address format should be a complete URL, including the protocol (http or https), hostname, and port number, for example:

```bash
python audio_classifier.py --directory "AUDIO_DIRECTORY" --api_key "YOUR_GEMINI_API_KEY" --proxy "http://127.0.0.1:7890"
```

This setting will apply to both HTTP and HTTPS requests.

## Output File

The program will generate an Excel file at the specified output path (or default path) containing the following information:

- Audio file path
- Categorized path (new location of the audio file after categorization)
- Main category (primary category extracted from tags)
- Audio content description
- Usage scenario suggestions
- Tag list
- Failure reason (if any)

**Note**: If an absolute path for the output file is not specified, the Excel file will be saved in the current working directory. The complete path of the output file will be displayed in the console after the program finishes running.

## Error Handling

- When API requests exceed quota limits, the program will automatically wait for the specified time before retrying
- If it still fails after retrying, it will continue to wait and retry until successful or until the maximum number of retries is reached
- All errors and warnings are logged in the `audio_classifier.log` file