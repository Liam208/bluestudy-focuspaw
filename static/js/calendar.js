let currentDisplayDate = new Date();
const calendarGrid = document.getElementById("calendarGrid");
const monthYearTitle = document.getElementById("currentMonthYear");

const todayStr = new Date().toISOString().split("T")[0];

const tasksByDate = {};

TASKS.forEach((task) => {
  const date = task.due_date;
  if (!tasksByDate[date]) {
    tasksByDate[date] = [];
  }

  // Check if overdue: date is before today AND status is not Completed
  const isOverdue = date < todayStr && task.status !== "Completed";

  tasksByDate[date].push({
    title: task.subject,
    prio: (task.priority || "med").toLowerCase(),
    overdue: isOverdue,
  });
});

function renderCalendar() {
  calendarGrid.innerHTML = "";
  const year = currentDisplayDate.getFullYear();
  const month = currentDisplayDate.getMonth();

  monthYearTitle.innerText = new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
  }).format(currentDisplayDate);

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const prevMonthLastDay = new Date(year, month, 0).getDate();

  // Days from previous month
  for (let i = firstDay; i > 0; i--) {
    createDayElement(prevMonthLastDay - i + 1, true);
  }

  // Days of current month
  const today = new Date();
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday =
      today.getDate() === day &&
      today.getMonth() === month &&
      today.getFullYear() === year;
    createDayElement(
      day,
      false,
      isToday,
      `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(
        2,
        "0"
      )}`
    );
  }

  // Fill remaining slots for 6-row grid if needed
  const totalSlots = 42;
  const filledSlots = firstDay + daysInMonth;
  for (let i = 1; i <= totalSlots - filledSlots; i++) {
    createDayElement(i, true);
  }
}

function createDayElement(day, isOtherMonth, isToday, dateStr) {
  const div = document.createElement("div");
  div.className = `calendar-day ${isOtherMonth ? "other-month" : ""} ${
    isToday ? "today" : ""
  }`;

  const numSpan = document.createElement("span");
  numSpan.className = "font-bold text-sm";
  numSpan.innerText = day;
  div.appendChild(numSpan);

  // Add tasks
  if (dateStr && tasksByDate[dateStr]) {
    // Limit to 3 tasks on mobile to prevent overflow, show more on desktop
    const maxTasks = window.innerWidth < 768 ? 2 : 4;
    const tasks = tasksByDate[dateStr];

    tasks.forEach((task, index) => {
      if (index < maxTasks) {
        const tDiv = document.createElement("div");
        if (task.overdue) {
          tDiv.className =
            "task-indicator bg-red-600 text-white border-none flex items-center gap-1";
          tDiv.innerHTML = `<i class="fas fa-exclamation-circle text-[8px]"></i> <span class="truncate">${task.title}</span>`;
        } else {
          tDiv.className = `task-indicator truncate ${
            task.prio === "high" ? "indicator-high" : "indicator-med"
          }`;
          tDiv.innerText = task.title;
        }
        div.appendChild(tDiv);
      } else if (index === maxTasks) {
        // Show "+X more" label
        const moreDiv = document.createElement("div");
        moreDiv.className =
          "text-[9px] text-slate-500 mt-1 font-medium text-center";
        moreDiv.innerText = `+${tasks.length - maxTasks} more`;
        div.appendChild(moreDiv);
      }
    });
  }

  calendarGrid.appendChild(div);
}

function changeMonth(dir) {
  currentDisplayDate.setMonth(currentDisplayDate.getMonth() + dir);
  renderCalendar();
}

function goToToday() {
  currentDisplayDate = new Date();
  renderCalendar();
}

// --- AI Sidebar Logic (Reusing your provided functionality) ---

window.onload = renderCalendar;
function toggleSettings() {
  const menu = document.getElementById("dropdownMenu");
  const icon = document.getElementById("settingsIcon");

  menu.classList.toggle("show");
  icon.classList.toggle("rotate-gear");

  // Close dropdown when clicking anywhere else
  const closeMenu = (e) => {
    if (!document.getElementById("settingsDropdown").contains(e.target)) {
      menu.classList.remove("show");
      icon.classList.remove("rotate-gear");
      document.removeEventListener("click", closeMenu);
    }
  };

  // Delay adding the event listener to prevent immediate closing
  setTimeout(() => {
    document.addEventListener("click", closeMenu);
  }, 10);
}
