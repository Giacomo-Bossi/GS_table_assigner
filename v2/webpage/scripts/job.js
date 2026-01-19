const job_id = getJobId();
const UPDATE_INTERVAL = 2000; // in milliseconds

let updater = setInterval(fetchJobStatus, UPDATE_INTERVAL);

window.onload = function() {
    fetchJobStatus();
};


function fetchJobStatus() {
    let status = fetch(`http://localhost:5000/status/${job_id}`);
    status.then(response => response.json())
        .then(data => {
            console.log("Job status:", data);
            document.getElementById("jobProgressText").textContent = data.status;
            if (data.status === "COMPLETED") {
                clearInterval(updater);
                document.getElementById("jobStatusText").textContent = "Completato!";
                document.querySelector(".loader-job").remove();
                document.querySelectorAll(".lo_sp").forEach(el => el.remove());
                let result = data.result;
                document.getElementById("jobProgressText").textContent = `Assegnati: ${result["total assignable"]} / ${result["total guests"]} (${result["total seats"]} posti)`;
                let area = document.querySelector(".drag-area");

                let showButton = document.createElement("button");
                showButton.innerHTML = "<i class=\"ri-eye-line\"></i>";
                showButton.onclick = function() {
                    window.location.href = `render.html?job_id=${job_id}`;
                };
                area.appendChild(document.createElement("br"));
                area.appendChild(showButton);
                

            } else if (data.status === "PROCESSING") {

            } else if (data.status === "PROGRESS") {
                let progress = data.meta;
                document.getElementById("jobProgressText").textContent = `Assegnati: ${progress.current} / ${progress.total}`;
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