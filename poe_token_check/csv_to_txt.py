import csv
import os

# Set the input and output file names
input_file = 'chat.csv'
output_file = 'token_to_test.txt'

# Open the input and output files
with open(input_file, 'r') as csv_file, open(output_file, 'w') as txt_file:
    # Create a CSV reader object
    reader = csv.DictReader(csv_file)

    # Iterate over the rows in the CSV file
    for row in reader:
        # Get the value of the Content column
        content = row['Content']

        # Write the content to the output file
        txt_file.write(content + '\n')

# Delete the input CSV file
os.remove(input_file)
