<?php

error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);

    /** Defined as the document root ($_SERVER['DOCUMENT_ROOT']) */
    define('__ROOT__', $_SERVER['DOCUMENT_ROOT']);

    # .htaccess transform the requested url to this file, 
    #  with the old local path as the argument.
    $request = $_SERVER['REQUEST_URI'];

    # split the old path from the URL parameters.
    /** Array of [0]: path, [1]: query */
    $param = explode('?', $request);
    $param[0] = rtrim($param[0], '/');
    #remove trailing slashes and load the correct webpage.

    switch ($param[0]) {
        case '/':
        case '':
            require __ROOT__ . '/views/homepage.php';
            break;
        case '/login':
            require __ROOT__ . '/views/login.php';
            break;
        case '/logout':
            require __ROOT__ . '/functions/logout.php';
            break;
        case '/mappa':
            require __ROOT__ . '/views/map.php';
            break;
        case '/prenotazione':
            require __ROOT__ . '/views/new_reservation.php';
            break;
        case '/eventi':
            require __ROOT__ . '/views/eventi.php';
            break;
        case '/eventi/crea':
            require __ROOT__ . '/views/eventicrea.php';
            break;
        case '/eventi/modifica':
            require __ROOT__ . '/views/eventimodifica.php';
            break;
        case '/eventi/cancella':
            require __ROOT__ . '/views/eventicancella.php';
            break;
        case '/eventi/prenotazioni':
            require __ROOT__ . '/views/eventiprenotazioni.php';
            break;
        case '/eventi/prenotazioni/cancella':
            require __ROOT__ . '/views/prenotazionecancella.php';
            break;
        case '/phpinfo':
            die("disabled");
            phpinfo();
            break;
        case '/upstatus':
            //die("disabled");
            require __ROOT__ . '/functions/upstatus.php';
            break;
        default:
            // if the URL is like /user/username, load the user view.
            // $paths = explode('/', trim($param[0],"/"));
            // if($paths[0]=="user"){
            //     $userView = $paths[1];
            //     require __DIR__ . "/views/userView.php";
            //     break;
            // }            
            http_response_code(404); # set HTTP error code to 404: Not Found, if the route is not found.
            require __DIR__ . '/errors/404.php';
            break;
    }
?>