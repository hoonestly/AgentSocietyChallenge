import json
import logging
import uuid
import pandas as pd
from tqdm import tqdm
import os
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REQUIRED_FILES_YELP = [
    'yelp_academic_dataset_business.json', 
    'yelp_academic_dataset_user.json', 
    'yelp_academic_dataset_review.json'
]

REQUIRED_FILES_AMAZON = [
    'Industrial_and_Scientific.csv', 
    'Musical_Instruments.csv', 
    'Video_Games.csv',
    'Industrial_and_Scientific.jsonl', 
    'Musical_Instruments.jsonl', 
    'Video_Games.jsonl',
    'meta_Industrial_and_Scientific.jsonl', 
    'meta_Musical_Instruments.jsonl', 
    'meta_Video_Games.jsonl'
]

REQUIRED_FILES_GOODREADS = [
    'goodreads_books_children.json', 
    'goodreads_reviews_children.json', 
    'goodreads_books_comics_graphic.json', 
    'goodreads_reviews_comics_graphic.json', 
    'goodreads_books_poetry.json', 
    'goodreads_reviews_poetry.json'
]

def load_data(file_path):
    """Load JSON data into a Pandas DataFrame with progress bar."""
    data = []
    with open(file_path, 'r') as file:
        for line in tqdm(file, desc=f"Loading {file_path}", unit=" lines"):
            data.append(json.loads(line))
    return pd.DataFrame(data)

def save_json(dataframe, output_file):
    """Save a Pandas DataFrame to a JSON file."""
    logging.info(f"Saving {output_file}...")
    dataframe.to_json(output_file, orient='records', lines=True)
    logging.info(f"{output_file} saved.")

def filter_data(top_cities, business_df, user_df, review_df):
    """Filter and save data within the top three cities with progress bars."""
    logging.info("Filtering data for top cities...")
    
    filtered_businesses = business_df[business_df['city'].isin(top_cities)]
    filtered_reviews = review_df[review_df['business_id'].isin(filtered_businesses['business_id'])]
    filtered_users = user_df[user_df['user_id'].isin(filtered_reviews['user_id'])]

    # Save filtered data in JSON format
    return filtered_businesses, filtered_reviews, filtered_users

