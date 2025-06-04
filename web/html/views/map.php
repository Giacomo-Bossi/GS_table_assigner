<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
	header('Location: /login?r');
	exit;
}
?>
<?php
    echo "<h1>Map</h1>";

    $planimetria = '[
    { "id": 0, "x": 50, "y": 50, "width": 75, "height": 200, "posti": [4, 0, 4, 1] },
    { "id": 1, "x": 220, "y": 50, "width": 75, "height": 200, "posti": [4, 0, 4, 1] },
    { "id": 2, "x": 390, "y": 50, "width": 75, "height": 200, "posti": [4, 0, 4, 1] },
    { "id": 3, "x": 560, "y": 50, "width": 75, "height": 200, "posti": [4, 0, 4, 1] },
    { "id": 4, "x": 50, "y": 350, "width": 75, "height": 600, "posti": [12, 1, 12, 0] },
    { "id": 5, "x": 220, "y": 350, "width": 75, "height": 600, "posti": [12, 1, 12, 0] },
    { "id": 6, "x": 390, "y": 350, "width": 75, "height": 600, "posti": [12, 1, 12, 0] },
    { "id": 7, "x": 560, "y": 350, "width": 75, "height": 600, "posti": [12, 1, 12, 0] },
    { "id": 8, "x": 730, "y": 350, "width": 75, "height": 600, "posti": [12, 1, 12, 0] }
]';
    $plan = json_decode($planimetria, true);
    $tables = [];
    foreach ($plan as $table) {
        $posti = $table['posti'];
        $totposti = 0;
        foreach ($posti as $p) {
            $totposti += $p;
        }


        // Add the table to the tables array
        array_push($tables, [
            'table_id' => (int)$table['id'],
            'capacity' => (int)$totposti,
            'head_seats' => (int)$posti[1]+(int)$posti[3]
        ]);
    }

    $groups = [];
    require_once __ROOT__ . '/functions/db_conn.php';
    $stmt = $conn->prepare("SELECT * FROM Prenotazione WHERE idevento = ?");
    $stmt->bind_param("i", $_GET['id']);
    $stmt->execute();
    $result = $stmt->get_result();
    if ($result->num_rows > 0) {
        while ($row = $result->fetch_assoc()) {
            $groups[] = [
                'name' => $row['id'],
                'size' => (int)$row['persone'],
                'required_head' => (int)$row['capotavola'],
            ];
        }
    } else {
        echo "Nessun gruppo trovato.";
        exit;
    }


    $input = [
        'tables' => $tables,
        'groups' => $groups
    ];
    $json_input = json_encode($input);
    //print($json_input);
    $url = 'http://localhost:8081';

    $options = array(
        'http' => array(
            'method'  => 'POST',
            'header'  => 'Content-type: application/json',
            'content' => $json_input,
        )
    );
    
    $context  = stream_context_create($options);
    
    $result = file_get_contents($url, false, $context);
    if ($result === FALSE) {
        echo "Error calling the optimization service.";
        exit;
    } 
    echo "<h2>Optimization Result:</h2>";
    
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canvas Table Layout</title>
    <style>
        body,
        html {
            margin: 0;
            padding: 0;
            height: 100%;
        }

        #canvas-container {
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        @media print {

            @page {
                size: auto landscape; /* or 'auto' or 'letter', etc. */
            }

            *:not(:has(#canvas)):not(#canvas) {
                display: none;
            }

            #canvas-container { 
            }
            
            #canvas{
                width: 100%;
                height: 100%;
                display: block;
                width: 100%;
                height: 100%;
                page-break-after: always;
            }
        }
    </style>
</head>

