```
_____ ____  ____  _____ _     _____   _  _      ____  _____ _____ 
/  __//  _ \/  _ \/  __// \   /  __/  / \/ \__/|/  _ \/  __//  __/ 
| |  _| / \|| / \|| |  _| |   |  \    | || |\/||| / \|| |  _|  \   
| |_//| \_/|| \_/|| |_//| |_/\|  /_   | || |  ||| |-||| |_//|  /_  
\____\\____/\____/\____\\____/\____\  \_/\_/  \|\_/ \|\____\\____\ 
                                                                   
 ____  ____  _      _      _     ____  ____  ____  _____ ____    _ 
/  _ \/  _ \/ \  /|/ \  /|/ \   /  _ \/  _ \/  _ \/  __//  __\  / \
| | \|| / \|| |  ||| |\ ||| |   | / \|| / \|| | \||  \  |  \/|  | |
| |_/|| \_/|| |/\||| | \||| |_/\| \_/|| |-||| |_/|| _/|| /_ |    /  \_/
\____/\____/\_/  \|\_/  \|\____/\____/\_/ \|\____/\____\\_/\_\  (_)
```

# img-dl: Resilient Web Image Downloader

A command-line tool that tries Google Images first and automatically falls back
to Bing Images when Google redirects the server browser to an automated-traffic
challenge or produces no qualifying files.

The command now exits non-zero when neither source produces an image above the
requested minimum size. A zero-file run is never reported as success.

Bing fallback cards must share a meaningful query term in their title, source
page, or image URL. This rejects unrelated ads and stale cards before download.
Each downloaded image also gets an adjacent `.json` manifest containing its
query, source engine, original image URL, source page, title, and timestamp so
editorial provenance can be checked before use.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd mcp-image-downloader
    ```

2.  **Global Installation (Recommended for CLI usage):**
    Ensure you have `pipx` installed. If not, you can usually install it with `pip install pipx --user` (though this might vary based on your system Python configuration).

    Once `pipx` is available, install `img-dl-cli` from the cloned repository:
    ```bash
    pipx install .
    ```
    This will install `img-dl-cli` into an isolated environment and make the `img-dl` command globally available.

3.  **Development Installation (Optional):**
    For developing the tool or if you prefer a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

## Usage

The primary way to use this tool is via the `img-dl` executable script.

```bash
img-dl <query> [options]
```

### Positional Arguments

*   `query`: The search term for the images you want to download. If your query contains spaces, wrap it in quotes (e.g., `"cute cats"`).

### Optional Arguments

*   `-n, --num`: The number of images to download. (Default: `5`)
*   `-s, --size`: The minimum image file size in kilobytes (KB). (Default: `180`)
*   `-t, --type`: The type of image to filter for. (Default: `photo`). Choices: `all`, `photo`, `clipart`, `lineart`, `gif`.
*   `-o, --output`: The directory where images will be saved. (Default: `images`)
*   `-l, --logs`: The directory where log files will be stored. (Default: `logs`)
*   `-h, --help`: Show the help message and exit.

### Examples

**Basic Download**

Download 5 photos of "dogs". This is the default number of images.

```bash
img-dl "dogs"
```

**Download More Images**

Download 20 photos of "landscapes":

```bash
img-dl "landscapes" -n 20
```

**Specify Image Type and Size**

Download 10 clipart images of "computers" with a minimum size of 50KB:

```bash
img-dl "computers" -n 10 -t clipart -s 50
```

**Custom Output Directory**

Download images to a specific folder named `~/Pictures/cat_pics`:

```bash
img-dl "cats" -o ~/Pictures/cat_pics
```
