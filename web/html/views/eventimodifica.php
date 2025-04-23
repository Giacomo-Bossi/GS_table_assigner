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
        $id = $_POST['id'];
        $nome = $_POST['nome'];
        $inizio = $_POST['inizio'];
        
        // Validate input
        if (empty($nome) || empty($inizio)) {
            echo "Nome e data/ora sono obbligatori.";
            exit;
        }

        require_once __ROOT__ . '/functions/db_conn.php';
        $stmt = $conn->prepare("UPDATE Evento SET nome = ?, time = ? WHERE id = ?");
        $stmt->bind_param("ssi", $nome, $inizio, $id);
        
        if ($stmt->execute()) {
            echo "Evento modificato con successo!";
            echo "<script>setTimeout(function(){ window.location.href = '/eventi'; }, 2000);</script>";
            die();
        } else {
            echo "Errore: " . $stmt->error;
        }
    }
    if (isset($_GET['id'])) {
        $id = $_GET['id'];
        require_once __ROOT__ . '/functions/db_conn.php';
        $stmt = $conn->prepare("SELECT * FROM Evento WHERE id = ?");
        $stmt->bind_param("i", $id);
        $stmt->execute();
        $result = $stmt->get_result();
        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            $nome = htmlspecialchars($row['nome']);
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
        <div>
            <label for="nome">ID:</label>
            <input type="text" value="<?= $id ?>" readonly disabled>
            <input type="hidden" name="id" value="<?= $id ?>">
        </div>
        <div>
            <label for="nome">Nome:</label>
            <input type="text" id="nome" name="nome" required value="<?= $nome ?>">
        </div>
        <div>
            <label for="inizio">Data/Ora:</label>
            <input type="datetime-local" id="inizio" name="inizio" required value="<?= date("Y-m-d\TH:i", strtotime($inizio)) ?>">
        </div>
        <button type="submit">Modifica evento</button>
</body>
</html>