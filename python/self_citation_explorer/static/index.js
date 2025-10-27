// Set up the progress bars
const evtSource = new EventSource("/stream");

evtSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const task = data.task || "";
  const progress = Math.floor(data.progress || 0);

  // Determine current page / container
  let progressBarId, progressLabelId;

  document.getElementById("progress-bar").style.width = progress + "%";
  document.getElementById("progress-label").innerText = task ? `${task}: ${progress}%` : "";
};


// Inactivate the buttons and search tabs while the data is being retrieved via the APi.
document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("button[name='button']");

    buttons.forEach(btn => {
        btn.addEventListener("click", (event) => {
            const clicked = event.currentTarget;

            // Disable all other form buttons immediately
            buttons.forEach(b => {
                if (b !== clicked) b.disabled = true;
            });

            // Leave clicked button enabled long enough for the browser to include its value in the POST
            setTimeout(() => { clicked.disabled = true; }, 100); // 50ms is usually enough

        });
    });
});