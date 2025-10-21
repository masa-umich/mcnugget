# Define the directory you want to open
TARGET_DIR="Desktop/mcnugget/mcnugget/autosequences"

# Loop through each line in the file
while IFS= read -r command; do
    # Check if the line is not empty or a comment
    if [[ ! -z "$command" && ! "$command" =~ ^# ]]; then
        # Open a new terminal and run the command
        # For macOS, use 'osascript' to open a new Terminal window
        osascript -e "tell application \"Terminal\" to do script \"cd $TARGET_DIR && poetry run $command\""
    fi
done < input.txt