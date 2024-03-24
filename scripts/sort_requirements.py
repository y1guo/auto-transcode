# sort_requirements.py
def sort_requirements():
    with open("requirements.txt", "r") as file:
        # Sort lines in a case-insensitive manner, ignoring empty lines
        lines = sorted((line.strip() for line in file if line.strip()), key=str.lower)

    with open("requirements.txt", "w") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sort_requirements()
