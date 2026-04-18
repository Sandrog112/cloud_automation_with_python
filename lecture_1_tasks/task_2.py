import argparse
import re


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    args = parser.parse_args()

    text = args.text
    floatList = [float(value) for value in re.findall(r"\d+\.\d+", text)]

    masked_text = re.sub(r"\d+\.\d+", " ", text)
    integers = [int(value) for value in re.findall(r"\d+", masked_text)]
    oddList = [value for value in integers if value % 2 == 1]
    evenList = [value for value in integers if value % 2 == 0]

    print(f"floatList = {floatList}")
    print(f"oddList = {oddList}")
    print(f"evenList = {evenList}")


if __name__ == "__main__":
    main()
