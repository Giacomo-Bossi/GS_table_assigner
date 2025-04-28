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
        $persone = $_POST['persone'];
        $capotavola = isset($_POST['capotavola']) ? 1 : 0;
        $evento = $_POST['evento'];
        $timestamp = date("Y-m-d H:i:s");
        $id = $_POST['id'];

        // Validate input
        if (empty($id) ||empty($nome) || empty($persone) || empty($evento)) {
            echo "Tutti i campi sono obbligatori.";
            
        } else {
            // Connect to the database
            require_once __ROOT__ . '/functions/db_conn.php';
            // Prepare and bind
            $stmt = $conn->prepare("INSERT INTO Prenotazione (id, nominativo, persone, capotavola, idevento, timestamp) VALUES (?, ?, ?, ?, ?, ?)");
            $stmt->bind_param("ssiiis", $id, $nome, $persone, $capotavola, $evento, $timestamp);
            // Execute the statement
            try{
                $stmt->execute();
                echo "Prenotazione aggiunta con successo.";
            } catch (Exception $e) {
                if($e->getCode() == 1062){
                    echo "Errore: ID già esistente (Prenotazione già aggiunta?).";
                } else {
                    echo "Errore: " . $e->getMessage();
                }
            }
            // Close the statement and connection
            $stmt->close();
            $conn->close();
        }
        die();
    }
?>

<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aggiungi prenotazione</title>
</head>
<body>
    <form method="POST">
        <input type="hidden" name="id" value="<?= str_pad(floor(microtime(true) * 10000), 16, "0", STR_PAD_LEFT) . '_' . bin2hex(random_bytes(4)); ?>">
        <div>
            <label for="evento">Evento:</label>
            <select id="evento" name="evento">
            <?php
            require_once __ROOT__ . '/functions/db_conn.php';
            $result = $conn->query("SELECT id, nome FROM Evento WHERE deleted=0");

            if ($result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {

                echo "<option value='" . $row["id"] . "' ". (($_GET["e"]==$row["id"])?"selected":"") ." >" . $row["nome"] . "</option>";
                }
            } else {
                echo "<option value=''>Nessun evento disponibile</option>";
            }
            ?>
            </select>
        </div>
        <div>
            <label for="nome">Nome:</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div>
            <label for="persone">Persone:</label>
            <input type="number" id="persone" name="persone" required>
        </div>
        <div>
            <label for="capotavola">Capotavola:</label>
            <input type="checkbox" id="capotavola" name="capotavola">
        </div>
        <button type="submit">Invia</button>
    </form> 
</body>
</html>