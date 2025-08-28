// function setNativeValue(element, value) {
//   const lastValue = element.value;
//   element.value = value;

//   const tracker = element._valueTracker;
//   if (tracker) tracker.setValue(lastValue);

//   element.dispatchEvent(new Event("input", { bubbles: true }));
//   element.dispatchEvent(new Event("change", { bubbles: true }));
// }

// function waitForInputs(timeout = 5000) {
//   return new Promise((resolve, reject) => {
//     const inputs = document.querySelectorAll("input");
//     if (inputs.length > 0) return resolve(inputs);

//     const observer = new MutationObserver(() => {
//       const inputs = document.querySelectorAll("input");
//       if (inputs.length > 0) {
//         observer.disconnect();
//         resolve(inputs);
//       }
//     });

//     observer.observe(document.body, { childList: true, subtree: true });

//     setTimeout(() => {
//       observer.disconnect();
//       reject("❌ Input fields not found within timeout.");
//     }, timeout);
//   });
// }

// function showToast(message = "✅ Autofilled by SecureAuth") {
//   const toast = document.createElement("div");
//   toast.textContent = message;
//   toast.style.cssText = `
//     position: fixed;
//     bottom: 20px;
//     right: 20px;
//     background-color: #4CAF50;
//     color: white;
//     padding: 12px 18px;
//     border-radius: 8px;
//     font-size: 14px;
//     box-shadow: 0 4px 12px rgba(0,0,0,0.15);
//     z-index: 2147483647;
//     font-family: sans-serif;
//     opacity: 0;
//     transition: opacity 0.3s ease-in-out;
//   `;
//   document.body.appendChild(toast);

//   // Trigger fade-in
//   setTimeout(() => {
//     toast.style.opacity = "1";
//   }, 100);

//   // Remove after 3s with fade-out
//   setTimeout(() => {
//     toast.style.opacity = "0";
//     setTimeout(() => toast.remove(), 300);
//   }, 3000);
// }

// (async () => {
//   const domain = window.location.hostname;
//   const { token } = await chrome.storage.local.get("token");
//   if (!token || !domain) return;

//   try {
//     const res = await fetch("http://127.0.0.1:5000/vault/api/autofill", {
//       method: "POST",
//       headers: {
//         "Authorization": `Bearer ${token}`,
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({ domain })
//     });

//     const data = await res.json();
//     if (!res.ok || !data.success || !data.data) return;

//     const inputs = await waitForInputs();

//     let filled = false;

//     for (const input of inputs) {
//       const name = (input.name || input.id || input.placeholder || "").toLowerCase();

//       if (input.type === "hidden" || input.readOnly || input.disabled) continue;

//       if (
//         input.type === "email" ||
//         name.includes("email") ||
//         name.includes("user") ||
//         name.includes("login") ||
//         name.includes("id")
//       ) {
//         setNativeValue(input, data.data.username);
//         filled = true;
//       }

//       if (input.type === "password" || name.includes("pass")) {
//         setNativeValue(input, data.data.password);
//         filled = true;
//       }
//     }

//     if (filled) {
//       showToast("✅ Credentials autofilled by SecureAuth");
//       console.log(`🔐 Autofilled credentials for ${domain}`);
//     }

//   } catch (e) {
//     console.error("❌ Autofill failed:", e);
//   }
// })();


function setNativeValue(element, value) {
  const lastValue = element.value;
  element.value = value;

  const tracker = element._valueTracker;
  if (tracker) tracker.setValue(lastValue);

  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
}

function waitForInputs(timeout = 5000) {
  return new Promise((resolve, reject) => {
    const inputs = document.querySelectorAll("input");
    if (inputs.length > 0) return resolve(inputs);

    const observer = new MutationObserver(() => {
      const inputs = document.querySelectorAll("input");
      if (inputs.length > 0) {
        observer.disconnect();
        resolve(inputs);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
      observer.disconnect();
      reject("❌ Input fields not found within timeout.");
    }, timeout);
  });
}

function showToast(message = "✅ Autofilled by SecureAuth") {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #4CAF50;
    color: white;
    padding: 12px 18px;
    border-radius: 8px;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 2147483647;
    font-family: sans-serif;
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
  `;
  document.body.appendChild(toast);

  setTimeout(() => toast.style.opacity = "1", 100);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

(async () => {
  const domain = window.location.hostname;

  // Get token, email, and login password from extension storage
  const { jwt_token, email, login_password } = await chrome.storage.local.get(["jwt_token", "email", "login_password"]);
  if (!jwt_token || !email || !login_password) return;

  try {
    const res = await fetch("http://127.0.0.1:5000/vault/api/autofill", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${jwt_token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        domain: domain,
        email: email,
        password: login_password
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success || !data.data) return;

    const inputs = await waitForInputs();

    let filled = false;
    for (const input of inputs) {
      const name = (input.name || input.id || input.placeholder || "").toLowerCase();
      if (input.type === "hidden" || input.readOnly || input.disabled) continue;

      if (
        input.type === "email" ||
        name.includes("email") ||
        name.includes("user") ||
        name.includes("login") ||
        name.includes("id")
      ) {
        setNativeValue(input, data.data.username);
        filled = true;
      }

      if (input.type === "password" || name.includes("pass")) {
        setNativeValue(input, data.data.password);
        filled = true;
      }
    }

    if (filled) {
      showToast("✅ Credentials autofilled by SecureAuth");
      console.log(`🔐 Autofilled credentials for ${domain}`);
    }

  } catch (err) {
    console.error("❌ Autofill failed:", err);
  }
})();
