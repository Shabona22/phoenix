function copyConfig(path) {
    fetch("/download/" + encodeURI(path))
        .then((r) => r.text())
        .then((text) => navigator.clipboard.writeText(text))
        .then(() => alert("کانفیگ کپی شد"))
        .catch(() => alert("خطا در کپی"));
}

function showQR(content) {
    fetch("/api/qr?config=" + encodeURIComponent(content))
        .then((r) => r.json())
        .then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            document.getElementById("qrImage").src = "data:image/png;base64," + data.qr;
            new bootstrap.Modal(document.getElementById("qrModal")).show();
        })
        .catch(() => alert("خطا در تولید QR"));
}
