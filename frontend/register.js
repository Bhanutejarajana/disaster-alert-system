function register() {

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirmPassword").value.trim();

    if (username === "" || password === "" || confirmPassword === "") {
        alert("Please fill all fields.");
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    fetch("http://127.0.0.1:5000/register", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            username,
            password
        })

    })

    .then(response => response.json())

    .then(data => {

        alert(data.message);

        if (data.message === "Registration successful") {

            window.location.href = "login.html";

        }

    })

    .catch(() => {

        alert("Unable to connect to the server.");

    });

}