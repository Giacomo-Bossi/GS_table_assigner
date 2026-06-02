const job_id = getJobId();
const UPDATE_INTERVAL = 2000; // in milliseconds

let updater = setInterval(fetchJobStatus, UPDATE_INTERVAL);

window.onload = function () {
    fetchJobStatus();
};


function fetchJobStatus() {
    let status = fetch(`solver/status/${job_id}`);
    status.then(response => response.json())
        .then(data => {
            console.log("Job status:", data);
            document.getElementById("jobProgressText").textContent = data.status;
            if (data.status === "COMPLETED") {
                clearInterval(updater);
                const assignedAll = data.result && data.result["total assignable"] == data.result["total guests"];
                const hasWarnings = data.result && data.result["warnings"] && data.result["warnings"].length > 0;
                if (hasWarnings) {
                    document.getElementById("jobStatusText").textContent = "Completato con avvisi!";
                    document.getElementById("jobStatusText").classList.add("warnJob");
                } else {
                    document.getElementById("jobStatusText").textContent = "Completato!";
                }
                document.querySelector(".loader-job").remove();
                document.querySelectorAll(".lo_sp").forEach(el => el.remove());
                let result = data.result;
                document.getElementById("jobProgressText").innerHTML = `Assegnati: <span class="seatNumLabel">${result["total assignable"]} / ${result["total guests"]}</span> (${result["total seats"]} posti)`;
                if (result["total assignable"] < result["total guests"]) {
                    $(".seatNumLabel").css("color", "darkred");
                }
                let area = document.querySelector(".drag-area");

                let dlPlaceholdersBtn = document.createElement("button");
                dlPlaceholdersBtn.innerHTML = `<i class="ri-file-paper-2-fill"></i>`;
                dlPlaceholdersBtn.onclick = function () {
                    window.location.href = `solver/download/${job_id}/placeholders`;
                };

                let dlMapBtn = document.createElement("button");
                dlMapBtn.innerHTML = `<i class="ri-treasure-map-line"></i>`;
                dlMapBtn.onclick = function () {
                    window.location.href = `solver/download/${job_id}/map`;
                };

                let buttonsContainer = document.createElement("div");
                buttonsContainer.style.display = "flex";
                buttonsContainer.style.flexDirection = "row";
                buttonsContainer.style.gap = "10px";
                buttonsContainer.appendChild(dlPlaceholdersBtn);
                buttonsContainer.appendChild(dlMapBtn);

                area.appendChild(document.createElement("br"));
                area.appendChild(buttonsContainer);

                if (hasWarnings) {
                    let warningsTable = $('<table class="warningTable"></table>');
                    warningsTable.append('<thead><tr><th><h2>Elenco avvisi:</h2></th></tr></thead>');
                    let warningsBody = $('<tbody></tbody>');
                    data.result.warnings.forEach(warning => {
                        warningsBody.append(`<tr><td>${warning}</td></tr>`);
                    });
                    warningsTable.append(warningsBody);
                    $(area).append(warningsTable);
                }

            } else if (data.status === "PROCESSING") {

            } else if (data.status === "PROGRESS") {
                let progress = data.meta;
                document.getElementById("jobProgressText").textContent = `Assegnati: ${progress.current} / ${progress.total}`;
            } else if (data.status === "FAILURE") {
                clearInterval(updater);
                document.getElementById("jobStatusText").textContent = "Errore durante l'elaborazione.";
                document.querySelector(".loader-job").remove();
                document.querySelectorAll(".lo_sp").forEach(el => el.remove());
            }


        })
        .catch(error => {
            console.error("Error fetching job status:", error);
        });

}













function getJobId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('job_id');
}