def check_required_files(input_dir):
    """Check if all required Amazon files exist in the input directory."""
    missing_files = []
    
    for file in REQUIRED_FILES_AMAZON:
        if not os.path.exists(os.path.join(input_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        print("Error: Missing required files:")
        for file in missing_files:
            print(f"- {file}")
        return False
    return True

def load_and_process_yelp_data(input_dir):
    logging.info("Loading and processing Yelp data...")
    # File paths
    business_file = os.path.join(input_dir, 'yelp_academic_dataset_business.json')
    user_file = os.path.join(input_dir, 'yelp_academic_dataset_user.json')
    review_file = os.path.join(input_dir, 'yelp_academic_dataset_review.json')

    # Load the datasets with progress bars
    business_df = load_data(business_file)
    user_df = load_data(user_file)
    review_df = load_data(review_file)

    # Find top cities and related data
    logging.info("Finding top cities by reviews for Yelp...")
    top_cities = ['Philadelphia', 'Tampa', 'Tucson']

    logging.info("Filtering data for top cities for Yelp...")
    filtered_businesses, filtered_reviews, filtered_users = filter_data(top_cities, business_df, user_df, review_df)
    return filtered_businesses, filtered_reviews, filtered_users

def load_and_process_amazon_data(input_dir):
    """Load and process Amazon dataset."""
    logging.info("Loading and processing Amazon data...")
    rating_only_files = ['Industrial_and_Scientific.csv', 'Musical_Instruments.csv', 'Video_Games.csv']
    review_files = ['Industrial_and_Scientific.jsonl', 'Musical_Instruments.jsonl', 'Video_Games.jsonl']
    meta_files = ['meta_Industrial_and_Scientific.jsonl', 'meta_Musical_Instruments.jsonl', 'meta_Video_Games.jsonl']

    # Load rating-only data
    all_rating_only = pd.concat([pd.read_csv(os.path.join(input_dir, f)) for f in rating_only_files])
    users = all_rating_only['user_id'].unique().tolist()
    items = all_rating_only['parent_asin'].unique().tolist()

    # Load review data
    all_reviews = pd.DataFrame()
    for f in review_files:
        data = load_data(os.path.join(input_dir, f))
        # Filter data based on users and items from rating-only data
        data = data[data['user_id'].isin(users) & data['parent_asin'].isin(items)] 
        all_reviews = pd.concat([all_reviews, data])
    
    # Load meta data
    all_meta = pd.DataFrame()
    for f in meta_files:
        data = load_data(os.path.join(input_dir, f))
        data = data[data['parent_asin'].isin(items)]
        all_meta = pd.concat([all_meta, data])

    return all_reviews, all_meta

def load_and_process_goodreads_data(input_dir):
    """Load and process Goodreads dataset."""
    logging.info("Loading and processing Goodreads data...")
    book_files = ['goodreads_books_children.json', 'goodreads_books_comics_graphic.json', 'goodreads_books_poetry.json']
    review_files = ['goodreads_reviews_children.json', 'goodreads_reviews_comics_graphic.json', 'goodreads_reviews_poetry.json']
    
    all_books = pd.concat([load_data(os.path.join(input_dir, f)) for f in book_files])
    all_reviews = pd.concat([load_data(os.path.join(input_dir, f)) for f in review_files])
    
    return all_books, all_reviews

def merge_business_data(amazon_meta, output_file=None):
    """Merge business data from Amazon source."""
    logging.info("Processing business data...")
    
    amazon_business = amazon_meta.rename(columns={
        'parent_asin': 'item_id'
    })
    amazon_business['source'] = 'amazon'
    amazon_business['type'] = 'product'
    amazon_json = json.loads(amazon_business.to_json(orient='records'))
    
    if output_file:
        logging.info(f"Saving business data to {output_file}...")
        with open(output_file, 'w') as f:
            for item in amazon_json:
                f.write(json.dumps(item) + '\n')

def merge_review_data(amazon_reviews, output_file=None):
    """Merge review data from Amazon source."""
    logging.info("Processing review data...")
    
    amazon_reviews = amazon_reviews.rename(columns={
        'asin': 'sub_item_id',
        'parent_asin': 'item_id',
        'rating': 'stars',
    })
    amazon_reviews['review_id'] = [str(uuid.uuid4()) for _ in range(len(amazon_reviews))]
    amazon_reviews['source'] = 'amazon'
    amazon_reviews['type'] = 'product'
    amazon_json = json.loads(amazon_reviews.to_json(orient='records'))
    
    if output_file:
        logging.info(f"Saving review data to {output_file}...")
        with open(output_file, 'w') as f:
            for item in amazon_json:
                f.write(json.dumps(item) + '\n')

def create_unified_users(amazon_reviews, output_file=None):
    """Create unified user data from Amazon reviews."""
    logging.info("Processing user data...")
    
    amazon_users = pd.DataFrame({
        'user_id': amazon_reviews['user_id'].unique(),
        'source': 'amazon'
    })
    amazon_json = json.loads(amazon_users.to_json(orient='records'))
    
    if output_file:
        logging.info(f"Saving user data to {output_file}...")
        with open(output_file, 'w') as f:
            for item in amazon_json:
                f.write(json.dumps(item) + '\n')

def main():
    """Main function for Amazon data processing."""
    parser = argparse.ArgumentParser(description="Process Amazon dataset for analysis.")
    parser.add_argument('--input_dir', required=True, help="Path to the input directory containing Amazon dataset files.")
    parser.add_argument('--output_dir', required=True, help="Path to the output directory for saving processed data.")
    args = parser.parse_args()

    # Check required files
    if not check_required_files(args.input_dir):
        return

    # Process Amazon data
    amazon_reviews, amazon_meta = load_and_process_amazon_data(args.input_dir)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process and save data
    merge_business_data(amazon_meta, os.path.join(args.output_dir, 'item.json'))
    merge_review_data(amazon_reviews, os.path.join(args.output_dir, 'review.json'))
    create_unified_users(amazon_reviews, os.path.join(args.output_dir, 'user.json'))

    logging.info("Amazon data processing completed successfully.")

if __name__ == '__main__':
    main()