const API = "http://127.0.0.1:8000";


// ==========================================================
// TOKEN
// ==========================================================

function getToken() {
    return localStorage.getItem("token");
}


// ==========================================================
// AUTH CHECK
// ==========================================================

function requireAuth() {

    const token = getToken();

    if (!token) {

        window.location.href =
            "/admin/login/";

        return false;
    }

    return true;
}


// ==========================================================
// AUTH HEADERS
// ==========================================================

function authHeaders() {

    return {
        "Authorization":
            `Bearer ${getToken()}`
    };
}


// ==========================================================
// LOGOUT
// ==========================================================

function logout() {

    localStorage.removeItem("token");

    window.location.href =
        "/admin/login/";
}


// ==========================================================
// LOGIN
// ==========================================================

async function login() {

    const username =
        document
            .getElementById("username")
            .value
            .trim();

    const password =
        document
            .getElementById("password")
            .value;

    const error =
        document.getElementById("error");

    error.textContent = "";


    if (!username || !password) {

        error.textContent =
            "Please enter username and password.";

        return;
    }


    try {

        const response = await fetch(
            `${API}/auth/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            error.textContent =
                data.detail ||
                "Invalid username or password.";

            return;
        }


        localStorage.setItem(
            "token",
            data.access_token
        );


        window.location.href =
            "/admin/dashboard/";

    }

    catch (err) {

        console.error(
            "Login error:",
            err
        );

        error.textContent =
            "Unable to connect to server.";
    }
}


// ==========================================================
// API GET
// ==========================================================

async function apiGet(url) {

    const token = getToken();

    console.log(
        "GET:",
        `${API}${url}`
    );

    console.log(
        "TOKEN EXISTS:",
        !!token
    );


    const response = await fetch(
        `${API}${url}`,
        {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${token}`
            }
        }
    );


    console.log(
        "API STATUS:",
        response.status
    );


    if (response.status === 401) {

        logout();

        return null;
    }


    if (!response.ok) {

        throw new Error(
            await response.text()
        );
    }


    return await response.json();
}


// ==========================================================
// API POST
// ==========================================================

async function apiPost(url, body) {

    const response = await fetch(
        `${API}${url}`,
        {
            method: "POST",

            headers: {
                "Authorization":
                    `Bearer ${getToken()}`,

                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(body)
        }
    );


    if (response.status === 401) {

        logout();

        return null;
    }


    return response;
}