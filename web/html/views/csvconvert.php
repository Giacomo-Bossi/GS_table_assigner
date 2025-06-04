<?php
require __ROOT__ . '/vendor/autoload.php';
require __ROOT__ . '/functions/solver.php';

$TITLE = "Festa dello Sport";
$YEAR = "2025";

//echo "<h1>CSV Convert</h1>";

use setasign\Fpdi\Fpdi;

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

////////END OF HEADERS AND TITLE//////////////

////////START OF JSON PARSING   //////////////

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

////////START OF CSV PARSING   //////////////
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
            'close_to' => ((!isset($line[9]))?[]:explode(",", $line[9])), // array of grouped groups
        ];
    }
}


////////SOLVER CALL//////////////
$result = (_SOLVER_solve($data, $csvArray)); // Call the solver function with the data

if ($result['total guests'] > $result['total assigneable']) {
    die("Error: Not enough space for the guests. Total guests: " . $result['total guests'] . ", Total tables: " . $result['total assigneable']);
}


////////START OF PDF COMPILATION//////////////
// Loop through each table in the JSON data
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
        // $group = array_find($csvArray, function($item) use ($group_name) {
        //     return $item['name'] === $group_name;
        // });
        $group = null;
        foreach ($csvArray as $g) {
            if ($g['name'] === $group_name) {
                $group = $g;
                break;
            }
        }
        if ($group['required_head'] == 1 && $table['head_seats'] > 0) {
            $capotavola[] = $group;
            $table['head_seats']--;
            continue; // Skip to next group if this is a head of table
        }
        $arrayofgruppi[] = $group; // Add group name to the array
    }
    if (count($capotavola) > 0  && isset($tavolo["gui"]["head_on"]) && $tavolo["gui"]["head_on"] == "START") {
        $arrayofgruppi = array_merge($capotavola, $arrayofgruppi); // Add head of table groups at the start
    } else if (count($capotavola) > 0  && isset($tavolo["gui"]["head_on"]) && $tavolo["gui"]["head_on"] == "END") {
        $arrayofgruppi = array_merge($arrayofgruppi, $capotavola); // Add head of table groups at the end
    } else if (count($capotavola) > 0  && isset($tavolo["gui"]["head_on"]) && $tavolo["gui"]["head_on"] == "BOTH") {
        // Add half on the start and half on the end
        $mid = ceil(count($capotavola) / 2);
        $arrayofgruppi = array_merge(
            array_slice($capotavola, 0, $mid),
            $arrayofgruppi,
            array_slice($capotavola, $mid)
        );
    }


    // foreach ($arrayofgruppi as $group) {
    //     $group_name = $group['name']; // Group name
    //     // Set font and color for group name
    //     $pdf->SetFont('Helvetica', '', 12);
    //     $pdf->SetTextColor(0, 0, 0); // Black color

    //     // Calculate position to center the text in the table
    //     $textWidth = $pdf->GetStringWidth($group_name) + $pdf->GetStringWidth(" ");
    //     $textX = $x + ($width - $textWidth) / 2; // Center horizontally
    //     $textY = $y + ($height / 2); // Center vertically with a small offset

    //     // Write the group name
    //     $pdf->SetXY($textX, $textY);
    //     $pdf->Write(0, $group_name);
    // }

    $width = $gui['width']; // Width in mm
    $height = $gui['height']; // Height in mm
    $x = $gui['x']; // X position in mm
    $y = $gui['y']; // Y position in mm

    if ($width <= $height) {


        $unitheight = $height / ($table['capacity'] - $table['head_seats']); // Calculate unit height based on side capacity


        foreach ($arrayofgruppi as $group) {
            $group_name = $group['show_name']; // Group name

            $group_height = ($group['size'] - $group['required_head']) * $unitheight; // Calculate height based on group size

            if ($y + $group_height >= $table['gui']['y'] + $table['gui']['height']) {
                $group_height = $table['gui']['y'] + $table['gui']['height'] - $y; // Adjust height to fit within the table

            }

            // Generate a random pastel color for each group
            $r = rand(150, 230);
            $g = rand(150, 230);
            $b = rand(150, 230);
            $pdf->SetFillColor($r, $g, $b); // Set random fill color

            $pdf->Rect($x, $y, $width, $group_height, 'F'); // Fill the rectangle for each group

            // Calculate position to center the text in the table
            
            $pdf->SetFont('Helvetica', '', 5);
            $pdf->SetTextColor(50, 50, 50); 
            $textWidth = $pdf->GetStringWidth($group_name) + $pdf->GetStringWidth(" ");
            $textX = $x + ($width - $textWidth) / 2; // Center horizontally
            $textY = $y + ($group_height / 2); // Center vertically
            

            //$pdf->Rect($textX , $textY - 1, $textWidth * 1.25, 2, 'F'); // Fill background for text


            // // Write the group name
            $textsToPrint[] = [
                'text' => $group_name,
                'x' => $textX,
                'y' => $textY
            ];
            // $pdf->SetXY($textX, $textY);
            // $pdf->Write(0, $group_name);

            // Move down for the next group
            $y += $group_height;
        }
    }  else {
        $unitwidth = $width / ($table['capacity'] - $table['head_seats']); // Calculate unit height based on side capacity


        
        $hor_idx=0;
        $totgr = count($arrayofgruppi);
        foreach ($arrayofgruppi as $group) {
            $group_name = $group['show_name']; // Group name

            $group_width = ($group['size'] - $group['required_head']) * $unitwidth; // Calculate height based on group size

            if ($y + $group_width >= $table['gui']['y'] + $table['gui']['width']) {
                $group_width = $table['gui']['y'] + $table['gui']['width'] - $y; // Adjust height to fit within the table

            }

            // Generate a random pastel color for each group
            $r = rand(150, 230);
            $g = rand(150, 230);
            $b = rand(150, 230);
            $pdf->SetFillColor($r, $g, $b); // Set random fill color

            $pdf->Rect($x, $y, $group_width,$height, 'F'); // Fill the rectangle for each group

            // Calculate position to center the text in the table
            
            $pdf->SetFont('Helvetica', '', 5);
            $pdf->SetTextColor(50, 50, 50); 
            $textWidth = $pdf->GetStringWidth($group_name) + $pdf->GetStringWidth(" ");
            $textX = $x + ($group_width - $textWidth)/ 2; // Center horizontally
            //$textY = $y + ($height) / 2; // Center vertically
            $textY = $y + 1 + (2 * ($hor_idx + (5 - $totgr)/2)); // Center vertically with a small offset
            $hor_idx++; // Increment horizontal group ID for next group

            
            //$pdf->Rect($textX , $textY - 1, $textWidth * 1.25, 2, 'F'); // Fill background for text


            // // Write the group name
            $textsToPrint[] = [
                'text' => $group_name,
                'x' => $textX,
                'y' => $textY
            ];

            // $pdf->SetXY($textX, $textY);
            // $pdf->Write(0, $group_name);

            // Move down for the next group
            $x += $group_width;
        }
    }

    
        $pdf->SetFont('Helvetica', '', 5);
        $pdf->SetTextColor(50, 50, 50); // Black color
    //draw the table names now
    foreach ($textsToPrint as $textData) {
        $pdf->SetXY($textData['x'], $textData['y']);
        $pdf->Write(0, $textData['text']);
    }

}


// // Set font and position for writing
// $pdf->SetFont('Helvetica', '', 12);
// $pdf->SetTextColor(0, 0, 0);


// $pdf->SetXY(50, 60);  // X and Y position in mm
// $pdf->Write(100, 'Mario Rossi'); // Write text

// Output the result
$pdf->Output(); // To browser
