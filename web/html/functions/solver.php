<?php
function _SOLVER_solve($tavoli, $prenotazioni) {
    
    $DEB_gen_start = microtime(true);

    $DEB_close_start = microtime(true);
    $vicini = [];
    foreach ($prenotazioni as $prenotazione) {
        if(count($prenotazione['close_to']) > 0) {
            $group = [];
            $group[] = $prenotazione;
            unset($prenotazioni[$prenotazione['name']]); // Remove the main reservation from the list
            foreach ($prenotazione['close_to'] as $close_to) {
                foreach ($prenotazioni as $key => $p) {
                    if ($p['name'] === $close_to) {
                        $group[] = $p;
                        unset($prenotazioni[$key]);
                        break;
                    }
                }
            }
            $vicini[] = $group; // Add the group of close reservations
        }
    }
    $DEB_close_end = microtime(true);

    $assegnamenti = [];
    $postiassegnati = 0;
    foreach($vicini as $group) {
        $size = 0;
        foreach ($group as $prenotazione) {
            $size += $prenotazione['size'];
        }
        $head_seats = 0;
        foreach ($group as $prenotazione) {
            $head_seats += $prenotazione['required_head'];
        }
        foreach ($tavoli as $tavolo){///cerco un tavolo che abbia abbastanza posti
            if($tavolo['capacity'] >= $size && $tavolo['head_seats'] >= $head_seats) {
                foreach ($group as $pren){
                    $assegnamenti[] = [
                        'table_id' => $tavolo['table_id'],
                        'group_name' => $pren['name'],
                    ];
                    $tavolo['capacity'] -= $pren['size'];
                    $postiassegnati+=$pren['size'];
                }
                break;
            }
        }

        // Se non c'è un tavolo abbastanza grosso, cerco più tavoli consecutivi nello stesso gruppo.

        $t_gruppo = 1;
        $ok = false;
        while (true) {
            $assegnati = 0;
            $gr = array_filter($tavoli, fn($tavolo) => $tavolo['tags']['group'] == $t_gruppo);
            if (count($gr) == 0) {
                //echo "Nessun tavolo trovato per il gruppo ".$t_gruppo."\n";
                break;
            }
            

            $tentativo = [];
            foreach($group as $gruppo){
                foreach($gr as &$t_gr){
                    if($t_gr['capacity'] >= $gruppo['size'] && $t_gr['head_seats'] >= $gruppo['required_head']){
                        $tentativo[] = [
                            'table_id' => $t_gr['table_id'],
                            'group_name' => $gruppo['name'],
                            'size' => $gruppo['size'],
                            'required_head' => $gruppo['required_head'],
                        ];
                        //riduzione locale
                        $t_gr['capacity'] -= $gruppo['size'];
                        $t_gr['head_seats'] -= $gruppo['required_head'];
                        $assegnati += $gruppo['size'];

                        //riduzione globale
                        $tavoli[$t_gr['table_id']-1]['capacity'] -= $gruppo['size'];
                        $tavoli[$t_gr['table_id']-1]['head_seats'] -= $gruppo['required_head'];
                        break; // Break the inner loop to move to the next group
                    }
                }
            }
           // echo "Tentativo: ".$size." posti da assegnare, ".$assegnati."assegnati\n";
            if($assegnati == $size){
                $ok = true;
                break;
            }
            $t_gruppo++;
            ////REVERT ALL EDITS TO TABLES
            //echo "Tentativo fallito con gruppo".($t_gruppo-1);
            foreach($tentativo as $edit){
                $tavoli[$edit['table_id']]['capacity'] += $edit['size'];
                $tavoli[$edit['table_id']]['head_seats'] += $edit['required_head'];

                //revert global
                $tavoli[$edit['table_id']-1]['capacity'] += $edit['size'];
                $tavoli[$edit['table_id']-1]['head_seats'] += $edit['required_head'];
            }

        }
        if($ok){
            foreach($tentativo as $t){
                $assegnamenti[] = $t;
            }
            $postiassegnati += $assegnati;
        }else{
            foreach($group as $g){
                $prenotazioni[] = $g; // If we can't assign the group, we re-add it to the main list
            }
        }

    }
    
   
    $capotavola = [];
    $auto_prenotazioni = [];
    $manual_prenotazioni = [];
    foreach ($prenotazioni as $prenotazione) {
        if($prenotazione['near_field'] == 1) {
            // Skip near field groups
            $manual_prenotazioni[] = $prenotazione;
            continue;
        }
        if($prenotazione['required_head'] == 1){ //TEMPORARY FIX
            // Skip head seat groups
            $capotavola[] = $prenotazione;
            continue;
        }
        $auto_prenotazioni[] = $prenotazione;
    }
    // execute the near field solver
    
    $DEB_head_start = microtime(true);
    $capotavola_assegnazioni = solveCapotavolaReservations($tavoli, $capotavola);
    if($capotavola_assegnazioni['failed']) {
        // If there are failed near field reservations, we re-add them to the automatic one
        foreach ($capotavola_assegnazioni['failed'] as $failed) {
            $auto_prenotazioni[] = $failed;
        }
    }
    $DEB_head_end = microtime(true);


    $DEB_near_start = microtime(true);
    $near_field = solveNearFieldReservations($tavoli, $manual_prenotazioni);

    if($near_field['failed']) {
        // If there are failed near field reservations, we re-add them to the automatic one
       
        foreach ($near_field['failed'] as $failed) {
            $auto_prenotazioni[] = $failed;
        }
    }
    $DEB_near_end= microtime(true);

    $mapped_tavoli = [];
    foreach ($tavoli as $tavolo) {
        
        $mapped_tavoli[] = [
            'table_id' => $tavolo['table_id'],
            'capacity' => $tavolo['capacity'],
            'head_seats' => $tavolo['head_seats'],
        ];
    }

    $input = [
        'tables' => $mapped_tavoli,
        'groups' => $auto_prenotazioni
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
    
    $DEB_sol_start = microtime(true);
    //* ///REAL SOLVER CALL
    $result = file_get_contents($url, false, $context);
    if ($result === FALSE) {
        echo "Error calling the optimization service.";
        exit;
    } 
    
    $result = json_decode($result, true);

    /*/ // EMPTY TESTING RESULT
    $result = [
        "total guests" => 0,
        "total assignable" => 0,
        "pairings" => []
    ];
    foreach($mapped_tavoli as $tavolo) {
        $result['pairings'][$tavolo['table_id']] = [];
    }
    //*/
    $merged = $result["pairings"];
    $DEB_sol_end = microtime(true);


    foreach($near_field['assigned'] as $near_field_assignment) {
        $table_id = $near_field_assignment['table_id'];
        $group_name = $near_field_assignment['group_name'];
        // Add the near field assignment to the merged result
        array_unshift($merged[$table_id], $group_name);
        //$merged[$table_id][] = $group_name;  //i want the group to be the first (closer to the windows)
    }
    

    foreach($assegnamenti as $groupings) {
        $table_id = $groupings['table_id'];
        $group_name = $groupings['group_name'];
        // Add the groupings assignment to the merged result
        array_unshift($merged[$table_id], $group_name);
    }

    //print_r($capotavola_assegnazioni['assigned']);
    foreach($capotavola_assegnazioni['assigned'] as $capotavola_assignment) {
        $table_id = $capotavola_assignment['table_id'];
        $group_name = $capotavola_assignment['group_name'];
        // Add the head spot assignment to the merged result
       // echo "Adding ".$table_id." - ".$group_name;
        array_unshift($merged[$table_id], $group_name);
        //$merged[$table_id][] = $group_name;  
    }
    $DEB_gen_end = microtime(true);
    $trueresults = [
        'total guests' => $result['total guests'] + $near_field['number_assigned'],
        'total assignable' => $result['total assignable'] + $near_field['number_assigned'],
        'pairings' => $merged,
        'DEB' => [
            'solver_duration' => $DEB_sol_end - $DEB_sol_start,
            'close_solver_duration' => $DEB_close_end - $DEB_close_start,
            'head_solver_duration' => $DEB_head_end - $DEB_head_start,
            'total_duration' => $DEB_gen_end - $DEB_gen_start
        ],
    ];


    return $trueresults;
}


function solveNearFieldReservations(&$tavoli, $campo_prenotazioni) {
    $assegnamenti = [];
    $fallimenti = []; 
    $totassegnati = 0;
    foreach ($campo_prenotazioni as $pren) {
        $found = false;
        foreach ($tavoli as &$tavolo) {
            
            if (isset($tavolo['tags']) && in_array('near_campo', $tavolo['tags']) && ($tavolo['capacity'] >= $pren['size']) && ($tavolo['head_seats'] >= $pren['required_head'])) {
                // Assign the group to this table
                $assegnamenti[] = [
                    'table_id' => $tavolo['table_id'],
                    'group_name' => $pren['name'],
                ];
                // Reduce the capacity of the table
                $tavolo['capacity'] -= $pren['size'];
                $totassegnati+=$pren['size'];
                $found = true;
                break; // Stop searching for this group
            }
        }
        if (!$found) {
            $fallimenti[] = $pren; // Store the failed assignment
            continue; //soft fail, if it can't find a place, leave to the basic solver
        }
    }
    $res = [
        'assigned' => $assegnamenti,
        'failed' => $fallimenti,
        'number_assigned' => $totassegnati
    ];
    return $res;
}


function solveCapotavolaReservations(&$tavoli, $capotavola_prenotazioni) {
    $assegnamenti = [];
    $fallimenti = []; 
    $totassegnati = 0;
    foreach ($capotavola_prenotazioni as $pren) {
        $found = false;
        foreach ($tavoli as &$tavolo) {
            
            if (($tavolo['capacity'] >= $pren['size']) && ($tavolo['head_seats'] >= $pren['required_head'])) {
                // Assign the group to this table
                $assegnamenti[] = [
                    'table_id' => $tavolo['table_id'],
                    'group_name' => $pren['name'],
                ];
                // Reduce the capacity of the table
                $tavolo['capacity'] -= $pren['size'];
                $totassegnati+=$pren['size'];
                $found = true;
                break; // Stop searching for this group
            }
        }
        if (!$found) {
            $fallimenti[] = $pren; // Store the failed assignment
            continue; //soft fail, if it can't find a place, leave to the basic solver
        }
    }
    $res = [
        'assigned' => $assegnamenti,
        'failed' => $fallimenti,
        'number_assigned' => $totassegnati
    ];
    return $res;



}


?>
