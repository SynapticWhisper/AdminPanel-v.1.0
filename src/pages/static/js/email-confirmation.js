const confirmationCode = document.getElementById("confirmation-code")
const resendCodeButton = document.getElementById("resend-code");

resendCodeButton.addEventListener('click', () => {
    // Make request to api
    // Restart timer
    let remainingTime = 120;
    localStorage.setItem('startTime', Date.now());
    resendCodeButton.disabled = true
    startTimer(remainingTime);
});

confirmationCode.addEventListener('input', () => {
    let button = document.getElementById("send-code");
    var code = confirmationCode.value;
    if (code.length === 6) {
        button.removeAttribute("disabled");
    } else {
        if (!button.hasAttribute("disabled")) {
            button.setAttribute("disabled", true);
        };
    };
});

function startCountDown(duration, timerElement, buttonElement) {
    let timer = duration;
    const interval  = setInterval(function () {
        let minutes = Math.floor(timer/60);
        let seconds = timer % 60;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        seconds = seconds < 10 ? '0' + seconds : seconds;
        timerElement.innerText = minutes + ":" + seconds;

        localStorage.setItem("remainingTime", timer);

        if (--timer < 0) {
            clearInterval(interval);
            buttonElement.disabled = false;
        };
    }, 1000);
};

function startTimer(remainingTime) {
    let timerElement = document.getElementById("timer");
    let buttonElement = document.getElementById("resend-code");

    if (remainingTime > 0) {
        startCountDown(remainingTime, timerElement, buttonElement);
    } else {
        timerElement.textContent = "0:00";
        buttonElement.disabled = false;
    }

};

window.onload = function () {  
    let remainingTime = localStorage.getItem('remainingTime');
    if (remainingTime === null) {
        remainingTime = 120;
        localStorage.setItem('startTime', Date.now());
    } else {
        const elapsed = Math.floor((Date.now() - localStorage.getItem('startTime')) / 1000);
        remainingTime = 120 - elapsed 
    };
    startTimer(remainingTime);
}