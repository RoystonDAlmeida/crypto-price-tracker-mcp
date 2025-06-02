# Crypto Price Tracker MCP Server

A Python-based server application that allows users to track cryptocurrency prices, manage a watchlist, and export data to Google Sheets. This server is built using the FastMCP framework and is designed to be run as a containerized application using Docker.

## Table of Contents

- [Crypto Price Tracker MCP Server](#crypto-price-tracker-mcp-server)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Technology Stack](#technology-stack)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [1. Clone the Repository](#1-clone-the-repository)
    - [2. Create and Activate a Python Virtual Environment](#2-create-and-activate-a-python-virtual-environment)
    - [3. Install Dependencies](#3-install-dependencies)
    - [4. Obtain Google Sheets API Credentials](#4-obtain-google-sheets-api-credentials)
    - [5. Build the Docker Image](#5-build-the-docker-image)
    - [6. Run the Docker Container](#6-run-the-docker-container)
      - [Direct Docker Usage](#direct-docker-usage)
      - [Configuration Parameters](#configuration-parameters)
      - [MCP Client Integration (GitHub Copilot)](#mcp-client-integration-github-copilot)
      - [Prerequisites](#prerequisites-1)
      - [Settings Configuration](#settings-configuration)
  - [How It Works](#how-it-works)
  - [Configuration](#configuration)
  - [Usage](#usage)
    - [Available Tools](#available-tools)
      - [Using Prompt Generation Tools](#using-prompt-generation-tools)
  - [Data Persistence](#data-persistence)
  - [Contributing](#contributing)
  - [License](#license)

## Features

*   **Watchlist Management:**
    *   Add cryptocurrencies to a personal watchlist.
    *   Remove cryptocurrencies from the watchlist.
    *   View the current watchlist.
*   **Price Tracking:**
    *   Fetch the latest prices for all coins in the watchlist (Using CoinGecko API).
*   **Google Sheets Integration:**
    *   Export watchlist and price data to a Google Sheet.
    *   Share the Google Sheet with a specified user.
    *   Analyze performance (highest gain/loss) from data in a Google Sheet.
*   **MCP Interaction:**
    *   Provides tools and prompts for interaction via the MCP (Model Context Protocol) over stdio.

## Technology Stack

*   **Python 3.12+**
*   **Docker:** For containerization.
*   **FastMCP (`mcp[cli]`):** Framework for building the server and its tools.
*   **uv:** For Python package management within the Docker build.
*   **httpx:** For making HTTP requests to the cryptocurrency API.
*   **Google API Client Libraries:** For interacting with Google Sheets.
    *   `google-api-python-client`
    *   `google-auth`
    *   `google-auth-oauthlib`
    *   `google-auth-httplib2`

## Prerequisites
*   **Docker:** Must be installed and running. Install Docker
*   **Google Cloud Project & Service Account:** Required for Google Sheets integration.
    *   A Google Cloud Platform project.
    *   Google Sheets API enabled for the project.
    *   A Service Account with permissions to edit Google Sheets.
    *   A JSON key file for the Service Account (referred to as `google_credentials.json`).

## Installation

### 1. Clone the Repository

First, clone this repository to your local machine:
```bash
git clone git@github.com:RoystonDAlmeida/crypto-price-tracker-mcp.git
cd crypto-price-tracker-mcp/
```

### 2. Create and Activate a Python Virtual Environment

It's highly recommended to use a virtual environment to isolate project dependencies. This project requires Python 3.12+.

```bash
# Navigate to your project directory if you aren't already there
# cd crypto-price-tracker-mcp/

# Create a virtual environment (e.g., named .venv)
python3.12 -m venv .venv

# Activate the virtual environment:
# On macOS and Linux:
source .venv/bin/activate
# On Windows (Git Bash or WSL):
# source .venv/Scripts/activate
# On Windows (Command Prompt):
# .venv\Scripts\activate.bat
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

Once activated, your shell prompt should indicate the active environment (e.g., `(.venv)`).

### 3. Install Dependencies

This project uses `uv` for Python package management (as specified in the "Technology Stack" and used in the `Dockerfile`), and dependencies are defined in `pyproject.toml`. Ensure your virtual environment is activated and you are in the project root directory, then run:

```bash
# Ensure uv is installed (e.g., pip install uv, or follow uv's installation guide)
# Then, install the project in editable mode with its dependencies:
uv pip install -e .
```
This will install the `crypto-price-tracker-mcp` package and its required libraries into your virtual environment.

### 4. Obtain Google Sheets API Credentials

1.  Go to the Google Cloud Console.
2.  Create a new project or select an existing one.
3.  Enable the "Google Sheets API" for your project.
4.  Create a Service Account:
   *   Navigate to "IAM & Admin" > "Service Accounts".
   *   Click "Create Service Account".
   *   Give it a name (e.g., "crypto-sheets-editor").
   *   Click "Done".
5.  Create a JSON key for the Service Account:
   *   Find your newly created service account in the list.
   *   Click on the three dots (Actions) next to it and select "Manage keys".
   *   Click "Add Key" > "Create new key".
   *   Select "JSON" as the key type and click "Create".
   *   A JSON file will be downloaded. **Rename this file to `google_credentials.json`**. Add this file to the root of the project folder.

### 5. Build the Docker Image

Navigate to the project's root directory (where the `Dockerfile` is located) in the virtual env and run:

```bash
docker build -t crypto-price-tracker .
```

### 6. Run the Docker Container

To run the server, you need to mount your google_credentials.json file into the container.

#### Direct Docker Usage

```bash
docker run -it --rm \
  -v /path/to/your/local/google_credentials.json:/app/google_credentials.json \
  crypto-price-tracker
```
Replace /path/to/your/local/google_credentials.json with the actual absolute path to your google_credentials.json file on your host machine.

#### Configuration Parameters

`-it`: Runs the container in interactive mode with a TTY, necessary for stdio communication
`--rm`: Automatically removes the container when it exits
`-v ...`: Mounts your local credentials file to /app/google_credentials.json inside the container, where the application expects it by default

#### MCP Client Integration (GitHub Copilot)

Since we'll be interacting with this MCP containerized server via prompts typed in an MCP client (GitHub Copilot), add the following configuration to your settings.json(Open User Settings file) in VSCode:

```json
{
    "mcpServers": {
        "crypto-price-tracker": {
            "command": "docker",
            "args": [
                "run",
                "--rm",
                "-i",
                "-v",
                "<local_path>/google_credentials.json:/app/google_credentials.json",
                "-e",
                "GOOGLE_CREDENTIALS_PATH=/app/google_credentials.json",
                "crypto-price-tracker-mcp"
            ]
        }
    }
}
```

Start Github Copilot in `Agent` mode and it will start the server specified in `settings.json`. Verify the console output for successful discovery of tools.

#### Prerequisites

Make sure to build the Docker image with the correct tag first:

```bash
docker build -t crypto-price-tracker-mcp .
```

#### Settings Configuration

**Important Notes:**

*   Replace `<local_path>` with the actual absolute path to your `google_credentials.json` file on your host machine.
*   The `-i` flag (instead of `-it`) is generally used for MCP client integration as it typically only requires standard input (stdin), not a full TTY.
*   The environment variable `GOOGLE_CREDENTIALS_PATH` is explicitly set in the example to ensure the application inside the container knows where to find the credentials file.
*   **Communication Method:** The server communicates over stdio (standard input/standard output), making it compatible with MCP clients like GitHub Copilot for seamless integration.

## How It Works

The server communicates over stdio (standard input/standard output), making it compatible with MCP clients like GitHub Copilot. This allows you to interact with the containerized MCP server through natural language prompts, while the server handles crypto price tracking and Google Sheets integration in the background.

Replace `/path/to/your/local/google_credentials.json` with the actual absolute path to your `google_credentials.json` file on your host machine.

*   `-it`: Runs the container in interactive mode with a TTY, necessary for stdio communication.
*   `--rm`: Automatically removes the container when it exits.
*   `-v ...`: Mounts your local credentials file to `/app/google_credentials.json` inside the container, where the application expects it by default.

The server communicates over **stdio** (standard input/standard output). You can interact with it using the MCP client(Github Copilot).

## Configuration

*   **Google Credentials:**
    *   The application looks for Google Sheets API credentials at `/app/google_credentials.json` inside the container by default.
    *   This path can be overridden by setting the `GOOGLE_CREDENTIALS_PATH` environment variable when running the container (e.g., `-e GOOGLE_CREDENTIALS_PATH=/custom/path/creds.json`).

## Usage

The server operates using the MCP protocol over stdio. After starting the container, it will be ready to accept MCP requests.

### Available Tools

The server exposes several tools that can be invoked:

*   **`get_watchlist`**: Get the current watchlist of tracked cryptocurrencies.
*   **`add_to_watchlist(id: str)`**: Add a cryptocurrency (e.g., "bitcoin") to the watchlist.
*   **`remove_from_watchlist(id: str)`**: Remove a cryptocurrency from the watchlist.
*   **`fetch_prices`**: Fetch the latest prices for all coins in the watchlist.
*   **`export_to_sheets(sheet_name: str, user_email: str)`**: Export all tracked price data to a Google Sheet with the given `sheet_name` and share it with `user_email`.
*   **`get_sheet_performance_leaders(sheet_name: str)`**: Identifies cryptocurrencies with the highest gain and highest loss from a specified Google Sheet based on the 'Change_24h' column.

#### Using Prompt Generation Tools

To assist MCP clients (like GitHub Copilot) in formulating requests or suggesting actions to the user, the server also provides several "prompt generation" tools. These tools, when called, return natural language strings. Here’s an overview of these tools, the prompts they generate, and their purpose:

*   **`get_watchlist_prompt()`**
    *   **Generated Prompt (Response Returned)**: `"Please fetch the watchlist."`
    *   **Tool Invoked (upon confirmation)**: `get_watchlist`
    *   **Purpose**: Suggests or initiates retrieval and display of the user's current watchlist.

*   **`add_coin_prompt(coin_id: str)`**
    *   **Example Input**: `coin_id="ethereum"`
    *   **Generated Prompt (Response Returned)**: `"Please add ETHEREUM to my watchlist."`
    *   **Tool Invoked (upon confirmation)**: `add_to_watchlist` (with the specified `coin_id`)
    *   **Purpose**: Helps formulate a request to add a specific cryptocurrency to the watchlist.

*   **`remove_coin_prompt(coin_id: str)`**
    *   **Example Input**: `coin_id="bitcoin"`
    *   **Generated Prompt (Response Returned)**: `"Please remove bitcoin from my watchlist."`
    *   **Tool Invoked (upon confirmation)**: `remove_from_watchlist` (with the specified `coin_id`)
    *   **Purpose**: Assists in creating a request to remove a specific cryptocurrency from the watchlist.

*   **`get_prices_prompt()`**
    *   **Generated Prompt (Response Returned)**: `"Please fetch the latest prices for all cryptocurrencies in my watchlist."`
    *   **Tool Invoked (upon confirmation)**: `fetch_prices`
    *   **Purpose**: Initiates a request to update and display current market prices for all coins in the watchlist.

*   **`export_prompt(sheet_name: str, user_email: str)`**
    *   **Example Inputs**: `sheet_name="Crypto Portfolio"`, `user_email="analyst@example.com"`
    *   **Generated Prompt (Response Returned)**: `"Please export all tracked price data to my Google Sheet 'Crypto Portfolio' and share it with analyst@example.com."`
    *   **Tool Invoked (upon confirmation)**: `export_to_sheets` (with `sheet_name` and `user_email`)
    *   **Purpose**: Facilitates requests for exporting watchlist and price data to a Google Sheet and sharing it.

*   **`get_sheet_performance_leaders_prompt(sheet_name: str)`**
    *   **Example Input**: `sheet_name="Crypto Analysis"`
    *   **Generated Prompt (Response Returned)**: `"From the Google Sheet named 'Crypto Analysis', can you tell me which crypto had the highest gain and which one had the biggest loss recently?"`
    *   **Tool Invoked (upon confirmation)**: `get_sheet_performance_leaders` (with `sheet_name`)
    *   **Purpose**: Helps in requesting performance analysis (highest gain/loss) from a specified Google Sheet.

An MCP client would typically use these generated prompts to guide the user or to directly formulate a call to one of the main action tools (like `add_to_watchlist(id: str)`, `get_watchlist()`, etc.) after user confirmation.

## Data Persistence

*   **`watchlist.json`**:
    *   The user's watchlist is stored in a file named `watchlist.json`.
    *   Inside the Docker container, this file will be created at `/app/watchlist.json`.

## Contributing

Contributions are welcome and greatly appreciated! If you'd like to contribute to the project, please follow these general steps:

1.  **Fork the Repository:**
    Start by forking the main repository to your own GitHub account.

2.  **Clone Your Fork:**
    Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/crypto-price-tracker-mcp.git
    cd crypto-price-tracker-mcp
    ```

3.  **Set Up Your Development Environment:**
    Follow the [Installation](#installation) steps to set up your local development environment, including creating a virtual environment and installing dependencies.

4.  **Create a New Branch:**
    Create a new branch for your feature or bug fix. Use a descriptive name (e.g., `feature/add-new-exchange` or `fix/price-fetch-error`).
    ```bash
    git checkout -b your-branch-name
    ```

5.  **Make Your Changes:**
    Implement your feature or fix the bug. Ensure your code adheres to the project's coding style and conventions.

6.  **Test Your Changes:**
    (If applicable) Add or update tests for your changes and ensure all tests pass.

7.  **Commit Your Changes:**
    Commit your changes with a clear and concise commit message.
    ```bash
    git add .
    git commit -m "feat: Describe your feature or fix"
    ```
    (Consider using Conventional Commits for commit messages.)

8.  **Push to Your Fork:**
    Push your changes to your forked repository on GitHub.
    ```bash
    git push origin your-branch-name
    ```

9.  **Open a Pull Request (PR):**
    Go to the original repository on GitHub and open a Pull Request from your forked branch to the main repository's `main` (or `master`) branch. Provide a clear description of your changes in the PR.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).