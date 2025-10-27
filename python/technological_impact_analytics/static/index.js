// Set up the progress bars
const evtSource = new EventSource("/stream");

evtSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const task = data.task || "";
  const progress = Math.floor(data.progress || 0);

  // Determine current page / container
  let progressBarId, progressLabelId;
  switch (window.location.pathname) {
    case "/trends":
      progressBarId = "progress-bar-trends";
      progressLabelId = "progress-label-trends";
      break;
    case "/dii":
      progressBarId = "progress-bar-dii";
      progressLabelId = "progress-label-dii";
      break;
    default:
      progressBarId = "progress-bar";
      progressLabelId = "progress-label";
  }

  document.getElementById(progressBarId).style.width = progress + "%";
  document.getElementById(progressLabelId).innerText = task ? `${task}: ${progress}%` : "";
};


// Inactivate the buttons and search tabs while the data is being retrieved via the APi.
document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("button[name='button']");
    const tabs = document.querySelectorAll(".search-tab-link");

    buttons.forEach(btn => {
        btn.addEventListener("click", (event) => {
            const clicked = event.currentTarget;

            // Disable all other form buttons immediately
            buttons.forEach(b => {
                if (b !== clicked) b.disabled = true;
            });

            // Disable tabs
            tabs.forEach(tab => {
                tab.classList.add("tab--disabled");
            });

            // Leave clicked button enabled long enough for the browser to include its value in the POST
            setTimeout(() => { clicked.disabled = true; }, 100); // 50ms is usually enough

        });
    });
});