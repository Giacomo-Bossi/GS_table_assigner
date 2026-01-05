<?php

$DEB_gen_start = microtime(true); // Start timing
require __ROOT__ . '/vendor/autoload.php';
require __ROOT__ . '/functions/solver.php';

$TITLE = "Festa dello Sport";
$YEAR = "2025";

$DEBUG = true; // Set to true to enable debug data output

use setasign\Fpdi\Fpdi;

$DEB_pdfload_start = microtime(true); // Start timing PDF loading
// Create new FPDI instance
$pdf = new Fpdi('L', 'mm', 'A3');

// Add a page
$pdf->AddPage();

// Set the source PDF file
$pdf->setSourceFile(__ROOT__ . '/res/PLANIMETRIA.pdf');

// Import page 1set size

$templateId = $pdf->importPage(1);

// Use the imported page as the template
$pdf->useTemplate($templateId);

// Hide default HEADERS
$pdf->SetTitle($TITLE . ' ' . $YEAR);
$pdf->SetAuthor('GS Montesolaro');
$pdf->SetCreator('GS Montesolaro');
$pdf->SetSubject($TITLE . ' ' . $YEAR . ' - Planimetria');
$pdf->SetKeywords($TITLE . ', Planimetria, ' . $YEAR);
$pdf->SetMargins(0, 0, 0); // Set margins to zero
$pdf->SetAutoPageBreak(false, 0); // Disable auto page breaks

$pdf->SetFillColor(255, 255, 255); // Set background color to white
$pdf->Rect(90, 11, 62, 17, 'F'); // Fill the background with white color
$pdf->Rect(155, 11, 175, 17, 'F'); // Fill the background with white color

// Set font and position for writing
$pdf->SetFont('Helvetica', '', 50);
$pdf->SetTextColor(39, 118, 187);
$pdf->SetXY(93, 21);  // X and Y position in mm
$pdf->Write(0, strtoupper($TITLE) . ' ' . $YEAR); // Write text

$DEB_pdfload_end = microtime(true); // Start timing PDF loading
////////END OF HEADERS AND TITLE//////////////

////////START OF JSON PARSING   //////////////

$DEB_json_start = microtime(true); // Start timing JSON parsing 
// Load JSON data
$jsonFile = __ROOT__ . '/res/tavoli.json';
$jsonData = file_get_contents($jsonFile);
if ($jsonData === false) {
    die("Error reading JSON file.");
}
$data = json_decode($jsonData, true);
if ($data === null) {
    die("Error decoding JSON data: " . json_last_error_msg());
}
$DEB_json_end = microtime(true); // End timing JSON parsing

////////START OF CSV PARSING   //////////////
$DEB_csv_start = microtime(true); // Start timing CSV parsing
// Load CSV data
$csvFile = __ROOT__ . '/res/giove.csv';
$csvData = file_get_contents($csvFile);
if ($csvData === false) {
    die("Error reading CSV file.");
}
$lines = explode("\n", $csvData);
$csvArray = [];
foreach ($lines as $line) {
    $line = trim($line);
    if (!empty($line)) {
        $line = str_getcsv($line, ';');
        if ($line[1] !== 'Giovedì 05/06') {
            // Skip lines with other dates 
            continue;
        }
        $csvArray[] = [
            'name' => $line[0],
            'show_name' => $line[2], // Show name
            'size' => (int)$line[3], // Convert group size to integer
            'required_head' => ($line[7] == "TRUE") ? 1 : 0, // Convert required head to boolean
            'near_field' => ($line[8] == "TRUE") ? 1 : 0, // Convert near field to boolean
            'close_to' => ((!isset($line[9])) ? [] : explode(",", $line[9])), // array of grouped groups
        ];
    }
}
$DEB_csv_end = microtime(true); // End timing CSV parsing

////////SOLVER CALL//////////////
$DEB_solver_start = microtime(true); // Start timing solver
$result = (_SOLVER_solve($data, $csvArray)); // Call the solver function with the data

