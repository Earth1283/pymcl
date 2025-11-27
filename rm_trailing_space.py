import glob

def clean_file(filepath):
    """
    Removes trailing whitespace from each line of a file.

    This function reads a file, processes its content to remove any trailing spaces
    or tabs from each line, and then overwrites the original file with the cleaned
    content. It only performs the write operation if changes are necessary.
    """
    try:
        # Read the original content, preserving newline characters
        with open(filepath, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # If the file is empty, there's nothing to do
        if not original_content:
            print(f"⚪ Skipping empty file: {filepath}")
            return

        # Create a new version of the content with trailing spaces removed
        lines = original_content.splitlines()
        stripped_lines = [line.rstrip() for line in lines]
        cleaned_content = '\n'.join(stripped_lines)

        # Add a final newline if the original file had one, which is common
        if original_content.endswith(('\n', '\r\n')):
            cleaned_content += '\n'

        # Only write back to the disk if the content has actually changed
        if cleaned_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(cleaned_content)
            print(f"✅ Cleaned: {filepath}")
        else:
            print(f"⚪ No changes needed: {filepath}")

    except UnicodeDecodeError:
        print(f"⚠️  Skipping non-UTF-8 file: {filepath}")
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")


def main():
    """
    Main function to find and process all Python files recursively.
    """
    # Use glob to find all .py files recursively from the current directory
    # The '**' pattern with recursive=True matches files in the current
    # dir and all subdirs.
    search_pattern = '**/*.py'
    python_files = glob.glob(search_pattern, recursive=True)

    if not python_files:
        print("🤷 No Python (.py) files found.")
        return

    if len(python_files) == 1:
        print("Found 1 Python file. Starting cleanup...\n")
    else:
        print(f"Found {len(python_files)} Python file(s). Starting cleanup...\n")

    for filepath in python_files:
        clean_file(filepath)
    print("\n✨ Cleanup complete! Pylint should be happy!")

if __name__ == "__main__":
    main()
