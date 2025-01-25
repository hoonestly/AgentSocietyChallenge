import os
import gzip

# Directory containing the downloaded .gz files
input_dir = 'dataset'

# Function to unzip a single .gz file
def unzip_file(gz_file, output_dir):
    output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(gz_file))[0])
    with gzip.open(gz_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"Unzipped: {gz_file} -> {output_file}")
    return output_file

# Process all .gz files in the directory
for filename in os.listdir(input_dir):
    if filename.endswith('.gz'):
        gz_file_path = os.path.join(input_dir, filename)
        try:
            unzip_file(gz_file_path, input_dir)
            os.remove(gz_file_path)  # Optional: Delete the original .gz file after extraction
        except Exception as e:
            print(f"Failed to unzip {gz_file_path}: {e}")
