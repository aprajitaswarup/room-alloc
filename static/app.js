const button = document.getElementById("allocate");
const status = document.getElementById("status");
const results = document.getElementById("results");
const output = document.getElementById("output");
const statistics = document.getElementById("statistics");

function readStudents() {
  const lines = document.getElementById("students").value
    .split("\n")
    .map(line => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const parts = line.split(",").map(part => part.trim());

    if (parts.length !== 3) {
      throw new Error(`Student line ${index + 1} needs 3 values.`);
    }

    const access = parts[2].toLowerCase();
    if (!["yes", "no"].includes(access)) {
      throw new Error(`Use yes or no for access on line ${index + 1}.`);
    }

    return {
      id: parts[0],
      group: parts[1],
      needs_access: access === "yes"
    };
  });
}

function readAccessiblePositions() {
  const text = document.getElementById("accessible").value.trim();
  if (!text) return [];

  return text.split(";").map(pair => {
    const numbers = pair.split(",").map(value => Number(value.trim()));

    if (numbers.length !== 2 || numbers.some(value => !Number.isInteger(value))) {
      throw new Error("Accessible positions should look like 1,1; 3,1.");
    }

    return numbers;
  });
}

function showChart(allocation, roomCount, rows, cols) {
  output.replaceChildren();

  for (let roomNumber = 1; roomNumber <= roomCount; roomNumber++) {
    const roomName = `Room ${roomNumber}`;
    const title = document.createElement("h3");
    title.textContent = roomName;
    output.appendChild(title);

    const table = document.createElement("table");

    for (let row = 1; row <= rows; row++) {
      const tr = document.createElement("tr");

      for (let col = 1; col <= cols; col++) {
        const td = document.createElement("td");
        const seat = allocation.find(item =>
          item.room === roomName && item.row === row && item.col === col
        );

        if (seat) {
          td.textContent = `${seat.student_id}\nGroup ${seat.group}`;
        } else {
          td.textContent = "Empty";
        }

        const accessiblePosition = readAccessiblePositions()
          .some(([r, c]) => r === row && c === col);

        if (accessiblePosition) {
          td.classList.add("accessible");
          td.title = "Accessible seat";
        }

        tr.appendChild(td);
      }

      table.appendChild(tr);
    }

    output.appendChild(table);
  }
}

function showStatistics(stats) {
    statistics.replaceChildren();
  
    const items = [
      ["Total students", stats.total_students],
      ["Allocated in valid plan", stats.allocated_students],
      ["Still unallocated", stats.remaining_students],
      ["Seat capacity", stats.seat_capacity],
      ["Empty seats", stats.empty_seats ?? "—"],
      ["Rooms used", stats.rooms_used],
      ["Accessibility needs", stats.students_needing_access],
      ["Accessible students seated", stats.accessible_students_seated],
      ["Accessible seats", stats.accessible_seats]
    ];
  
    for (const [label, value] of items) {
      const card = document.createElement("div");
      card.className = "stat-box";
  
      const heading = document.createElement("span");
      heading.textContent = label;
  
      const number = document.createElement("strong");
      number.textContent = value;
  
      card.append(heading, number);
      statistics.appendChild(card);
    }
  }

button.addEventListener("click", async () => {
  status.textContent = "Working…";
  results.classList.remove("hidden");
  output.replaceChildren();

  try {
    const payload = {
      students: readStudents(),
      room_count: Number(document.getElementById("room-count").value),
      rows: Number(document.getElementById("rows").value),
      cols: Number(document.getElementById("cols").value),
      accessible_positions: readAccessiblePositions()
    };

    const response = await fetch("/api/allocate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (data.statistics) {
        showStatistics(data.statistics);
      }

    if (!response.ok) {
      throw new Error(data.detail || "The request could not be processed.");
    }

    if (!data.ok) {
      status.textContent = "No valid allocation found.";
      data.conflicts.forEach(message => {
        const item = document.createElement("p");
        item.className = "conflict";
        item.textContent = message;
        output.appendChild(item);
      });
      return;
    }

    status.textContent = data.message;
    showChart(
      data.allocation,
      payload.room_count,
      payload.rows,
      payload.cols
    );
  } catch (error) {
    status.textContent = error.message;
  }
});