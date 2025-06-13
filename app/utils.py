
def load_file_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        return "File not found."
    except IOError:
        return "An error occurred while reading the file."