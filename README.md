# PeopleBot

PeopleBot is an open-source project built in Python, utilizing the power of large language models (LLMs) like GPT-3.5-turbo, face recognition, and speech recognition to create an interactive chatbot that can communicate with people, remember their faces, and continue conversations from where they left off. The goal of this project is to learn as much as possible about the people it interacts with and be a good friend.

## Features

- Face recognition to identify and remember individuals
- Utilizes ChatGPT API for generating human-like responses
- Speech recognition to transcribe spoken input
- SQLite3 to store conversation data and face recognition data
- Easily extensible and customizable

## Installation

To install PeopleBot, please follow these steps:

1. Clone this repository to your local machine:
  ```
  git clone https://github.com/yourusername/peoplebot.git
  ```
  
2. Change to the cloned directory:
  ```
  cd peoplebot
  ```
  
3. Set up a virtual environment (optional, but recommended):

  ```
  python3 -m venv venv
  source venv/bin/activate
  ```


4. Install the required packages:

  ```
  pip install -r requirements.txt
  ```


5. Set up an OpenAI API key:

- Obtain an API key from [OpenAI](https://beta.openai.com/signup/).
- Set the API key as an environment variable:
  ```
  export OPENAI_API_KEY="your_api_key_here"
  ```

## Usage

To run PeopleBot, execute the following command:
```
python people_bot.py
```


The chatbot will start processing video from your webcam, detecting faces, and initiating conversations. When it recognizes a face, it will either start a new conversation or continue a previous one, depending on whether it has encountered the person before.

Please ensure your webcam and microphone are connected and working correctly for the best user experience.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please feel free to create an issue or submit a pull request.

## License

PeopleBot is released under the MIT License.

