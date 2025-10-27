const evtSource = new EventSource("/stream");

evtSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const task = data.task || "";
  const progress = Math.floor(data.progress || 0);

  // Update bar width
  document.getElementById("progress-bar").style.width = progress + "%";

  // Update label (task + progress)
  const label = task ? `${task}: ${progress}%` : "";
  document.getElementById("progress-label").innerText = label;
};


document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("button[name='button']");

    buttons.forEach(btn => {
        btn.addEventListener("click", (event) => {
            const clicked = event.currentTarget;

            // Disable all other buttons immediately
            buttons.forEach(b => {
                if (b !== clicked) b.disabled = true;
            });

            // Let the clicked button remain enabled just long enough for the form to send its value
            setTimeout(() => {
                clicked.disabled = true;
            }, 50); // 50ms is usually enough
        });
    });
});