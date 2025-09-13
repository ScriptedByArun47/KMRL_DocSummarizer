const API = "http://localhost:9000/api";
let currentUser = null;

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (res.ok) {
    currentUser = data.user;
    document.getElementById("loginPage").style.display = "none";
    document.getElementById("dashboard").style.display = "block";
    document.getElementById("userRole").innerText = currentUser.role;
    loadDocuments();
  } else {
    document.getElementById("loginMsg").innerText = data.error;
  }
}

function logout() {
  currentUser = null;
  document.getElementById("loginPage").style.display = "block";
  document.getElementById("dashboard").style.display = "none";
}

async function loadDocuments() {
  const res = await fetch(`${API}/documents`);
  const docs = await res.json();
  const list = document.getElementById("docsList");
  list.innerHTML = "";
  docs.forEach(doc => {
    const div = document.createElement("div");
    div.className = "doc-card";
    div.innerText = doc.title + " (by " + doc.uploadedBy + ")";
    div.onclick = () => showDoc(doc);
    list.appendChild(div);
  });
}

function showDoc(doc) {
  document.getElementById("docDetails").style.display = "block";
  document.getElementById("docTitle").innerText = doc.title;
  document.getElementById("docUrl").innerText = doc.url;
  document.getElementById("docUrl").href = doc.url;
  document.getElementById("docSummary").innerText = doc.summary;
}
