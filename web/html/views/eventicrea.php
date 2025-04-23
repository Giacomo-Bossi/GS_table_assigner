<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
	header('Location: /login?r');
	exit;
}
?>

<?php

if($_SERVER["REQUEST_METHOD"] == "POST"){
    $nome = $_POST['nome'];
    $inizio = $_POST['inizio'];
    
    // Validate input
    if (empty($nome) || empty($inizio)) {
        echo "Nome e data/ora sono obbligatori.";
        exit;
    }

    require_once __ROOT__ . '/functions/db_conn.php';
    $stmt = $conn->prepare("INSERT INTO Evento (nome, time) VALUES (?, ?)");
    $stmt->bind_param("ss", $nome, $inizio);
    
    if ($stmt->execute()) {
        echo "Evento aggiunto con successo!";
        echo "<script>setTimeout(function(){ window.location.href = '/eventi'; }, 2000);</script>";
        die();
    } else {
        echo "Errore: " . $stmt->error;
    }
}


?>

<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuovo evento</title>
</head>
<body>
    <form method="POST">
        <div>
            <label for="nome">Nome:</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div>
            <label for="inizio">Data/Ora:</label>
            <input type="datetime-local" id="inizio" name="inizio" required value="<?= date("Y-m-d\TH:00") ?>">
        </div>
        <button type="submit">Crea evento</button>
    </form>
</body>
</html>