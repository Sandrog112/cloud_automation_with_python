import argparse


def is_armstrong(number: int) -> bool:
    digits = str(number)
    power = len(digits)
    return number == sum(int(digit) ** power for digit in digits)


def recursive_sum(values: list[int], index: int = 0) -> int:
    if index >= len(values):
        return 0
    return values[index] + recursive_sum(values, index + 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=9)
    parser.add_argument("--end", type=int, default=9999)
    args = parser.parse_args()

    armstrong_numbers = [
        number for number in range(args.start, args.end + 1) if is_armstrong(number)
    ]
    total = recursive_sum(armstrong_numbers)

    print(f"Armstrong numbers: {armstrong_numbers}")
    print(f"Total sum: {total}")


if __name__ == "__main__":
    main()
