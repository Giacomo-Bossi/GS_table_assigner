async function createJob(file) {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = async function(event) {
        // parse CSV content
        const csvString = event.target.result;
        const gruppiData = generateGruppiJSON(csvString);
        console.log("Generated gruppi data:", gruppiData);

        // load table configuration
        const tavoliResponse = await fetch('/v2/tavoli.json');
        const tavoliData = await tavoliResponse.json();
        console.log("Loaded tavoli data:", tavoliData);
        
        jobCall(gruppiData, tavoliData);
    };
}

const PRESOLVER_PERC_WEIGHT = 50;
async function jobCall(gruppiData, tavoliData) {
    // presolver
    try {
        
        /* [EMPTY] */ 


    
        changeProgressBar(PRESOLVER_PERC_WEIGHT);
    } catch (e) {
        alert("Error during presolver: " + e.message);
        window.location.reload();
        return;
    }
    // external solver call
    try {
        const response = await fetch('http://localhost:5000/start_job', { // [TODO] replace with actual solver URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                groups: gruppiData,
                tables: tavoliData.map(t => ({table_id: t.table_id, capacity: t.capacity, head_seats: t.head_seats || 0, show_name: t.show_name || ""}))
            })
        });
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
    if(lines[0].startsWith("ID;GIORNO;NOME;POSTI;NOTE;CAPO")){ 
        //const headers = lines[0].split(';').map(header => header.trim());
        start = 1; // skip header
    }

    // Parse data rows
    const data = [];
    for (let i = start; i < lines.length; i++) {
        const values = lines[i].split(';').map(value => value.trim());
        console.log("Parsing line:", values.length, "values");
        if(values.length < 6) {
            console.log("Skipping invalid row:", lines[i]);
            continue; // Skip invalid row
        }

        data.push({
            name: values[0], // id del gruppo (unico)
            show_name: values[2], // nome visualizzato
            size: parseInt(values[3], 10), // dimensione del gruppo
            required_head: values[5].toLowerCase() === 'vero' || values[5].toLowerCase() === 'true', // il gruppo richiede un posto capotavola
            near_field: false, // [FUTURE] for future use, richiesto tavolo con vista campo
            close_to: []  // [FUTURE] for future use, richiesto vicino a (lista di id di altri gruppi, soft requirement) 
        });
    }
    
    return data;
}