if ($result['total guests'] > $result['total assignable']) {
    die("Error: Not enough space for the guests. Total guests: " . $result['total guests'] . ", Total tables: " . $result['total assignable']);
}
$DEB_solver_end = microtime(true); // End timing solver

////////START OF PDF COMPILATION//////////////
$DEB_pdf_start = microtime(true); // Start timing PDF compilation
// Loop through each table in the JSON data
$DEB_failedcolorsc = 0;

$lastColor = [255, 255, 255]; // Initialize last color to white
$textsToPrint = [];
foreach ($data as $table) {
    $gui = $table['gui']; // Gui data for table
    // Extract table properties
    $x = $gui['x']; // X position in mm
    $y = $gui['y']; // Y position in mm
    $width = $gui['width']; // Width in mm
    $height = $gui['height']; // Height in mm

    // Draw the table rectangle
    $pdf->SetFillColor(230, 250, 230); // Set fill color

    if (isset($table['tags']) && in_array('near_campo', $table['tags'])) {
        $pdf->SetFillColor(190, 230, 230); // Set fill color for near campo
    }

    $pdf->Rect($x, $y, $width, $height, 'F'); // Fill the rectangle

    $arrayofgruppi = [];
    $capotavola = [];
    foreach ($result['pairings'][$table['table_id']] as $group_name) {

        // Find the group in $csvArray with name = $group_name
        $group = null;
        foreach ($csvArray as $g) {
            if ($g['name'] === $group_name) {
                $group = $g;
                break;
            }
        }
        if ($group['size'] <= 0) {
            continue; // Skip groups with size 0 or less
        }

        if ($group['required_head'] == 1 && $table['head_seats'] > 0) {
            $capotavola[] = $group;
            $table['head_seats']--;
            continue; // Skip to next group if this is a head of table
        }
        $arrayofgruppi[] = $group; // Add group name to the array
    }


    if (count($capotavola) > 0  && isset($table["gui"]["head_on"]) && $table["gui"]["head_on"] == "START") {
        $arrayofgruppi = array_merge($capotavola, $arrayofgruppi); // Add head of table groups at the start
    } else if (count($capotavola) > 0  && isset($table["gui"]["head_on"]) && $table["gui"]["head_on"] == "END") {
        $arrayofgruppi = array_merge($arrayofgruppi, $capotavola); // Add head of table groups at the end
    } else if (count($capotavola) > 0  && isset($table["gui"]["head_on"]) && $table["gui"]["head_on"] == "BOTH") {
        // Add half on the start and half on the end
        $mid = ceil(count($capotavola) / 2);
        $arrayofgruppi = array_merge(
            array_slice($capotavola, 0, $mid),
            $arrayofgruppi,
            array_slice($capotavola, $mid)
        );
    }

    $width = $gui['width']; // Width in mm
    $height = $gui['height']; // Height in mm
    $x = $gui['x']; // X position in mm
    $y = $gui['y']; // Y position in mm


    if ($width <= $height) {

        $unitheight = $height / ($table['capacity'] - $table['head_seats']); // Calculate unit height based on side capacity

        foreach ($arrayofgruppi as $group) {
            $group_name = $group['show_name'] . ' (' . $group['size'] . ($group["required_head"] == 1 ? ';C' : '') . ')'; // Group label

            $group_height = ($group['size'] - $group['required_head']) * $unitheight; // Calculate height based on group size

            if ($y + $group_height >=  $gui['y'] +  $gui['height']) {
                $group_height =  $gui['y'] +  $gui['height'] - $y; // Adjust height to fit within the table

            }

            if ($group['required_head'] == 1 &&  $gui['head_on'] == "END") {
                $y =  $gui['y'] + $gui['height'] - $group_height;
            }

            // Generate a random pastel color for each group
            do{
                $r = rand(150, 230);
                $g = rand(150, 230);
                $b = rand(150, 230);
                $newColor = [$r, $g, $b];
                $DEB_failedcolorsc++;
            } while (deltaE($lastColor, $newColor) < 20); // Ensure the color is different enough from the last one
            $DEB_failedcolorsc--;
            $lastColor = $newColor; // Update last color
            // $r = rand(150, 230);
            // $g = rand(150, 230);
            // $b = rand(150, 230);
            $pdf->SetFillColor($r, $g, $b); // Set random fill color

            $pdf->Rect($x, $y, $width, $group_height, 'F'); // Fill the rectangle for each group

            // Calculate position to center the text in the table

            setFont($pdf);
            $textWidth = $pdf->GetStringWidth($group_name) + $pdf->GetStringWidth(" ");
            $textX = $x + ($width - $textWidth) / 2; // Center horizontally
            $textY = $y + ($group_height / 2); // Center vertically

            // // Write the group name
            $textsToPrint[] = [
                'text' => $group_name,
                'x' => $textX,
                'y' => $textY,
                'r' => $r,
                'g' => $g,
                'b' => $b
            ];

            // Move down for the next group
            $y += $group_height;
        }
    } else {
        $unitwidth = $width / ($table['capacity'] - $table['head_seats']); // Calculate unit height based on side capacity

        $hor_idx = 0;
        $totgr = count($arrayofgruppi);
        foreach ($arrayofgruppi as $group) {
            $group_name = $group['show_name'] . ' (' . $group['size'] . ($group["required_head"] == 1 ? ';C' : '') . ')'; // Group label


            $group_width = ($group['size'] - $group['required_head']) * $unitwidth; // Calculate height based on group size

            if ($y + $group_width >= $table['gui']['y'] + $table['gui']['width']) {
                $group_width = $table['gui']['y'] + $table['gui']['width'] - $y; // Adjust height to fit within the table

            }

            // Generate a random pastel color for each group
            do{
                $r = rand(150, 230);
                $g = rand(150, 230);
                $b = rand(150, 230);
                $newColor = [$r, $g, $b];
                $DEB_failedcolorsc++;
            } while (deltaE($lastColor, $newColor) < 20); // Ensure the color is different enough from the last one
            $DEB_failedcolorsc--;
            $lastColor = $newColor; // Update last color
            $pdf->SetFillColor($r, $g, $b); // Set random fill color

            $pdf->Rect($x, $y, $group_width, $height, 'F'); // Fill the rectangle for each group

            // Calculate position to center the text in the table

            setFont($pdf);
            $textWidth = $pdf->GetStringWidth($group_name) + $pdf->GetStringWidth(" ");
            $textX = $x + ($group_width - $textWidth) / 2; // Center horizontally
            $textY = $y + 3 + $height * ($hor_idx / 4); // Center vertically with a small offset
            $hor_idx++; // Increment horizontal group ID for next group
            // // Write the group name
            $textsToPrint[] = [
                'text' => $group_name,
                'x' => $textX,
                'y' => $textY,
                'r' => $r,
                'g' => $g,
                'b' => $b
            ];
            // Move down for the next group
            $x += $group_width;
        }
    }
}

