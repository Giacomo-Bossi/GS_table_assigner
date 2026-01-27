async function createJob(file) {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = async function (event) {
        // parse CSV content
        const csvString = event.target.result;
        const gruppiData = generateGruppiJSON(csvString);
        console.log("Generated gruppi data:", gruppiData);

        // load table configuration
        const tavoliResponse = await fetch('tavoli.json');
        const tavoliData = await tavoliResponse.json();
        console.log("Loaded tavoli data:", tavoliData);

        jobCall(gruppiData, tavoliData);
    };
}

const PRESOLVER_PERC_WEIGHT = 50;
async function jobCall(gruppiData, tavoliData) {
    // presolver
    let gruppiAssegnati = [];
    let assegnamentiManuali = {};
    try {
        for (let [idx, tavolo] of tavoliData.entries()) {
            assegnamentiManuali[""+`${tavolo.table_id}`] = [];
        }
        let biggestTableCapacity = tavoliData.reduce((maxCap, t) => Math.max(maxCap, t.capacity), 0);
        let gruppiGrossi = gruppiData.filter(g => g.size > biggestTableCapacity);

        while (gruppiGrossi.length > 0) {
            console.log("Splitting group:", gruppiGrossi[0]);
            let giàAssegnatoA = [];
            let gruppo = gruppiGrossi[0];
            let gruppiNuovi = [];
            if (gruppo.required_head) {
                let biggestHeadTableCapacity = tavoliData.reduce((maxCap, t) => Math.max(maxCap, t.head_seats ? t.capacity : 0), 0);
                let nuovoGruppoTesta = {
                    name: gruppo.name + "_head",
                    show_name: gruppo.show_name,
                    size: biggestHeadTableCapacity,
                    required_head: true,
                    near_field: gruppo.near_field,
                    close_to: gruppo.close_to
                };
                gruppiNuovi.push(nuovoGruppoTesta);
                gruppo.size -= biggestHeadTableCapacity;
                gruppo.required_head = false;
                let tavolo = tavoliData.find(t => t.head_seats && t.capacity >= nuovoGruppoTesta.size);
                if (tavolo) {
                    assegnamentiManuali[`${tavolo.table_id}`].push(nuovoGruppoTesta.name);
                    giàAssegnatoA.push(tavolo.table_id);
                } else {
                    console.error("No suitable table found for head group:", nuovoGruppoTesta);
                }
                tavoliData.find(t => t.table_id === tavolo.table_id).capacity -= nuovoGruppoTesta.size; // reduce available capacity
                
                gruppiAssegnati.push(nuovoGruppoTesta);
            }


            while (gruppo.size > 0) {
                let sizeToAssign = Math.min(gruppo.size, biggestTableCapacity);
                if(gruppo.size>=14 && gruppo.size != sizeToAssign && gruppo.size - sizeToAssign < 7) {
                    sizeToAssign = Math.ceil(gruppo.size / 2);
                }
                let nuovoGruppo = {
                    name: gruppo.name + "_part" + (gruppiNuovi.length + 1),
                    show_name: gruppo.show_name,
                    size: sizeToAssign,
                    required_head: false,
                    near_field: gruppo.near_field,
                    close_to: gruppo.close_to
                };
                gruppiNuovi.push(nuovoGruppo);
                gruppo.size -= sizeToAssign;
                if(giàAssegnatoA.length > 0) {  /* sort tables by distance from the first assigned table for the group 🤯 */
                    tavoliData.sort((a,b) => {
                        let ax = a.gui.x + a.gui.width/2;
                        let ay = a.gui.y + a.gui.height/2;
                        let bx = b.gui.x + b.gui.width/2;
                        let by = b.gui.y + b.gui.height/2;
                        let refTable = tavoliData.find(t => t.table_id === giàAssegnatoA[0]);
                        let rx = refTable.gui.x + refTable.gui.width/2;
                        let ry = refTable.gui.y + refTable.gui.height/2;
                        let da = Math.sqrt((ax - rx)**2 + (ay - ry)**2);
                        let db = Math.sqrt((bx - rx)**2 + (by - ry)**2);
                        return da - db;
                    });
                }
                let tavolo = tavoliData.find(t => t.capacity >= nuovoGruppo.size);
                if (tavolo) {
                    if (giàAssegnatoA.includes(tavolo.table_id)) {
                        assegnamentiManuali[`${tavolo.table_id}`].size += nuovoGruppo.size;
                    }else{
                        assegnamentiManuali[`${tavolo.table_id}`].push(nuovoGruppo.name);
                        giàAssegnatoA.push(tavolo.table_id);
                    }
                } else {
                    console.error("No suitable table found for group part:", nuovoGruppo);
                }
                tavoliData.find(t => t.table_id === tavolo.table_id).capacity -= nuovoGruppo.size; // reduce available capacity
                biggestTableCapacity = tavoliData.reduce((maxCap, t) => Math.max(maxCap, t.capacity), 0);
                gruppiAssegnati.push(nuovoGruppo);
            }
            gruppiGrossi = gruppiData.filter(g => g.size > biggestTableCapacity);
        }
        console.log("New groups after splitting:", assegnamentiManuali);
        changeProgressBar(PRESOLVER_PERC_WEIGHT);
    } catch (e) {
        alert("Error during presolver: " + e.message);
        window.location.reload();
        return;
    }
    // external solver call
    try {
        const response = await fetch('solver/start_job', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                groups: gruppiData,
                tables: tavoliData.map(t => ({ table_id: t.table_id, capacity: t.capacity, head_seats: t.head_seats || 0, show_name: t.show_name || "" })),
                assignments: assegnamentiManuali,
                assignments_groups: gruppiAssegnati
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