<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
	header('Location: /login?r');
	exit;
}
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home 🦺</title>
</head>
<body>
    <h1>Welcome home <?php echo $_SESSION['username']?></h1>
    
    <br>
    <button>
        <a href="/prenotazione">Add new reservation</a>
    </button>
    <br>
    <button>
        <a href="/mappa">Show Map</a>
    </button>
    <br>
    <button>
        <a href="/eventi">Eventi</a>
    </button>
    <br>
    <br>
    <button>
        <a href="/logout">Logout</a>
    </button>
</body>
</html>