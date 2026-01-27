$(document).ready(function() {
    fetch('solver/jobs')
        .then(response => response.json())
        .then(data => {
            const jobsList = $('#tableBody');
            for (const [idx, jobId] of data.jobs.entries()){
                jobsList.append(`<tr id="${jobId}">
                    <td>${idx + 1}</td>
                    <td ></td>
                    <td><i class="ri-loader-2-line jobIcon execJob"></i></td>
                    <td><button disabled><i class="ri-eye-line"></i></button><button disabled><i class="ri-delete-bin-line"></i></button></td>
                </tr>`);
                
                const updateJobStatus = () => {
                    fetch(`solver/status/${jobId}`)
                        .then(response => response.json())
                        .then(statusData => {
                            
                                console.log(statusData);
                            // Update the status column based on the fetched status
                            const statusCell = $(`#${jobId} td:nth-child(3)`);
                            const numsCell = $(`#${jobId} td:nth-child(2)`);
                            if (statusData.status === "COMPLETED") {
                                if(statusData.result && statusData.result["total assignable"] ==  statusData.result["total guests"] ){
                                    statusCell.html('<i class="ri-file-check-line jobIcon doneJob"></i>');
                                    numsCell.html(`${statusData.result["total assignable"]} / ${statusData.result["total guests"]}`);
                                    numsCell.addClass("ok");
                                } else {
                                    statusCell.html('<i class="ri-file-warning-line jobIcon failJob"></i>');
                                    numsCell.html(`${statusData.result["total assignable"]} / ${statusData.result["total guests"]}`);
                                    numsCell.addClass("err");
                                }

                                clearInterval(jobUpdater);
                            } else if (statusData.status === "PROCESSING") {
                                statusCell.html('<i class="ri-loader-2-line jobIcon execJob"></i>');
                            } else if (statusData.status === "PROGRESS") {
                                numsCell.html(`${statusData.meta.current} / ${statusData.meta.total}`);
                            } else {
                                statusCell.html(`<i class="ri-error-warning-line jobIcon err"></i> ${statusData.status}`);
                            }
                        })
                        .catch(error => console.error(`Error fetching status for job ${jobId}:`, error));
                };
                
                updateJobStatus();
                let jobUpdater = setInterval(updateJobStatus, 2000);
            }
        })
        .catch(error => console.error('Error fetching jobs:', error));


});