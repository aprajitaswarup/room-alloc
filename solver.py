#this file contains the CSP-- students are the variables to assign, 
#seats are their possible domains, and the constrains decide which choices are allowed.
def side_by_side(a, b):
    return (
        a["room"] == b["room"]
        and a["row"] == b["row"]
        and abs(a["col"] - b["col"]) == 1
    )

def solve(students, seats, enforce_groups=True, enforce_access=True):
    assigned = {}

    def legal_seats(student):
        options = []

        for seat in seats:
#a seat can only be used once
            if any(s["id"] == seat["id"] for s in assigned.values()):
                continue

#students needing accessibility can only use accessible seats
            if enforce_access and student["needs_access"] and not seat["accessible"]:
                continue

#same grp students cannot sit immediately beside each other.
            conflict = False
            if enforce_groups:
                for other in students:
                    if other["id"] in assigned:
                        if student["group"] == other["group"]:
                            if side_by_side(seat, assigned[other["id"]]):
                                conflict = True
                                break

            if not conflict:
                options.append(seat)

#prioritise ordinary seats for students who dont need accessible seating
        options.sort(key=lambda seat: seat["accessible"])
        return options

    def backtrack():
        if len(assigned) == len(students):
            return True

        remaining = [s for s in students if s["id"] not in assigned]

#min remaining values-- choose the student with fewest seat options
        student = min(
            remaining,
            key=lambda s: (
                len(legal_seats(s)),
                not s["needs_access"]
            )
        )

        for seat in legal_seats(student):
            assigned[student["id"]] = seat

#fwd checking-- stop if a remaining student has no legal seat
            future_students = [
                s for s in remaining if s["id"] != student["id"]
            ]

            if all(legal_seats(s) for s in future_students):
                if backtrack():
                    return True

#choice led to a dead end... undo it and try another seat.
            del assigned[student["id"]]

        return False

    if backtrack():
        return assigned
    return None


def explain_failure(students, seats):
    if len(students) > len(seats):
        return ["There are more students than available seats."]

    students_needing_access = sum(
        student["needs_access"] for student in students
    )
    available_access_seats = sum(
        seat["accessible"] for seat in seats
    )

    if students_needing_access > available_access_seats:
        return [
            "More students need accessible seats than there are "
            "accessible seats."
        ]

    group_relaxed = solve(students, seats, enforce_groups=False)
    access_relaxed = solve(students, seats, enforce_access=False)

    reasons = []

    if group_relaxed is not None:
        reasons.append(
            "A solution exists if the same-group adjacency rule is relaxed."
        )

    if access_relaxed is not None:
        reasons.append(
            "A solution exists if the accessible-seat restriction is relaxed."
        )

    both_relaxed = solve(
        students,
        seats,
        enforce_groups=False,
        enforce_access=False
    )

    if (both_relaxed is not None
            and group_relaxed is None
            and access_relaxed is None):
        reasons.append(
            "The group-separation and accessibility rules conflict when "
            "applied together."
        )

    if not reasons:
        reasons.append(
            "No solution found. The rules may conflict in combination."
        )
    return reasons

#backtracking means-- try a seat, continue assigning, and go back to try a different seat if you get stuck
#fwd checking catches some dead ends early... “min remaining values” rule tries the most restricted student first.