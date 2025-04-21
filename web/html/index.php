<?php

// error_reporting(E_ALL);
// ini_set('display_errors', 1);
    
    # .htaccess transform the requested url to this file, 
    #  with the old local path as the argument.
    $request = $_SERVER['REQUEST_URI'];

    # split the old path from the URL parameters.
    $param = explode('?', $request);
    $param[0] = rtrim($param[0], '/');
    #remove trailing slashes and load the correct webpage.

    switch ($param[0]) {
        case '/':
        case '':
        case '/home':
            require __DIR__ . '/views/homepage.php';
            break;
        case '/login':
            require __DIR__ . '/views/login.php';
            break;
        case '/register':
            require __DIR__ . '/views/register.php';
            break;
        case '/dashboard':
            require __DIR__ . '/views/dashboard.php';
            break;
        case '/profile':
            require __DIR__ . '/views/profile.php';
            break;
        case '/logout':
            require __DIR__ . '/functions/logout.php';
            break;
        case '/phpinfo':
            echo "disabled";
            //phpinfo();
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