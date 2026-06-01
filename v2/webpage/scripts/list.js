$(document).ready(function() {
    fetch('solver/jobs')
        .then(response => response.json())
        .then(data => {
            const jobsList = $('#tableBody');
            
            for (const [idx, jobId] of data.jobs.entries()){  
                jobsList.append(`<tr id="${jobId}" class="jobRow">
                    <td>${data.jobs.length - idx}</td>
                    <td ></td>
                    <td><i class="ri-loader-2-line jobIcon execJob"></i></td>
                    <td><button onclick="document.location.href='solver/download/${jobId}/placeholders'"><i class="ri-file-paper-2-fill" ></i></button><button onclick="document.location.href='solver/download/${jobId}/map'"><i class="ri-treasure-map-line" ></i></button></td>
                </tr>`);
                
                const updateJobStatus = () => {
                    fetch(`solver/status/${jobId}`)
                        .then(response => response.json())
                        .then(statusData => {
                            
                            const assignedAll = statusData.result && statusData.result["total assignable"] ==  statusData.result["total guests"];
                            const hasWarnings = statusData.result && statusData.result["warnings"] && statusData.result["warnings"].length > 0;
                            console.log(statusData);

                            // Update the status column based on the fetched status
                            const statusCell = $(`#${jobId} td:nth-child(3)`);
                            const numsCell = $(`#${jobId} td:nth-child(2)`);
                            const btnsCell = $(`#${jobId} td:nth-child(4)`);
                            if (statusData.status === "COMPLETED") {
                                if(assignedAll && !hasWarnings){
                                    statusCell.html('<i class="ri-file-check-line jobIcon doneJob"></i>');
                                    numsCell.html(`${statusData.result["total assignable"]} / ${statusData.result["total guests"]}`);
                                    numsCell.addClass("ok");
                                } else if(assignedAll && hasWarnings){
                                    statusCell.html('<i class="ri-file-warning-line jobIcon warnJob"></i>');
                                    numsCell.html(`${statusData.result["total assignable"]} / ${statusData.result["total guests"]}`);
                                    numsCell.addClass("warn");
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
                                numsCell.html(`<p>${statusData.status}</p>`);
                                statusCell.html(`<i class="ri-error-warning-line jobIcon err"></i>`);
                            }


                            if(hasWarnings){
                                btnsCell.append('<button onclick="document.location.href=\'job.html?job_id=' + jobId + '\'"><i class="ri-feedback-line" ></i></button>');
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