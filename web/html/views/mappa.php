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
    echo "<h2>todo</h2>";
?>