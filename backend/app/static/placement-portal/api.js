const API = (() => {
  const getToken = () => localStorage.getItem("ppa_token");

  function authHeaders() {
    const token = getToken();
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  async function apiRequest(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw: text };
    }

    if (!res.ok) {
      const msg = data.error || data.message || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  }

  return {
    apiGet: (path) => apiRequest("GET", path),
    apiPost: (path, body) => apiRequest("POST", path, body),
  };
})();

