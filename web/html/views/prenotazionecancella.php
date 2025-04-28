<?php
session_start();
if (!isset($_SESSION['username'])) {
    $_SESSION['next'] = $_SERVER['REQUEST_URI'];
    header('Location: /login?r');
    exit;
}
?>
<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $id = $_POST['id'];

    // Validate input
    if (empty($id)) {
        echo "ID dell'evento mancante.";
        exit;
    }

    require_once __ROOT__ . '/functions/db_conn.php';
    $stmt = $conn->prepare("DELETE FROM Prenotazione WHERE id = ?");
    $stmt->bind_param("s", $id);

    if ($stmt->execute()) {
        echo "Prenotazione cancellata con successo!";
        echo "<script>setTimeout(function(){ window.history.go(-2); }, 2000);</script>";
        die();
    } else {
        echo "Errore: " . $stmt->error;
    }
}
if (isset($_GET['id'])) {
    $id = $_GET['id'];
    require_once __ROOT__ . '/functions/db_conn.php';
    $stmt = $conn->prepare("SELECT * FROM Prenotazione p LEFT JOIN Evento e ON e.id = p.idevento WHERE p.id = ?");
    $stmt->bind_param("i", $id);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();
        $nome = htmlspecialchars($row['nome']);
        $nominativo = htmlspecialchars($row['nominativo']);
        $persone = htmlspecialchars($row['persone']);
        $capotavola = htmlspecialchars($row['capotavola']);
        $inizio = htmlspecialchars($row['time']);
    } else {
        echo "Evento non trovato.";
        exit;
    }
} else {
    echo "ID evento non specificato.";
    exit;
}
?>

<!DOCTYPE html>
<html lang="it">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modifica evento</title>
</head>

<body>
    <form method="POST">
        <input type="text" name="id" hidden value="<?= $id?>">
        <div>
            <label for="evento">Evento:</label>
            <select id="evento" name="evento" disabled>
                <option selected><?= $nome . ' (' . $inizio . ')'; ?></option>
            </select>
        </div>
        <div>
            <label for="nome">Nome:</label>
            <input type="text" id="nome" name="nome" disabled value="<?= $nominativo?>">
        </div>
        <div>
            <label for="persone">Persone:</label>
            <input type="number" id="persone" name="persone" disabled value="<?= $persone?>">
        </div>
        <div>
            <label for="capotavola">Capotavola:</label>
            <input type="checkbox" id="capotavola" name="capotavola" disabled <?= ($capotavola ? 'checked' : '') ?>>
        </div>
        <button type="submit">Confirm deletion</button>
        <button type="button" onclick="history.back()">Cancel</button>
</body>

</html>