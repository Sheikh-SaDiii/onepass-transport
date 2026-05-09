import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAnalytics, isSupported as analyticsSupported } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-analytics.js";
import { getAuth, signInWithCustomToken, signOut } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyC7LCi9nt03XrdA1ahmCWJZO-QE0HiIYXA",
  authDomain: "onepass-53d58.firebaseapp.com",
  projectId: "onepass-53d58",
  storageBucket: "onepass-53d58.firebasestorage.app",
  messagingSenderId: "460217064037",
  appId: "1:460217064037:web:e8b1b71e8c6f5ec22b048c",
  measurementId: "G-FX1QDV7D9W"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

analyticsSupported().then((ok) => {
  if (ok) getAnalytics(app);
});

window.firebaseApp = app;
window.firebaseAuth = auth;
window.firebaseDb = db;

const ctx = window.OnePass || {};

window.firebaseReady = (async () => {
  if (!ctx.djangoAuthed) {
    if (auth.currentUser) await signOut(auth);
    return null;
  }
  if (auth.currentUser && auth.currentUser.uid === String(ctx.djangoUserId)) {
    return auth.currentUser;
  }
  try {
    const res = await fetch(ctx.firebaseTokenUrl, { credentials: "same-origin" });
    if (!res.ok) throw new Error(`token endpoint ${res.status}`);
    const data = await res.json();
    const cred = await signInWithCustomToken(auth, data.token);
    return cred.user;
  } catch (e) {
    console.warn("[firebase] custom-token sign-in failed:", e);
    return null;
  }
})();