setFont($pdf);
//draw the table names now
foreach ($textsToPrint as $textData) {
    $pdf->SetFillColor($textData['r'], $textData['g'], $textData['b']); // Set color to the pastel color
    $pdf->Rect($textData['x'], $textData['y'] - 1.75, $pdf->GetStringWidth($textData['text']) + 2, 3, 'F'); // Fill background for text

    $pdf->SetXY($textData['x'], $textData['y']);
    $pdf->Write(0, $textData['text']);
}
$DEB_pdf_end = microtime(true); // End timing PDF compilation
$DEB_gen_end = microtime(true); // End timing generation

if($DEBUG){
    // Debug output
    $pdf->SetFont('Helvetica', 'B', 12);
    $pdf->SetTextColor(0, 0, 0);
    $pdf->SetXY(355, 155);
    $pdf->Write(0, "DEBUG");
    $pdf->SetFont('Helvetica', 'B', 9);
    $pdf->SetXY(355, 160);
    $pdf->Write(0, "Failed color attempts: " . $DEB_failedcolorsc);
    $DEB = $result['DEB'];
    $pdf->SetXY(355, 165);
    $pdf->Write(0, "Timings: ");
    $pdf->SetXY(356, 170);
    $pdf->Write(0, "Solver: ");
    $pdf->SetXY(357, 175);
    $pdf->Write(0, "ILP Solver: " . number_format($DEB['solver_duration'], 6) . " sec");
    $pdf->SetXY(357, 180);
    $pdf->Write(0, "Close Solver: " . number_format($DEB['close_solver_duration'], 6) . " sec");
    $pdf->SetXY(357, 185);
    $pdf->Write(0, "Head Solver: " . number_format($DEB['head_solver_duration'], 6) . " sec");
    $pdf->SetXY(357, 190);
    $pdf->Write(0, "Total: " . number_format($DEB['total_duration'], 6) . " sec");
    $pdf->SetXY(356, 195);
    $pdf->Write(0, "Render: ");
    $pdf->SetXY(357, 200);
    $pdf->Write(0, "PDF Load: " . number_format($DEB_pdfload_end - $DEB_pdfload_start, 6) . " sec");
    $pdf->SetXY(357, 205);
    $pdf->Write(0, "JSON Parse: " . number_format($DEB_json_end - $DEB_json_start, 6) . " sec");
    $pdf->SetXY(357, 210);
    $pdf->Write(0, "CSV Parse: " . number_format($DEB_csv_end - $DEB_csv_start, 6) . " sec");
    $pdf->SetXY(357, 215);
    $pdf->Write(0, "PDF Render: " . number_format($DEB_pdf_end - $DEB_pdf_start, 6) . " sec");
    $pdf->SetXY(357, 220);
    $pdf->Write(0, "Solver call: " . number_format($DEB_solver_end - $DEB_solver_start, 6) . " sec");
    $pdf->SetXY(356, 225);
    $pdf->Write(0, "TOTAL: " . number_format($DEB_gen_end - $DEB_gen_start, 6) . " sec");

}


