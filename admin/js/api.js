async function apiGet(url) {

    const res = await fetch(
        `${API}${url}`,
        {
            headers: authHeaders()
        }
    );

    if (res.status === 401) {
        logout();
        return null;
    }

    if (!res.ok) {
        throw new Error(await res.text());
    }

    return await res.json();
}


async function apiPost(url, body) {

    const res = await fetch(
        `${API}${url}`,
        {
            method: "POST",
            headers: {
                ...authHeaders(),
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        }
    );

    if (res.status === 401) {
        logout();
        return null;
    }

    return res;
}


async function apiPut(url, body = null) {

    const options = {
        method: "PUT",
        headers: {
            ...authHeaders()
        }
    };

    if (body) {
        options.headers["Content-Type"] =
            "application/json";

        options.body =
            JSON.stringify(body);
    }

    const res = await fetch(
        `${API}${url}`,
        options
    );

    if (res.status === 401) {
        logout();
        return null;
    }

    return res;
}


async function apiDelete(url) {

    const res = await fetch(
        `${API}${url}`,
        {
            method: "DELETE",
            headers: authHeaders()
        }
    );

    if (res.status === 401) {
        logout();
        return null;
    }

    return res;
}