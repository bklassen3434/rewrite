# ReWrite

This is the readme for ReWrite

Author: Ben Klassen

## Setup

Here is how to get started using ReWrite!

1. Install Python 3.11 <https://www.python.org/downloads/>

### 1 | Server

You will need a server running in the [/server/](/server/) directory.

Windows:

1. Create a virtual environment (e.g., `py -m venv venv`)
2. Activate env (e.g., `venv\scripts\active`)
3. Install packages (e.g., `python -m pip install -r requirements.txt`)
4. Run program (e.g., `python chatgpt_api.py`)

MacOS/Linux:

1. Create a virtual environment (e.g., `python3 -m venv venv`)
2. Activate env (e.g., `source venv/bin/activate`)
3. Install packages (e.g., `python -m pip install -r requirements.txt`)
4. Run program (e.g., `python chatgpt_api.py`)

### 2 | Interface

You will serve the web files from this directory.

1. Start up a local HTTP web server
   1. For Windows: `py -m http.server 8000`
   2. For MacOS/Linux: `python3 -m http.server 8000`
2. Navigate in your web browser to [http://localhost:8000/](http://localhost:8000/)

## Credits

Author: Ben Klassen

## License

MIT
