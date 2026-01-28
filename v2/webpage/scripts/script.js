//selecting all required elements
const dropArea = document.querySelector("#loadHere.drag-area"),
    // dragText removed, we use querySelectorAll inside function or global
    button = dropArea.querySelector("button"),
    input = dropArea.querySelector("input");
let file; //this is a global variable and we'll use it inside multiple functions
var fileobj;
let alreadyUploading = false;

button.onclick = () => {
    input.click(); //if user click on the button then the input also clicked
    file_browse();

}

input.addEventListener("change", function () {
    if (this.files.length > 1) {
        alert("Please select only one file!");
        return;
    }
    file = this.files[0];
    //dropArea.classList.add("active");
    // showFile(); //calling function
});


let dragCounter = 0;

//If user Drag File Over DropArea
dropArea.addEventListener("dragenter", (event) => {
    event.preventDefault();
    dragCounter++;
    if (event.dataTransfer.items && event.dataTransfer.items.length > 0) {
        // Only update text on initial entry or if text is wrong
        if (event.dataTransfer.items.length > 1) {
            console.log("piu di un file");
            dropArea.classList.add("error");
            animateText("Scegli un file solo!");
        } else if (event.dataTransfer.items[0].kind === "file" && (event.dataTransfer.items[0].type === "text/csv" || event.dataTransfer.items[0].type === "application/vnd.ms-excel")) {
            dropArea.classList.add("active");
            dropArea.classList.remove("error");
            animateText("Rilascia per caricare il file");
        } else if (event.dataTransfer.items[0].kind === "file") {
            dropArea.classList.add("error");
            animateText("Serve un file CSV!");
        }
    }
});

dropArea.addEventListener("dragover", (event) => {
    event.preventDefault(); //preventing from default behaviour
    // Logic moved to dragenter to avoid continuous firing
});

//If user leave dragged File from DropArea
dropArea.addEventListener("dragleave", () => {
    dragCounter--;
    if (dragCounter === 0) {
        dropArea.classList.remove("active");
        dropArea.classList.remove("error");
        animateText("Trascina qui il CSV");
    }
});

//If user drop File on DropArea
dropArea.addEventListener("drop", (event) => {
    event.preventDefault(); //preventing from default behaviour
    dragCounter = 0; // Reset counter
    if (event.dataTransfer.files.length > 1) {
        dropArea.classList.add("error");
        animateText("Carica un file solo!");
        dropArea.classList.remove("active");
        return;
    }
    if (event.dataTransfer.files[0].type !== "text/csv" && event.dataTransfer.files[0].name.split('.').pop().toLowerCase() !== 'csv') {
        dropArea.classList.add("error");
        animateText("Serve un file CSV!");
        dropArea.classList.remove("active");
        return;
    }
    file = event.dataTransfer.files[0];
    js_file_upload(file);
    // showFile(); //calling function
});

// Initial Selectors
const textSlides = document.querySelectorAll('.text-slide');
let currentSlideIndex = 0; // 0 is active, 1 is next

function animateText(newText) {
    const activeSlide = textSlides[currentSlideIndex];
    const nextIndex = (currentSlideIndex + 1) % 2;
    const nextSlide = textSlides[nextIndex];

    // Optimization: Ignore if the text is already what we want
    // Note: We check the active slide's text
    if (activeSlide.textContent === newText) return;

    // Prepare next slide
    nextSlide.textContent = newText;

    // Reset next slide to bottom position instantly (remove transition temporarily)
    nextSlide.style.transition = 'none';
    nextSlide.classList.remove('active', 'exit');
    // Force reflow
    void nextSlide.offsetWidth;
    // Restore transition
    nextSlide.style.transition = '';

    // Animate
    activeSlide.classList.add('exit');
    activeSlide.classList.remove('active');

    nextSlide.classList.add('active');

    // Update index pointer
    currentSlideIndex = nextIndex;
}


function upload_file(e) {
    e.preventDefault();
    fileobj = e.dataTransfer.files[0];
    js_file_upload(fileobj);
}

function file_browse() {
    document.getElementById('file').onchange = function () {
        fileobj = document.getElementById('file').files[0];
        if (fileobj.type !== "text/csv" && fileobj.name.split('.').pop().toLowerCase() !== 'csv') {
            dropArea.classList.add("error");
            animateText("Serve un file CSV!");
            return;
        }
        js_file_upload(fileobj);
    };
}


function js_file_upload(file_obj) {
    if (alreadyUploading) {
        alert("A file is already been uploaded!");
        return;
    }
    if (file_obj != undefined) {
        alreadyUploading = true;
        document.getElementById("drag").style["display"] = "none";
        document.getElementById("uploading").style["display"] = "";
        createJob(file_obj);
        return;
        var form_data = new FormData();
        form_data.append('file', file_obj);
        var xhttp = new XMLHttpRequest();
        xhttp.upload.addEventListener("progress", updateProgress);
        xhttp.open("POST", "TODO", true);
        xhttp.onload = function (event) {

            if (xhttp.status == 200) {
                console.log("Uploaded!");
                showFile(xhttp.responseText);
            } else {
                window.location.href = "/error.html?err=" + xhttp.status;
                //alert(xhttp.status);
            }
        }
        xhttp.send(form_data);
    }
}

let progress = document.getElementsByClassName("progress")[0];

function updateProgress(e) {
    //    progress.style.width = (((e.loaded/e.total)*100))+ "%";
    changeProgressBar(Math.floor((e.loaded / e.total) * 100));
    document.getElementById("jobState").textContent = bytesToSize(e.loaded) + " / " + bytesToSize(e.total);
}



const sleep = (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
}

function createLinkToPreload(externalHref) {
    let linkElement = document.createElement("link");
    linkElement.rel = "preload";
    linkElement.href = externalHref;
    linkElement.as = "fetch";

    //let me = this;
    //linkElement.onload = () => {me.onElementPreloaded(externalHref)};
    //linkElement.onerror = () => {me.onElementPreloadError(externalHref)};

    return linkElement;
}


function changeProgressBar(percent) {
    const circleBar = document.querySelector('.circleBar');
    const radius = circleBar.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    circleBar.style.strokeDasharray = `${circumference}`;
    circleBar.style.strokeDashoffset = `${circumference - percent / 100 * circumference}`;
    document.querySelector('.num').textContent = `${percent}%`;
}


function bytesToSize(bytes = 0) {
    const si_prefix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const base = 1024;
    let sizeClass = Math.min(Math.floor(logN(bytes, base)), si_prefix.length - 1);
    let freeSpace = (bytes / Math.pow(base, sizeClass)).toFixed(2) + " " + si_prefix[sizeClass];
    return freeSpace;
}

function logN(val, base) {
    return Math.log(val) / Math.log(base);
}

