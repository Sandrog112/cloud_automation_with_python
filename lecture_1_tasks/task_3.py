import argparse

data = {
    1: [
        {"seat_name": "a1", "isTaken": True},
        {"seat_name": "a2", "isTaken": False},
        {"seat_name": "a3", "isTaken": True},
        {"seat_name": "a4", "isTaken": True},
        {"seat_name": "a5", "isTaken": False},
    ],
    2: [
        {"seat_name": "b1", "isTaken": False},
        {"seat_name": "b2", "isTaken": False},
        {"seat_name": "b3", "isTaken": True},
        {"seat_name": "b4", "isTaken": False},
        {"seat_name": "b5", "isTaken": True},
    ],
    3: [
        {"seat_name": "c1", "isTaken": False},
        {"seat_name": "c2", "isTaken": True},
        {"seat_name": "c3", "isTaken": True},
        {"seat_name": "c4", "isTaken": True},
        {"seat_name": "c5", "isTaken": False},
    ],
}


def find_first_available(carriage: list[dict]) -> dict | None:
    for seat in carriage:
        if not seat["isTaken"]:
            return seat
    return None


def find_nearest_available(carriage: list[dict], seat_index: int) -> dict | None:
    available = [
        (abs(index - seat_index), index, seat)
        for index, seat in enumerate(carriage)
        if not seat["isTaken"]
    ]
    if not available:
        return None
    return min(available, key=lambda item: (item[0], item[1]))[2]


def reserve(carriage_number: int, seat_name: str) -> str:
    if carriage_number not in data:
        for other_number in sorted(data):
            seat = find_first_available(data[other_number])
            if seat is not None:
                seat["isTaken"] = True
                return (
                    f"Carriage {carriage_number} not found. "
                    f"Reserved seat {seat['seat_name']} in carriage {other_number}."
                )
        return "No available seats in any carriage."

    carriage = data[carriage_number]
    requested_index = next(
        (index for index, seat in enumerate(carriage) if seat["seat_name"] == seat_name),
        None,
    )

    if requested_index is None:
        seat = find_first_available(carriage)
        if seat is not None:
            seat["isTaken"] = True
            return (
                f"Seat {seat_name} does not exist in carriage {carriage_number}. "
                f"Reserved seat {seat['seat_name']} in the same carriage."
            )
    else:
        requested_seat = carriage[requested_index]
        if not requested_seat["isTaken"]:
            requested_seat["isTaken"] = True
            return f"Seat {seat_name} in carriage {carriage_number} reserved successfully."

        nearest = find_nearest_available(carriage, requested_index)
        if nearest is not None:
            nearest["isTaken"] = True
            return (
                f"Seat {seat_name} is taken. "
                f"Reserved nearest available seat {nearest['seat_name']} in carriage {carriage_number}."
            )

    for other_number in sorted(data):
        if other_number == carriage_number:
            continue
        seat = find_first_available(data[other_number])
        if seat is not None:
            seat["isTaken"] = True
            return (
                f"No available seats in carriage {carriage_number}. "
                f"Reserved seat {seat['seat_name']} in carriage {other_number}."
            )
    return "No available seats in any carriage."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("carriage", type=int)
    parser.add_argument("seat")
    args = parser.parse_args()

    print(reserve(args.carriage, args.seat.lower()))


if __name__ == "__main__":
    main()
