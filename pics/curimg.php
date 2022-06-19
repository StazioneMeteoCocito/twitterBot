<?php
$isUaWar = true;
if(date("d") == "03" && date("m") == "06"){
	$file = "it.png";
}
elseif(date("d") == "09" && date("m") == "05"){
	$file = "eu.png";
}
elseif(date("m") == "06"){
	$file = "june.png";
}
elseif($isUaWar){
	$file = "ua.png";
}
else{
	$file = "default.png";
}
$type = 'image/png';
header('Content-Type:'.$type);
header('Content-Length: ' . filesize($file));
readfile($file);
