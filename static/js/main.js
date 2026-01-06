const aiSendBtn = document.getElementById("aiSendBtn");
const aiResponseArea = document.getElementById("aiResponseArea");
// --- PRIORITY SELECTOR ---
function setPrio(val) {
  document.getElementById("priorityInput").value = val;
  const btns = document.querySelectorAll(".prio-btn");
  btns.forEach((btn) => {
    btn.classList.remove("active");
    if (btn.innerText === val) btn.classList.add("active");
  });
}

// --- DATE PICKER ---
const dateBtn = document.querySelector(".button-test");
const editDateBtn = document.querySelector("#editModal .button-test");
const editDateInput = document.querySelector("#editModal input[type='date']");

if (editDateBtn && editDateInput) {
  editDateBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    editDateInput.showPicker(); // shows the date picker for this specific input
  });
}
if (dateBtn) {
  dateBtn.addEventListener("click", () => {
    document.querySelector('input[type="date"]').showPicker();
  });
}

function toggleAI(e) {
  if (e) e.stopPropagation();
  const modal = document.getElementById("aiModal");
  modal.classList.toggle("modal-active");
}

window.addEventListener("click", (e) => {
  const modal = document.getElementById("aiModal");
  const panel = modal.querySelector(".ai-panel");
  if (modal.classList.contains("modal-active") && !panel.contains(e.target)) {
    toggleAI();
  }
});
const aiInput = document.getElementById("aiInput");

aiInput.addEventListener("input", () => {
  aiInput.style.height = "auto"; // reset height
  aiInput.style.height = aiInput.scrollHeight + "px"; // grow to fit content
});
aiSendBtn.addEventListener("click", async () => {
  const prompt = aiInput.value.trim();
  if (!prompt) return;

  const userWrapper = document.createElement("div");
  userWrapper.className = "flex justify-end";

  const userBubble = document.createElement("div");
  userBubble.className =
    "bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[80%] text-sm leading-relaxed";
  userBubble.textContent = prompt;

  userWrapper.appendChild(userBubble);
  aiResponseArea.appendChild(userWrapper);

  aiInput.value = "";
  aiInput.style.height = "auto"; // <--- add this line to reset height
  aiResponseArea.scrollTop = aiResponseArea.scrollHeight;

  try {
    const res = await fetch("/ask_ai", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `prompt=${encodeURIComponent(prompt)}`,
    });
    const data = await res.json();

    const aiWrapper = document.createElement("div");
    aiWrapper.className = "flex justify-start";

    const aiBubble = document.createElement("div");
    aiBubble.className =
      "bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 px-4 py-3 rounded-2xl rounded-bl-md max-w-[80%] text-sm leading-relaxed";

    aiBubble.innerHTML = marked.parse(data.response);

    aiWrapper.appendChild(aiBubble);
    aiResponseArea.appendChild(aiWrapper);
    renderMathInElement(aiBubble, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
    });
    aiResponseArea.scrollTop = aiResponseArea.scrollHeight;
  } catch (err) {
    console.error(err);
    const errorMsg = document.createElement("div");
    errorMsg.className =
      "bg-red-50 dark:bg-red-900/50 p-4 rounded-2xl border border-red-100 dark:border-red-900/30 text-sm";
    errorMsg.textContent = "Error contacting AI.";
    aiResponseArea.appendChild(errorMsg);
  }
});
aiInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    aiSendBtn.click();
    e.preventDefault();
  }
});

function toggleAddTask() {
  const content = document.getElementById("addTaskContent");
  const icon = document.getElementById("toggleIcon");

  if (content.style.maxHeight === "0px") {
    // Expand
    content.style.maxHeight = "1000px";
    content.style.opacity = "1";
    icon.style.transform = "rotate(0deg)";
  } else {
    // Retract
    content.style.maxHeight = "0px";
    content.style.opacity = "0";
    icon.style.transform = "rotate(180deg)";
  }
}
function openEditModal(id, subject, description, date, priority) {
  const modal = document.getElementById("editModal");
  const form = document.getElementById("editForm");
  modal.querySelector(".card").onclick = (e) => e.stopPropagation();

  form.action = `/edit/${id}`;

  // Populate fields
  document.getElementById("editSubject").value = subject;
  document.getElementById("editDescription").value = description;
  document.getElementById("editDate").value = date;
  document.getElementById("editPriority").value = priority;

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeEditModal() {
  const modal = document.getElementById("editModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}
// --- Delete Confirmation Logic ---
function confirmDelete(taskId) {
  const modal = document.getElementById("deleteModal");
  const confirmBtn = document.getElementById("confirmDeleteBtn");

  // Set the link to the backend delete route
  confirmBtn.href = `/delete/${taskId}`;

  // Show the modal
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeDeleteModal() {
  const modal = document.getElementById("deleteModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

// Close modal if clicking outside the box
window.onclick = function (event) {
  const deleteModal = document.getElementById("deleteModal");
  const editModal = document.getElementById("editModal");
  if (event.target == deleteModal) closeDeleteModal();
  if (event.target == editModal) closeEditModal();
};
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
document.querySelectorAll("#dropdownMenu a").forEach((link) => {
  link.addEventListener("click", () => {
    document.getElementById("dropdownMenu").classList.remove("show");
    document.getElementById("settingsIcon").classList.remove("rotate-gear");
  });
});
