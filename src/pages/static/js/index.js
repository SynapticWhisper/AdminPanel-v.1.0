const open_signin_menu = document.getElementById("sign-in");
const close_signin_menu = document.getElementById("close-signin");

const open_signup_menu = document.getElementById("sign-up");
const close_signup_menu = document.getElementById("close-signup");

const username = document.getElementById("username");
const password = document.getElementById("password");

const new_username = document.getElementById("username-input");
const new_email = document.getElementById("email-input");
const new_birthdate = document.getElementById("date-input");
const new_password = document.getElementById("password-input");
const new_conf_password = document.getElementById("password-confirmation");

const signin = document.getElementById("signin-btn");
const signup = document.getElementById("signup-btn");

username.addEventListener('input', () => {
    const errorField = document.getElementById("sign-in-error-message");
    if (username.classList.contains('incorrect')) {
        username.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

password.addEventListener('input', () => {
    const errorField = document.getElementById("sign-in-error-message");
    if (password.classList.contains('incorrect')) {
        password.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

new_username.addEventListener('input', () => {
    const errorField = document.getElementById("sign-up-error-message");
    if (new_username.classList.contains('incorrect')) {
        new_username.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

new_email.addEventListener('input', () => {
    const errorField = document.getElementById("sign-up-error-message");
    if (new_email.classList.contains('incorrect')) {
        new_email.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

new_birthdate.addEventListener('input', () => {
    const errorField = document.getElementById("sign-up-error-message");
    if (new_birthdate.classList.contains('incorrect')) {
        new_birthdate.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

new_password.addEventListener('input', () => {
    const errorField = document.getElementById("sign-up-error-message");
    if (new_password.classList.contains('incorrect')) {
        new_password.classList.toggle('incorrect')
    };
    if (new_conf_password.classList.contains('incorrect')) {
        new_conf_password.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

new_conf_password.addEventListener('input', () => {
    const errorField = document.getElementById("sign-up-error-message");
    if (new_conf_password.classList.contains('incorrect')) {
        new_conf_password.classList.toggle('incorrect')
    };
    if (new_password.classList.contains('incorrect')) {
        new_password.classList.toggle('incorrect')
    };
    errorField.innerText = "";
});

function clearSignInPopUp() {
    const errorField = document.getElementById("sign-in-error-message");
    
    password.classList.toggle('incorrect', false)
    username.classList.toggle('incorrect', false)

    errorField.innerText = "";
    username.value = "";
    password.value = "";
};

function clearSignUpPopUp() {
    const errorField = document.getElementById("sign-up-error-message");
    const successField = document.getElementById("sign-up-success-message");

    new_username.classList.toggle("incorrect", false);
    new_email.classList.toggle("incorrect", false);
    new_birthdate.classList.toggle("incorrect", false);
    new_password.classList.toggle("incorrect", false);
    new_conf_password.classList.toggle("incorrect", false);

    new_username.value = '';
    new_email.value = '';
    new_birthdate.value = '';
    new_password.value = '';
    new_conf_password.value = '';
    errorField.innerText = '';
    successField.innerHTML = '';
};

function showSignInPopUp() {
    const signInPopUp = document.querySelector(".signin-popup");
    signInPopUp.classList.toggle('closed', false);
};

function closeSignInPopUp() {
    const signInPopUp = document.querySelector(".signin-popup");
    signInPopUp.classList.toggle('closed', true);
    clearSignInPopUp();
};

function showSignUpPopUp() {
    const signInPopUp = document.querySelector(".signup-popup");
    signInPopUp.classList.toggle('closed', false);
};

function closeSignUpPopUp() {
    const signInPopUp = document.querySelector(".signup-popup");
    signInPopUp.classList.toggle('closed', true);
    clearSignUpPopUp();
};

async function signInRequest(event) {
    // event.preventDefault();
    const form = document.getElementById("signin-form");
    const errorField = document.getElementById("sign-in-error-message");
    const formData = new FormData(form);

    let username_value = formData.get("username")
    let password_value = formData.get("password")

    if (username_value === "" && password_value === "") {
        username.classList.toggle("incorrect", true);
        password.classList.toggle("incorrect", true);
        errorField.innerText = "Fields can't be empty!";
        return;
    } else if (username_value === "") {
        username.classList.toggle("incorrect", true);
        errorField.innerText = "Username field can't be empty!";
        return;
    } else if (password_value === "") {
        password.classList.toggle("incorrect", true);
        errorField.innerText = "Password field can't be empty!";
        return;
    }

    const response = await fetch("/auth/v1/login", {
        method: "POST",
        headers: {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            "username": username_value,
            "password": password_value
        })
    });

    if (response.status === 200) {
        window.location.href = "/pages/home"
        clearSignInPopUp()
    } else {
        const errorMessage = await response.json()
        username.classList.toggle("incorrect", true)
        password.classList.toggle("incorrect", true)
        password.value = ""
        errorField.innerText = errorMessage.detail;
    };
};

async function signUpRequest(event) {
    // event.preventDefault();
    const form = document.getElementById("signup-form");
    const errorField = document.getElementById("sign-up-error-message");
    const successField = document.getElementById("sign-up-success-message");
    const formData = new FormData(form);
    if (formData.get("username") === "") {
        new_username.classList.toggle("incorrect", true);
        errorField.innerText = "Username field can't be empty!";
        return;
    } else if (formData.get("email") === "") {
        new_email.classList.toggle("incorrect", true);
        errorField.innerText = "Email field can't be empty!";
        return;
    } else if (formData.get("birthdate") === "") {
        new_birthdate.classList.toggle("incorrect", true);
        errorField.innerText = "Birth date field can't be empty!";
        return;
    } else if (formData.get("password") === "") {
        new_password.classList.toggle("incorrect", true);
        errorField.innerText = "Password field can't be empty!";
        return;
    };

    if (formData.get("password") !== formData.get("conf-password")) {
        new_password.classList.toggle("incorrect", true);
        new_conf_password.classList.toggle("incorrect", true);
        errorField.innerText = "The passwords you entered do not match.";
        return;
    };

    formData.delete("conf-password")

    const response = await fetch("/user/sign-up", {
        method: "POST",
        headers: {
            'accept': 'application/json',
        },
        body: formData
    });

    const errorMessage = await response.json()
    console.log(errorMessage.detail)

    if (response.status === 201) {
        clearSignUpPopUp();
        successField.innerText = errorMessage.detail;
    } else if (response.status === 409) {
        if (errorMessage.detail.includes("email")) {
            new_email.classList.toggle("incorrect", true)
        } else if (errorMessage.detail.includes("username")) {
            new_username.classList.toggle("incorrect", true)
        } else {
            new_email.classList.toggle("incorrect", true);
            new_username.classList.toggle("incorrect", true);
        };
        new_password.value = ""
        new_conf_password.value = ""
        errorField.innerText = errorMessage.detail;
    } else {
        errorField.innerText = errorMessage.detail;
    };
};

open_signin_menu.addEventListener('click', showSignInPopUp);
close_signin_menu.addEventListener('click', closeSignInPopUp);
open_signup_menu.addEventListener('click', showSignUpPopUp);
close_signup_menu.addEventListener('click', closeSignUpPopUp);
signin.addEventListener("click", signInRequest)
signup.addEventListener("click", signUpRequest)
