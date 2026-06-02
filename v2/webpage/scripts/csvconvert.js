async function createJob(file) {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = async function (event) {
        // parse CSV content
        const csvString = event.target.result;
        const gruppiData = generateGruppiJSON(csvString);
        console.log("Generated gruppi data:", gruppiData);

        // load table configuration
        const tavoliResponse = await fetch('tavoli_FDS.json');
        const tavoliData = (await tavoliResponse.json()).tables;
        console.log("Loaded tavoli data:", tavoliData);

        jobCall(gruppiData, tavoliData);
    };
}

async function jobCall(gruppiData, tavoliData) {
    // external solver call
    try {
        const payload = JSON.stringify({
            groups: gruppiData,
            tables: tavoliData
        });

        changeProgressBar(5);
        const response = await postJsonWithProgress('solver/start_job', payload, changeProgressBar);
        const result = await response.json();
        if (!response.ok) {
            alert("Error creating job: " + result.message);
            return;
        }

        const jobId = result.task_id;
        console.log("Job id:", jobId);

        changeProgressBar(100);
        window.location.href = "job.html?job_id=" + jobId;
    } catch (e) {
        alert("Error during job creation: " + e.message);
        window.location.reload();
        return;
    }

}

function postJsonWithProgress(url, payload, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        let lastPercent = -1;

        const report = (percent) => {
            const clamped = Math.max(0, Math.min(100, percent));
            if (clamped !== lastPercent) {
                lastPercent = clamped;
                onProgress(clamped);
            }
        };

        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                report(Math.round((event.loaded / event.total) * 80));
            }
        };

        xhr.onprogress = (event) => {
            if (event.lengthComputable) {
                report(80 + Math.round((event.loaded / event.total) * 20));
            }
        };

        xhr.onload = () => {
            report(100);
            resolve({
                ok: xhr.status >= 200 && xhr.status < 300,
                status: xhr.status,
                json: () => Promise.resolve().then(() => {
                    if (!xhr.responseText) {
                        return {};
                    }
                    return JSON.parse(xhr.responseText);
                })
            });
        };

        xhr.onerror = () => reject(new Error('Network error'));

        xhr.send(payload);
        report(10);
    });
}



function generateGruppiJSON(csvString) {
    // Normalize line endings
    csvString = csvString.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // Split into lines and filter empty ones
    const lines = csvString.split('\n').filter(line => line.trim() !== '');

    if (lines.length === 0) {
        return [];
    }

    // Parse header row
    let start = 0
    if (lines[0].startsWith("ID;GIORNO;NOME;POSTI;NOTE;CAPO")) {
        //const headers = lines[0].split(';').map(header => header.trim());
        start = 1; // skip header
    }

    // Parse data rows
    const data = [];
    for (let i = start; i < lines.length; i++) {
        const values = lines[i].split(';').map(value => value.trim());
        console.log("Parsing line:", values.length, "values");
        if (values.length < 6) {
            console.log("Skipping invalid row:", lines[i]);
            continue; // Skip invalid row
        }

        let groupObj = {
            name: values[0], // id del gruppo (unico)
            show_name: values[2], // nome visualizzato
            size: parseInt(values[3], 10), // dimensione del gruppo
            real_size: parseInt(values[3], 10), // dimensione del gruppo, da non toccare nel solver (usata per display)
            required_head: values[5].toLowerCase() === 'vero' || values[5].toLowerCase() === 'true', // il gruppo richiede un posto capotavola
            near_field: values.length > 7 && (values[7].toLowerCase() === 'vero' || values[7].toLowerCase() === 'true'), // il gruppo richiede un posto vicino al campo
        };

        if (values.length > 6 && values[6].trim() !== "") {
            let closeToValue = values[6].trim();
            // Handle multiple IDs if necessary, or just string
            groupObj.close_to = closeToValue;
        }
        data.push(groupObj);
    }
    console.log("Parsed groups data:", data);
    return data;
}