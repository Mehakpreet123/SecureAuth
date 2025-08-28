FILES = []  # In-memory store

def save_file_metadata(filename):
    FILES.append(filename)

def get_all_files():
    return FILES
