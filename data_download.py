import os
import requests
from tqdm import tqdm

# List of URLs to download
urls = [
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Industrial_and_Scientific.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/meta_categories/meta_Industrial_and_Scientific.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/benchmark/5core/rating_only/Industrial_and_Scientific.csv.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Musical_Instruments.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/meta_categories/meta_Musical_Instruments.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/benchmark/5core/rating_only/Musical_Instruments.csv.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/review_categories/Video_Games.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/raw/meta_categories/meta_Video_Games.jsonl.gz',
    'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/benchmark/5core/rating_only/Video_Games.csv.gz'
]

# Ensure the dataset directory exists
os.makedirs('dataset', exist_ok=True)

# Function to download a file with progress bar
def download_file(url, output_dir):
    local_filename = os.path.join(output_dir, url.split('/')[-1])
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(local_filename, 'wb') as file, tqdm(
            desc=local_filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                bar.update(len(chunk))
    return local_filename

# Download each file
for url in urls:
    print(f"Downloading {url}")
    try:
        download_file(url, 'dataset')
        print(f"Downloaded successfully: {url}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