// Output the result
$pdf->Output(); // To browser
function setFont($pdf)
{
    $pdf->SetFont('Helvetica', 'B', 7);
    $pdf->SetTextColor(50, 50, 50);
}

function rgbToLab($r, $g, $b)
{
    // Convert RGB [0,255] to XYZ
    foreach (['r' => $r, 'g' => $g, 'b' => $b] as $k => $v) {
        $v = $v / 255;
        $$k = ($v > 0.04045) ? pow(($v + 0.055) / 1.055, 2.4) : ($v / 12.92);
    }
    $x = ($r * 0.4124564 + $g * 0.3575761 + $b * 0.1804375) * 100;
    $y = ($r * 0.2126729 + $g * 0.7151522 + $b * 0.0721750) * 100;
    $z = ($r * 0.0193339 + $g * 0.1191920 + $b * 0.9503041) * 100;

    // Convert XYZ to Lab
    foreach (['x' => $x, 'y' => $y, 'z' => $z] as $k => $v) {
        $ref = ['x' => 95.047, 'y' => 100.0, 'z' => 108.883][$k];
        $t = $v / $ref;
        $$k = ($t > 0.008856) ? pow($t, 1/3) : (7.787 * $t + 16/116);
    }

    return [
        'L' => 116 * $y - 16,
        'a' => 500 * ($x - $y),
        'b' => 200 * ($y - $z),
    ];
}

function deltaE($rgb1, $rgb2)
{
    $lab1 = rgbToLab($rgb1[0], $rgb1[1], $rgb1[2]);
    $lab2 = rgbToLab($rgb2[0], $rgb2[1], $rgb2[2]);
    return sqrt(
        pow($lab1['L'] - $lab2['L'], 2) +
        pow($lab1['a'] - $lab2['a'], 2) +
        pow($lab1['b'] - $lab2['b'], 2)
    );
}