<body>
   
        <canvas id="canvas"></canvas>
    

    <script>
        async function config(params) {
            let tables = <?php echo json_encode($plan); ?>;
            let reservs = <?php echo json_encode($groups); ?>;
            let tableConfig = <?php echo $result; ?>;
            console.log(tableConfig);
            console.log("Tables", tables);
            console.log("Groups", reservs


            );
            const ctx = setupCanvas(document.getElementById('canvas'));

            // Resize the canvas to fill the available space
            // function resizeCanvas() {
            //     canvas.width = window.innerWidth;
            //     canvas.height = window.innerHeight;
            //     renderReservationsMap(); // Re-render after resizing
            // }
            canvas.width = 1754;
            canvas.height = 1240;

            // Call resize function on window resize
            // window.addEventListener('resize', resizeCanvas);
            // resizeCanvas(); // Initial call to set the canvas size
            renderReservationsMap();

            renderReservationsMap();
            // Function to render the table map
            function renderTableMap() {
                ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas before drawing


                console.log("Rendering Tables", tables);
                // Draw each table from the config
                tables.forEach(table => {
                    ctx.fillStyle = 'transparent'; // Table color
                    ctx.fillRect(table.x, table.y, table.width, table.height); // Draw the table

                    ctx.strokeStyle = 'black'; // Border color
                    ctx.strokeRect(table.x, table.y, table.width, table.height); // Table border

                    // // Add the table ID text
                    // ctx.fillStyle = 'black'; // Text color
                    // ctx.font = '16px Arial';
                    // ctx.fillText(`Table ${table.id}`, table.x + 10, table.y + 30);

                    // Draw the seats for the table
                    drawSeats(table.x, table.y, table.width, table.height, table.posti);

                });
            }

            function renderReservationsMap() {
                renderTableMap();
                if (!tableConfig.pairings) {
                    return;
                }
                console.log("Rendering Reservations", tableConfig.pairings);
                tables.forEach((table) => {
                    
                    let groups = tableConfig.pairings[table.id].map((id)=>{return reservs.find((o)=>{return o.name == id})})
                    if(!groups || groups.length == 0){
                        return;
                    }
                    
                    let totalGroupSize = groups.reduce((sum, group) => sum + group.size, 0);
                    let totalSeats = table.posti.reduce((sum, seats) => sum + seats, 0);

                    console.log("Table", table.id, "Groups", groups, "Total Group Size", totalGroupSize, "Total Seats", totalSeats);
                    let offset = 0;
                    let tph = table.height / Math.max(table.posti[0], table.posti[2]);
                    let tpw = table.width / Math.max(table.posti[1], table.posti[3]);
                    let Ogroups = [];
                    let ap = -table.posti[3];
                    let gl = groups.length;
                    let salta = 0;
                    for (let i = 0; i < gl; i++) {
                        let gr = groups.find((group) => (group.size + ap) % 2 == 0);
                        if (!gr) {
                            if (salta < totalSeats - totalGroupSize) {
                                salta++;
                                console.log("Group skip added", ap, table.id);
                                Ogroups.push({ skip: true, size: 1 });
                                i--;
                                continue;
                            }
                            gr = groups[0];
                            console.log("Group not found", ap, table.id);
                        }
                        ap += gr.size;
                        Ogroups.push(gr);
                        groups.splice(groups.indexOf(gr), 1);
                    }
                    let pRim = [...table.posti];
                    let int = 0;
                    Ogroups.forEach((group, idx) => {

                        let random = seededRandom(table.id * 150 + idx ?? 0);
                        let color = `rgb(${random() * 255},${random() * 255},${random() * 255})`;
                        let grs = group.size;
                        if (group.skip) {
                            color = "transparent";
                        }
                        //console.log("   Group", group, "Seats", grs);
                        //TOP SEATS
                        let topSeats = Math.min(grs, pRim[3]);
                        let left = grs - topSeats;
                        pRim[3] = pRim[3] - topSeats;

                        let vSeats = Math.min(left, pRim[0] + pRim[2]);
                        left = left - vSeats;
                        let vSeatsHL = Math.floor(vSeats / 2);
                        let vSeatsHH = vSeats - vSeatsHL;
                        let vSeatsR = (pRim[0] > pRim[2]) ? vSeatsHH : vSeatsHL;
                        let vSeatsL = (pRim[0] > pRim[2]) ? vSeatsHL : vSeatsHH;

                        pRim[0] = pRim[0] - vSeatsR;
                        pRim[2] = pRim[2] - vSeatsL;



                        let botSeats = Math.min(left, table.posti[1]);
                        left = left - botSeats;
                        pRim[1] = pRim[1] - botSeats;

                        if (left > 0) {
                            console.error("Not enough seats for group", group);
                        }

                        //draw seats coloered
                        //vertical coloring
                        if (int++ < 0) {
                            console.log("Group Skipped");
                            return;
                        };
                        console.log("    Group", group, "Seats", grs, "Top", topSeats, "Left", left, "VSeatsL", vSeatsL, "VSeatsR", vSeatsR, "Bot", botSeats);
                        //topSeats
                        console.log("color", color);
                        ctx.fillStyle = color;
                        if (topSeats > 0) {
                            let f = (table.posti[3] - (pRim[3] + topSeats) == 0);
                            let l = (pRim[3] == 0);
                            //ctx.fillRect(table.x + (tpw*(table.posti[3]-pRim[3]-topSeats)), table.y, tpw*topSeats, tph);
                            ctx.beginPath();
                            ctx.moveTo(table.x + (tpw * (table.posti[3] - pRim[3] - topSeats)), table.y);
                            ctx.lineTo(table.x + (tpw * (table.posti[3] - pRim[3] - topSeats)) + tpw * topSeats, table.y);
                            ctx.lineTo(table.x + (tpw * (table.posti[3] - pRim[3] - topSeats)) + tpw * topSeats - (l * (tpw / 2)), table.y + tph / 2);
                            ctx.lineTo(table.x + (tpw * (table.posti[3] - pRim[3] - topSeats)) + (f * (tpw / 2)), table.y + tph / 2);
                            ctx.closePath();
                            ctx.fill();
                        }



                        //vertical seats left
                        if (vSeatsL > 0) {
                            f = (table.posti[2] - (pRim[2] + vSeatsL) == 0 && table.posti[3] > 0);
                            l = (pRim[2] == 0 && table.posti[1] > 0);
                            //ctx.fillStyle = f?color:"red";
                            ctx.beginPath();
                            ctx.lineTo(table.x + 1, table.y + ((tph * (table.posti[2] - pRim[2] - vSeatsL)) * !f));
                            ctx.lineTo(table.x + 1 + tpw / 2, table.y + (tph * (table.posti[2] - pRim[2] - vSeatsL + f / 2)));
                            ctx.lineTo(table.x + 1 + tpw / 2, table.y + (tph * (table.posti[2] - pRim[2] - l / 2)));
                            ctx.lineTo(table.x + 1, table.y + (tph * (table.posti[2] - pRim[2])));
                            ctx.closePath();
                            ctx.fill();
                        }

                        //vertical seats right
                        if (vSeatsR > 0) {
                            f = (table.posti[0] - (pRim[0] + vSeatsR) == 0 && table.posti[3] > 0);
                            l = (pRim[0] == 0 && table.posti[1] > 0);
                            // ctx.fillStyle = color;
                            ctx.beginPath();
                            ctx.lineTo(table.x - 1 + table.width, table.y + ((tph * (table.posti[0] - pRim[0] - vSeatsR)) * !f));
                            ctx.lineTo(table.x - 1 + table.width - tpw / 2, table.y + (tph * (table.posti[0] - pRim[0] - vSeatsR + f / 2)));
                            ctx.lineTo(table.x - 1 + table.width - tpw / 2, table.y + (tph * (table.posti[0] - pRim[0] - l / 2)));
                            ctx.lineTo(table.x - 1 + table.width, table.y + (tph * (table.posti[0] - pRim[0])));

                            ctx.closePath();
                            ctx.fill();
                        }


                        //bottom seats
                        if (botSeats > 0) {
                            console.log("BotSeats", botSeats);
                            let f = (table.posti[1] - (pRim[1] + botSeats) == 0);
                            let l = (pRim[1] == 0);
                            //ctx.fillRect(table.x + (tpw*(table.posti[3]-pRim[3]-topSeats)), table.y, tpw*topSeats, tph);
                            ctx.beginPath();
                            ctx.moveTo(table.x + (tpw * (table.posti[1] - pRim[1] - botSeats)), table.y + table.height);
                            ctx.lineTo(table.x + (tpw * (table.posti[1] - pRim[1] - botSeats)) + tpw * botSeats, table.y + table.height);
                            ctx.lineTo(table.x + (tpw * (table.posti[1] - pRim[1] - botSeats)) + tpw * botSeats - (l * (tpw / 2)), table.y + table.height - tph / 2);
                            ctx.lineTo(table.x + (tpw * (table.posti[1] - pRim[1] - botSeats)) + (f * (tpw / 2)), table.y + table.height - tph / 2);
                            ctx.closePath();
                            ctx.fill();
                        }
                    });


                })
            }

            function drawSeats(tx, ty, tw, th, posti) {
                if (posti.length !== 4) return;
                let size = Math.min(
                    th * 0.8 / (posti[0]),
                    tw * 0.8 / (posti[1]),
                    th * 0.8 / (posti[2]),
                    tw * 0.8 / (posti[3])
                );
                let spaced = size / 0.8;
                let border = (spaced - size) / 2

                let len = posti[0] * spaced - 2 * border;
                let start = (th - len) / 2;
                for (let i = 0; i < posti[0]; i++) {
                    drawSeat(tx + tw, ty + start + i * spaced, Math.PI, size);
                }
                len = posti[1] * spaced - 2 * border;
                start = (tw - len) / 2;
                for (let i = 0; i < posti[1]; i++) {
                    drawSeat(tx + start + i * spaced, ty + th, -Math.PI / 2, size);
                }
                len = posti[2] * spaced - 2 * border;
                start = (th - len) / 2;
                for (let i = 0; i < posti[2]; i++) {
                    drawSeat(tx - size, ty + start + i * spaced, 0, size);
                }
                len = posti[3] * spaced - 2 * border;
                start = (tw - len) / 2;
                for (let i = 0; i < posti[3]; i++) {
                    drawSeat(tx + start + i * spaced, ty - size, Math.PI / 2, size);
                }

            }

            function drawSeat(x, y, rotation = 0, size = 30) {
                let radius = 0.3 * size;

                ctx.save();
                // Translate to the center of the seat, then rotate
                ctx.translate(x + size / 2, y + size / 2);
                ctx.rotate(rotation);
                // Translate back so drawing starts at the top-left corner
                ctx.translate(-size / 2, -size / 2);

                ctx.beginPath();
                ctx.moveTo(radius, 0); // Start at the top-left corner with rounded edge

                // Draw the top edge
                ctx.lineTo(size - radius, 0);
                ctx.arcTo(size, 0, size, radius, radius); // Top-right corner

                // Draw the right edge
                ctx.lineTo(size, size - radius);
                ctx.arcTo(size, size, size - radius, size, radius); // Bottom-right corner

                // Draw the back
                ctx.lineTo(0, size);
                ctx.lineTo(0, 0);
                ctx.lineTo(size - radius, 0);
                ctx.moveTo(0.15 * size, 0);
                ctx.lineTo(0.15 * size, 0);
                ctx.lineTo(0.15 * size, size);


                ctx.closePath();
                ctx.fillStyle = 'white'; // Fill color
                ctx.fill();
                ctx.strokeStyle = 'black'; // Border color
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.restore();
            }

            function seededRandom(seed) {
                const m = 0x80000000, a = 1103515245, c = 12345;
                return function () {
                    seed = (a * seed + c) % m;
                    return seed / m;
                };
            }
        }
        config();


        function setupCanvas(canvas) {
            // Get the device pixel ratio, falling back to 1.
            var dpr = window.devicePixelRatio || 1;
            console.log(dpr);
            // Get the size of the canvas in CSS pixels.
            var rect = canvas.getBoundingClientRect();
            // Give the canvas pixel dimensions of their CSS
            // size * the device pixel ratio.
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            var ctx = canvas.getContext('2d');
            // Scale all drawing operations by the dpr, so you
            // don't have to worry about the difference.
            ctx.scale(dpr, dpr);
            return ctx;
        }
    </script>
</body>

</html>