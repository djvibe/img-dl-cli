```
  _______  _______  __   __  _______
 |   _   ||       ||  | |  ||       |
 |  |_|  ||    ___||  |_|  ||    ___|
 |       ||   |___ |       ||   |___
 |       ||    ___||       ||    ___|
 |   _   ||   |___  |   |  ||   |___
 |__| |__||_______|  |___|  ||_______|
   ______   _______  __   __  ___
  |      | |       ||  | |  ||   |
  |  _    ||   _   ||  |_|  ||   |
  | | |   ||  | |  ||       ||   |
  | |_|   ||  |_|  ||       ||   |___
  |       ||       | |     | |       |
  |______| |_______|  |___|  |_______|
```

# img-dl: Google Image Downloader

A simple command-line tool to download high-resolution images from Google Images.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd mcp-image-downloader
    ```

2.  **Install dependencies:**
    It's highly recommended to use a virtual environment.

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Make the script executable:**
    (This step might have already been done by git)
    ```bash
    chmod +x img-dl
    ```

## Usage

The primary way to use this tool is via the `img-dl` executable script.

```bash
./img-dl <query> [options]
```

### Positional Arguments

*   `query`: The search term for the images you want to download. If your query contains spaces, wrap it in quotes (e.g., `"cute cats"`).

### Optional Arguments

| Flag          | Alias | Description                               | Default   | Choices                                 |
|---------------|-------|-------------------------------------------|-----------|-----------------------------------------|
| `--num`       | `-n`  | The number of images to download.         | `5`       | Any integer                             |
| `--size`      | `-s`  | The minimum image file size in kilobytes (KB). | `180`     | Any integer                             |
| `--type`      | `-t`  | The type of image to filter for.          | `photo`   | `all`, `photo`, `clipart`, `lineart`, `gif` |
| `--output`    | `-o`  | The directory where images will be saved. | `images`  | Any valid path                          |
| `--logs`      | `-l`  | The directory where log files will be stored. | `logs`    | Any valid path                          |
| `--help`      | `-h`  | Show the help message and exit.           |           |                                         |

### Examples

**Basic Download**

Download 5 photos of "dogs":

```bash
./img-dl "dogs"
```

**Download More Images**

Download 20 photos of "landscapes":

```bash
./img-dl "landscapes" -n 20
```

**Specify Image Type and Size**

Download 10 clipart images of "computers" with a minimum size of 50KB:

```bash
./img-dl "computers" -n 10 -t clipart -s 50
```

**Custom Output Directory**

Download images to a specific folder named `~/Pictures/cat_pics`:

```bash
./img-dl "cats" -o ~/Pictures/cat_pics
```
