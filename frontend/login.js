function login() {

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    fetch("http://127.0.0.1:5000/login", {

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

       if (data.role === "admin") {

            localStorage.setItem("role", "admin");
            localStorage.setItem("username", username);

            window.location.href = "admin.html";

        }
        else if (data.role === "user") {

            localStorage.setItem("role", "user");
            localStorage.setItem("username", username);

            window.location.href = "user.html";

        }
        
        else {

            alert(data.message);

        }

    })
    .catch(() => {

        alert("Unable to connect to the server.");

    });

}