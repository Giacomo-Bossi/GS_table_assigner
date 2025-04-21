<?php

// Create connection
$conn = new mysqli(getenv('DB_HOST'), getenv('DB_USER'), getenv('DB_PASS'), getenv('DB_NAME'));

// Check connection
if ($conn->connect_error) {
    die("Connection to database failed");
}

?>