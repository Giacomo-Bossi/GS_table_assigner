<?php

$headers = apache_request_headers();
if (!isset($headers['Authorization'])) {
    header('HTTP/1.0 401 Unauthorized');
    echo 'Authorization Required';
    exit;
}
$auth = $headers['Authorization'];
if ($auth != "68fcf87e19e49567b09ea60fcc9fa298") {
    header('HTTP/1.0 401 Unauthorized');
    echo 'Authorization Failed';
    exit;
}

require_once __ROOT__ . '/functions/db_conn.php';

$stmt = $conn->prepare("SHOW STATUS LIKE 'uptime'");

$stmt->execute();
$stmt->bind_result($nul, $uptime);
$stmt->fetch();
$stmt->close();
$uptime = $uptime / 60; // Convert to minutes
$uptime = round($uptime, 2); // Round to 2 decimal places
$uptime = $uptime . " min";
$uptime = htmlspecialchars($uptime);
echo "<h1>Uptime: $uptime</h1>";
$stmt = $conn->prepare("SHOW STATUS LIKE 'Threads_connected'");
$stmt->execute();
$stmt->bind_result($nul, $threads_connected);
$stmt->fetch();
$stmt->close();
$threads_connected = htmlspecialchars($threads_connected);
echo "<h1>Threads connected: $threads_connected</h1>";

$stmt = $conn->prepare("SELECT VERSION() AS version, @@version_comment AS version_commen");
$stmt->execute();
$stmt->bind_result($version, $version_comment);
$stmt->fetch();
$stmt->close();
$version = htmlspecialchars($version);
$version_comment = htmlspecialchars($version_comment);
echo "<h1>Version: $version</h1>";
echo "<h1>DB: $version_comment</h1>";



?>