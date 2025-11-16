// static/js/main.js

console.log("main.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  // Grab the signup form if we're on the signup page
  const signupForm = document.querySelector("form.auth-form");

  if (!signupForm) {
    // We're not on the signup page – nothing else to do.
    return;
  }

  console.log("Signup form found");

  signupForm.addEventListener("submit", () => {
    // IMPORTANT: we DO NOT preventDefault here,
    // so the normal Flask POST /signup still happens.
    console.log("Signup form submitted");
  });
});

