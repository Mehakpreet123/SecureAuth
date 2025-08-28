// document.getElementById("loginBtn").addEventListener("click", async () => {
//   const email = document.getElementById("email").value;
//   const password = document.getElementById("password").value;

//   try {
//     const res = await fetch("http://127.0.0.1:5000/api/login", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ email, password })
//     });

//     const data = await res.json();

//     if (res.ok && data.token) {
//       await chrome.storage.local.set({ token: data.token });
//       document.getElementById("status").innerText = "Login successful!";
//     } else {
//       document.getElementById("status").innerText = "Login failed.";
//     }
//   } catch (err) {
//     document.getElementById("status").innerText = "Error logging in.";
//     console.error(err);
//   }
// });


document.getElementById("loginBtn").addEventListener("click", async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const res = await fetch("http://127.0.0.1:5000/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (res.ok && data.token) {
      // Store JWT token, email, and login password for autofill
      await chrome.storage.local.set({
        jwt_token: data.token,
        email: email,
        login_password: password
      });

      document.getElementById("status").innerText = "Login successful!";
    } else {
      document.getElementById("status").innerText = "Login failed: " + (data.error || "");
    }
  } catch (err) {
    document.getElementById("status").innerText = "Error logging in.";
    console.error(err);
  }
});
