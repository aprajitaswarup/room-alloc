from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from solver import solve, explain_failure


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Room Allocation System")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/allocate")
def allocate(payload: dict):
    try:
        students = payload["students"]
        room_count = int(payload["room_count"])
        rows = int(payload["rows"])
        cols = int(payload["cols"])
        accessible_positions = payload["accessible_positions"]

        if not students:
            raise ValueError("Enter at least one student.")

        if room_count < 1 or rows < 1 or cols < 1:
            raise ValueError("Rooms, rows, and columns must be at least 1.")

        if room_count > 5 or rows > 20 or cols > 20:
            raise ValueError("For this demo, use at most 5 rooms and 20 rows "
                             "or columns.")

        student_ids = [student["id"] for student in students]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError("Each student must have a unique ID.")

        for row, col in accessible_positions:
            if row < 1 or row > rows or col < 1 or col > cols:
                raise ValueError(
                    f"Accessible seat ({row}, {col}) is outside the room."
                )

        seats = []
        for room_number in range(1, room_count + 1):
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    seats.append({
                        "id": f"R{room_number}-r{row}c{col}",
                        "room": f"Room {room_number}",
                        "row": row,
                        "col": col,
                        "accessible": [row, col] in accessible_positions
                    })

    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    allocation = solve(students, seats)

    if allocation is None:
        return {
            "ok": False,
            "conflicts": explain_failure(students, seats)
        }

    results = []
    for student in students:
        seat = allocation[student["id"]]
        results.append({
            "student_id": student["id"],
            "group": student["group"],
            "needs_access": student["needs_access"],
            "room": seat["room"],
            "row": seat["row"],
            "col": seat["col"],
            "accessible": seat["accessible"]
        })

    # Independent validation of the completed allocation.
    problems = []

    if len(results) != len(students):
        problems.append("Not every student received a seat.")

    if len({item["room"] + str(item["row"]) + str(item["col"])
            for item in results}) != len(results):
        problems.append("A seat was assigned more than once.")

    for item in results:
        if item["needs_access"] and not item["accessible"]:
            problems.append(
                f"{item['student_id']} was not given an accessible seat."
            )

    for i, first in enumerate(results):
        for second in results[i + 1:]:
            same_group = first["group"] == second["group"]
            side_by_side = (
                first["room"] == second["room"]
                and first["row"] == second["row"]
                and abs(first["col"] - second["col"]) == 1
            )
            if same_group and side_by_side:
                problems.append(
                    f"{first['student_id']} and {second['student_id']} "
                    "from the same group are side by side."
                )

    if problems:
        return {"ok": False, "conflicts": problems}

    return {
        "ok": True,
        "allocation": results,
        "message": "Allocation found and validated."
    }