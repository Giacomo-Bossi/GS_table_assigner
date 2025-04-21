<?php
require_once '../php/db_conn.php';
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "Today is ".date("d/m/Y H:i:s")."<br>";

echo "Connection to database successful<br>";

$user = "user";
// Prepare the SQL query with a placeholder
$sql = "SELECT id,password FROM User WHERE id = ?";

// Prepare the statement
$stmt = $conn->prepare($sql);

if ($stmt === false) {
    die("Error preparing statement: " . $conn->error);
}

// Bind the parameter to the statement (s for string type)
$stmt->bind_param("s", $user);

// Execute the statement
$stmt->execute();

// Get the result
$result = $stmt->get_result();

// Check if user was found
if ($result->num_rows > 0) {
    // Fetch and display results
    while ($row = $result->fetch_assoc()) {
        echo "ID: " . $row["id"] . "<br>";

        //pssw Verification v-0.1
        if($row["password"] == "tmnf"){
            echo "Password is correct<br>";
        } else {
            echo "Password is incorrect<br>";
        }
    }
} else {
    echo "No user found!";
}

// Close the statement and connection
$stmt->close();
$conn->close();



?>