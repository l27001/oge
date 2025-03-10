let Gdata, Ldata;
function showMessage(type, message) {
    let msgdiv = document.getElementById('messages');
    var msg = document.createElement("div");
    msg.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`;
    msg = msgdiv.appendChild(msg);
    setTimeout(() => msgdiv.removeChild(msg), 5000);
}

async function downloadImage() {
    const image = await fetch(document.getElementById('preview').src)
    const imageBlog = await image.blob()
    const imageURL = URL.createObjectURL(imageBlog)
  
    const link = document.createElement('a')
    link.href = imageURL
    link.download = 'image file name here'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

function submitChanges(notify=1) {
    if(notify == 1) {
        showMessage("success", "Рабочее изображение заменено");
    }
    updateImage(Ldata, 1);
}

function updateImage(data, new_=0) {
    let img = document.getElementById('preview');
    let timestamp = Date.now();
    img.src = `/preview/${data.filename}?${timestamp}`;
    img.style.display = 'block';
    img.height = data.size[0];
    img.width = data.size[1];
    document.getElementById("resizeHeight").value = data.size[0];
    document.getElementById("resizeWidth").value = data.size[1];
    Ldata = data;
    if(new_ == 1) {
        document.getElementById("contrastContrast").value = 1;
        document.getElementById("contrastBrightness").value = 0;
        document.getElementById("rotate_y").value = Math.floor(data.size[0]/2);
        document.getElementById("rotate_x").value = Math.floor(data.size[1]/2);
        document.getElementById("resizeScale").value = 1;
        document.getElementById("infoHeight").value = data.size[0];
        document.getElementById("infoWidth").value = data.size[1];
        document.getElementById("colorRed").value = 1;
        document.getElementById("colorGreen").value = 1;
        document.getElementById("colorBlue").value = 1;
        Gdata = data;
    }
}

function reeset() {
    updateImage(Gdata, 1);
}

function uploadFile() {
    let fileInput = document.getElementById('imageLoader');
    let file = fileInput.files[0];
    if (!file) {
        showMessage("danger", "Необходимо выбрать файл!");
        return;
    }
    let formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data, 1);
            document.getElementById("accordionExample").hidden = 0;
        }
    })
    .catch(error => console.error('Error:', error));
}

function resize(hw=0) {
    let formData = new FormData(document.getElementById("resizeForm"));
    if(hw == 1) {
        formData.set("scale", 0);
    }

    fetch('/resize/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
           document.getElementById("resizeScale").value = data.scale;
        }
    })
    .catch(error => console.error('Error:', error));
}

function crop() {
    let formData = new FormData(document.getElementById("cropForm"));

    fetch('/crop/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
        }
    })
    .catch(error => console.error('Error:', error));
}

function mirror(axis) {
    let formData = new FormData();
    formData.append('axis', axis)

    fetch('/mirror/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
            submitChanges(0);
        }
    })
    .catch(error => console.error('Error:', error));
}

function rotate() {
    let formData = new FormData(document.getElementById("rotateForm"));

    fetch('/rotate/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
            submitChanges(0);
        }
    })
    .catch(error => console.error('Error:', error));
}

function doContrast() {
    let formData = new FormData(document.getElementById("contrastForm"));

    fetch('/contrast/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
        }
    })
    .catch(error => console.error('Error:', error));
}

function color() {
    let formData = new FormData(document.getElementById("colorForm"));

    fetch('/color/' + Gdata.filename, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage("danger", data.error);

        } else {
            updateImage(data);
        }
    })
    .catch(error => console.error('Error:', error));
}